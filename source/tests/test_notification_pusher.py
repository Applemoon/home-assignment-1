import json
import requests
import unittest
from mock import Mock, patch, mock_open
import tarantool
import tarantool_queue
from source import notification_pusher
from source.notification_pusher import *
from notification_pusher import *
from gevent import queue as gevent_queue
import imp

MAGIC_NUMBER = 42


class NotificationPusherTestCase(unittest.TestCase):
    def app_stop(self, arg):
        notification_pusher.run_application = False

    def test_notification_worker_ok(self):
        self.callback_url_str = 'callback_url'
        self.url = 'url'

        task = Mock(task_id=MAGIC_NUMBER, data={self.callback_url_str: self.url, 'id': MAGIC_NUMBER})
        task_queue = Mock()

        with patch('notification_pusher.requests.post') as mock_post:
            notification_pusher.notification_worker(task, task_queue)

        task.data.pop(self.callback_url_str)
        mock_post.assert_called_with(self.url, data=json.dumps(task.data))

        task_queue.put.assert_called_once_with((task, 'ack'))

    def test_notification_worker_with_except(self):
        self.callback_url_str = 'callback_url'
        self.url = 'url'

        task = Mock(task_id=MAGIC_NUMBER, data={self.callback_url_str: self.url, 'id': MAGIC_NUMBER})
        task_queue = Mock()

        with patch('notification_pusher.requests.post', side_effect=requests.RequestException) as mock_post:
            notification_pusher.notification_worker(task, task_queue)

        task.data.pop(self.callback_url_str)
        mock_post.assert_called_with(self.url, data=json.dumps(task.data))

        task_queue.put.assert_called_once_with((task, 'bury'))

    def test_done_with_processed_tasks(self):
        task = Mock()
        action_name = "test"

        task_queue = Mock()
        task_queue.get_nowait.return_value = (task, action_name)
        task_queue.qsize.return_value = 1

        notification_pusher.done_with_processed_tasks(task_queue)

        task.test.assert_called_once_with()
        task_queue.qsize.assert_called_once_with()

    def test_done_with_processed_tasks_empty_exception(self):
        task_queue = Mock()
        task_queue.get_nowait.side_effect = gevent_queue.Empty
        task_queue.qsize.return_value = 1

        notification_pusher.done_with_processed_tasks(task_queue)

        task_queue.qsize.assert_called_once_with()

    def test_done_with_processed_tasks_database_error_exception(self):
        task_queue = Mock()
        task_queue.get_nowait.return_value = (Mock(), "test")
        task_queue.qsize.return_value = 1

        with patch('notification_pusher.getattr', Mock(side_effect=tarantool.DatabaseError), create=True):
            with patch('notification_pusher.logger.exception') as mock_exception:
                done_with_processed_tasks(task_queue)

        self.assertEqual(mock_exception.call_count, 1)
        task_queue.qsize.assert_called_once_with()

    def test_stop_handler(self):
        notification_pusher.run_application = True

        signum = MAGIC_NUMBER
        notification_pusher.stop_handler(signum)

        self.assertFalse(notification_pusher.run_application)
        self.assertEqual(notification_pusher.exit_code,
                         notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)

    def test_main_loop(self):
        config = Mock(QUEUE_HOST=MAGIC_NUMBER,
                      QUEUE_PORT=MAGIC_NUMBER,
                      QUEUE_SPACE=MAGIC_NUMBER,
                      QUEUE_TUBE='test',
                      WORKER_POOL_SIZE=2)

        notification_pusher.tarantool_queue = Mock(spec=tarantool_queue)
        notification_pusher.sleep = Mock(side_effect=self.app_stop)
        notification_pusher.run_application = True

        notification_pusher.main_loop(config)

        self.assertTrue(notification_pusher.sleep.called)
        self.assertTrue(notification_pusher.tarantool_queue.Queue.called)
        self.assertTrue(notification_pusher.tarantool_queue.Queue().tube.called)
        self.assertTrue(notification_pusher.tarantool_queue.Queue().tube().take.called)

    def test_parse_cmd_args__abbr(self):
        cfg = '/conf'
        pidfile = '/pidfile'

        parsed_args = parse_cmd_args(['-c', cfg, '-P', pidfile, '-d'])

        self.assertTrue(parsed_args.config == cfg)
        self.assertTrue(parsed_args.pidfile == pidfile)
        self.assertTrue(parsed_args.daemon)

    def test_parse_cmd_args__full(self):
        cfg = '/conf'
        pidfile = '/pidfile'

        parsed_args = parse_cmd_args(['--config', cfg, '--pid', pidfile])

        self.assertTrue(parsed_args.config == cfg)
        self.assertTrue(parsed_args.pidfile == pidfile)
        self.assertFalse(parsed_args.daemon)

    def test_daemonize_ok(self):
        pid = 42
        with patch('os.fork', Mock(return_value=pid)) as os_fork:
            with patch('os._exit', Mock()) as os_exit:
                notification_pusher.daemonize()

        os_fork.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_exception(self):
        with patch('os.fork', Mock(side_effect=OSError("err"))):
            with patch('os.setsid', Mock()) as os_setsid:
                self.assertRaises(Exception, notification_pusher.daemonize)

        self.assertFalse(os_setsid.called)

    def test_daemonize_ok_after_setsid(self):
        pid = 0
        fork_pid = 42
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()) as os_exit:
                    notification_pusher.daemonize()

        self.assertEquals(os_fork.call_count, 2)
        os_setsid.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_exception_after_setsid(self):
        pid = 0
        fork_pid = OSError("err")
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()):
                    self.assertRaises(Exception, notification_pusher.daemonize)

        self.assertTrue(os_fork.called)
        os_setsid.assert_called_once_with()

    def test_daemonize__not_exit(self):
        pid = 0
        fork_pid = 0
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()) as os_exit:
                    notification_pusher.daemonize()

        self.assertEquals(os_fork.call_count, 2)
        os_setsid.assert_called_once_with()
        self.assertFalse(os_exit.called)

    def test_load_config_from_pyfile(self):
        filepath = 'filepath/'

        def execfile(filepath, variables):
            variables['UPPER'] = {'key1': 1, 'key2': 'value2'}
            variables['lower'] = 42

        with patch('__builtin__.execfile', side_effect=execfile):
            cfg = notification_pusher.load_config_from_pyfile(filepath)

        self.assertEqual(cfg.UPPER, {'key1': 1, 'key2': 'value2'})
        self.assertEqual(hasattr(cfg, 'lower_case'), False)

    def test_install_signal_handlers(self):
        with patch('notification_pusher.gevent.signal', Mock()) as mock_signal:
            notification_pusher.install_signal_handlers()

        self.assertEqual(mock_signal.call_count, 4)

    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        self.logger_temp = notification_pusher.logger
        notification_pusher.logger = Mock()
        m_open = mock_open()
        with patch('source.notification_pusher.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                notification_pusher.create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_main(self):
        notification_pusher.load_config_from_pyfile = Mock(return_value=Mock(LOGGING={}, EXIT_CODE=exit_code))
        argv = ['1', '-c', '/conf_path', '-d', '-P', '/pidfile']
        mock_dict_config = Mock()
        mock_daemonize = Mock()
        notification_pusher.daemonize = mock_daemonize
        mock_create_pidfile = Mock()
        notification_pusher.create_pidfile = mock_create_pidfile
        temp_main_loop = notification_pusher.main_loop  # TODO bad, need patch
        notification_pusher.main_loop = Mock(side_effect=self.app_stop)
        notification_pusher.patch_all = Mock()
        notification_pusher.dictConfig = mock_dict_config
        notification_pusher.install_signal_handlers = Mock()
        notification_pusher.run_application = True

        main_result = notification_pusher.main(argv)

        self.assertEqual(mock_daemonize.call_count, 1)
        self.assertEqual(mock_create_pidfile.call_count, 1)
        self.assertEqual(main_result, 0)

        notification_pusher.main_loop = Mock(side_effect=Exception)
        notification_pusher.main_loop.sleep = Mock(side_effect=self.app_stop)
        notification_pusher.run_application = True

        with self.assertRaises(Exception):
            main_result = notification_pusher.main(argv)

        self.assertEqual(mock_daemonize.call_count, 2)
        self.assertEqual(mock_create_pidfile.call_count, 2)
        self.assertEqual(main_result, 0)

        notification_pusher.main_loop = temp_main_loop
