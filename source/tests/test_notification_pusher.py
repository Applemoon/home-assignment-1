import json
import requests
import unittest
import tarantool
import source
from tarantool_queue import tarantool_queue
from mock import Mock, patch, mock_open
from gevent import queue as gevent_queue
from source.notification_pusher import notification_worker, daemonize, done_with_processed_tasks, \
    install_signal_handlers, load_config_from_pyfile, parse_cmd_args, create_pidfile

MAGIC_NUMBER = 42


def app_stop(arg):
    source.notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):
    def test_notification_worker_ok(self):
        callback_url_str = 'callback_url'
        url = 'url'

        task = Mock(task_id=MAGIC_NUMBER, data={callback_url_str: url, 'id': MAGIC_NUMBER})
        task_queue = Mock()

        with patch('source.notification_pusher.requests.post') as mock_post:
            notification_worker(task, task_queue)

        task.data.pop(callback_url_str)
        mock_post.assert_called_with(url, data=json.dumps(task.data))

        task_queue.put.assert_called_once_with((task, 'ack'))

    def test_notification_worker_with_except(self):
        callback_url_str = 'callback_url'
        url = 'url'

        task = Mock(task_id=MAGIC_NUMBER, data={callback_url_str: url, 'id': MAGIC_NUMBER})
        task_queue = Mock()

        with patch('source.notification_pusher.requests.post', side_effect=requests.RequestException) as mock_post:
            notification_worker(task, task_queue)

        task.data.pop(callback_url_str)
        mock_post.assert_called_with(url, data=json.dumps(task.data))

        task_queue.put.assert_called_once_with((task, 'bury'))

    def test_done_with_processed_tasks(self):
        task = Mock()
        action_name = "test"

        task_queue = Mock()
        task_queue.get_nowait.return_value = (task, action_name)
        task_queue.qsize.return_value = 1

        done_with_processed_tasks(task_queue)

        task.test.assert_called_once_with()
        task_queue.qsize.assert_called_once_with()

    def test_done_with_processed_tasks_empty_exception(self):
        task_queue = Mock()
        task_queue.get_nowait.side_effect = gevent_queue.Empty
        task_queue.qsize.return_value = 1

        done_with_processed_tasks(task_queue)

        task_queue.qsize.assert_called_once_with()

    def test_done_with_processed_tasks_database_error_exception(self):
        task_queue = Mock()
        task_queue.get_nowait.return_value = (Mock(), "test")
        task_queue.qsize.return_value = 1

        with patch('source.notification_pusher.getattr', Mock(side_effect=tarantool.DatabaseError), create=True):
            with patch('source.notification_pusher.logger.exception') as mock_exception:
                done_with_processed_tasks(task_queue)

        self.assertEqual(mock_exception.call_count, 1)
        task_queue.qsize.assert_called_once_with()

    def test_stop_handler(self):
        source.notification_pusher.run_application = True

        signum = MAGIC_NUMBER
        source.notification_pusher.stop_handler(signum)

        self.assertFalse(source.notification_pusher.run_application)
        self.assertEqual(source.notification_pusher.exit_code,
                         source.notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)

    def test_main_loop(self):
        config = source.notification_pusher.Config()
        config.QUEUE_HOST = MAGIC_NUMBER
        config.QUEUE_PORT = MAGIC_NUMBER
        config.QUEUE_SPACE = MAGIC_NUMBER
        config.QUEUE_TUBE = 'test'
        config.WORKER_POOL_SIZE = 2
        config.QUEUE_TAKE_TIMEOUT = 0
        config.SLEEP = 0
        config.HTTP_CONNECTION_TIMEOUT = 0

        source.notification_pusher.tarantool_queue = Mock(spec=tarantool_queue)
        source.notification_pusher.sleep = Mock(side_effect=app_stop)
        source.notification_pusher.run_application = True
        mock_pool = Mock()
        mock_pool().free_count.return_value = 1

        with patch('source.notification_pusher.Pool', mock_pool):
            source.notification_pusher.main_loop(config)

        mock_pool().free_count.assert_called_once_with()

    def test_main_loop_false(self):
        config = source.notification_pusher.Config()
        config.QUEUE_HOST = MAGIC_NUMBER
        config.QUEUE_PORT = MAGIC_NUMBER
        config.QUEUE_SPACE = MAGIC_NUMBER
        config.QUEUE_TUBE = 'test'
        config.WORKER_POOL_SIZE = 2
        config.QUEUE_TAKE_TIMEOUT = 0
        config.SLEEP = 0

        source.notification_pusher.tarantool_queue = Mock(spec=tarantool_queue)
        source.notification_pusher.sleep = Mock(side_effect=app_stop)
        source.notification_pusher.run_application = False
        mock_pool = Mock()
        mock_pool().free_count.return_value = 1

        with patch('source.notification_pusher.Pool', mock_pool):
            source.notification_pusher.main_loop(config)

        self.assertFalse(mock_pool().free_count.called)

    def test_parse_cmd_args__abbr(self):
        cfg = '/conf'
        pidfile = '/pidfile'

        parsed_args = parse_cmd_args(['-c', cfg, '-P', pidfile, '-d'])

        self.assertEqual(parsed_args.config, cfg)
        self.assertEqual(parsed_args.pidfile, pidfile)
        self.assertTrue(parsed_args.daemon)

    def test_parse_cmd_args__full(self):
        cfg = '/conf'
        pidfile = '/pidfile'

        parsed_args = parse_cmd_args(['--config', cfg, '--pid', pidfile])

        self.assertEqual(parsed_args.config, cfg)
        self.assertEqual(parsed_args.pidfile, pidfile)
        self.assertFalse(parsed_args.daemon)

    def test_daemonize_ok(self):
        pid = 42
        with patch('os.fork', Mock(return_value=pid)) as os_fork:
            with patch('os._exit') as os_exit:
                daemonize()

        os_fork.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_exception(self):
        with patch('os.fork', Mock(side_effect=OSError("err"))):
            with patch('os.setsid') as os_setsid:
                self.assertRaises(Exception, daemonize)

        self.assertFalse(os_setsid.called)

    def test_daemonize_ok_after_setsid(self):
        pid = 0
        fork_pid = 42
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid') as os_setsid:
                with patch('os._exit') as os_exit:
                    daemonize()

        self.assertEquals(os_fork.call_count, 2)
        os_setsid.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_exception_after_setsid(self):
        pid = 0
        fork_pid = OSError("err")
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid') as os_setsid:
                with patch('os._exit'):
                    self.assertRaises(Exception, daemonize)

        self.assertTrue(os_fork.called)
        os_setsid.assert_called_once_with()

    def test_daemonize__not_exit(self):
        pid = 0
        fork_pid = 0
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid') as os_setsid:
                with patch('os._exit') as os_exit:
                    daemonize()

        self.assertEquals(os_fork.call_count, 2)
        os_setsid.assert_called_once_with()
        self.assertFalse(os_exit.called)

    def test_load_config_from_pyfile(self):
        filepath = 'filepath/'
        test_dict = {'key1': 1, 'key2': 'value2'}
        lower_key_name = 'lower'

        def my_execfile(filepath, variables):
            variables['UPPER'] = test_dict
            variables[lower_key_name] = 42

        with patch('__builtin__.execfile', side_effect=my_execfile):
            cfg = load_config_from_pyfile(filepath)

        self.assertEqual(cfg.UPPER, test_dict)
        self.assertFalse(hasattr(cfg, lower_key_name))

    def test_install_signal_handlers(self):
        with patch('source.notification_pusher.gevent.signal') as mock_signal:
            install_signal_handlers()

        self.assertEqual(mock_signal.call_count, 4)

    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        self.logger_temp = source.notification_pusher.logger
        m_open = mock_open()
        with patch('source.notification_pusher.open', m_open, create=True):
            with patch('source.notification_pusher.logger'):
                with patch('os.getpid', Mock(return_value=pid)):
                    create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))

    @patch('source.notification_pusher.parse_cmd_args', Mock(return_value=Mock(daemon=True, pidfile=True)))
    @patch('source.notification_pusher.main_loop', Mock(side_effect=app_stop))
    @patch('source.notification_pusher.create_pidfile')
    @patch('source.notification_pusher.daemonize')
    def test_main__ok(self, mock_daemonize, mock_create_pidfile):
        config = source.notification_pusher.Config()
        config.LOGGING = Mock()

        with patch('source.notification_pusher.load_config_from_pyfile', Mock(return_value=config)):
            with patch('source.notification_pusher.os.path'):
                with patch('source.notification_pusher.patch_all'):
                    with patch('source.notification_pusher.dictConfig'):
                        exit_code = source.notification_pusher.main(list())

        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called_once_with(True)
        self.assertEquals(source.notification_pusher.exit_code, exit_code)

    @patch('source.notification_pusher.parse_cmd_args', Mock(return_value=Mock(daemon=True, pidfile=True)))
    @patch('source.notification_pusher.main_loop', Mock(side_effect=Exception))
    @patch('source.notification_pusher.create_pidfile')
    @patch('source.notification_pusher.daemonize')
    def test_main__exception(self, mock_daemonize, mock_create_pidfile):
        config = source.notification_pusher.Config()
        config.LOGGING = Mock()
        config.SLEEP_ON_FAIL = 42

        with patch('source.notification_pusher.load_config_from_pyfile', Mock(return_value=config)):
            with patch('source.notification_pusher.os.path'):
                with patch('source.notification_pusher.patch_all'):
                    with patch('source.notification_pusher.dictConfig'):
                        with patch('source.notification_pusher.logger'):
                            with patch('source.notification_pusher.sleep', Mock(side_effect=app_stop)) as mock_sleep:
                                exit_code = source.notification_pusher.main(list())

        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called_once_with(True)
        mock_sleep.assert_called_once_with(config.SLEEP_ON_FAIL)
        self.assertEquals(source.notification_pusher.exit_code, exit_code)
