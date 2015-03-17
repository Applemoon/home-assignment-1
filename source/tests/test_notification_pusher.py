import unittest
from mock import Mock, patch, mock_open
from source import notification_pusher
from source.notification_pusher import *
from notification_pusher import *
from gevent import queue as gevent_queue


class NotificationPusherTestCase(unittest.TestCase):

    def setUp(self):
        self.callback_url_str = 'callback_url'
        self.url = 'url'
        self.magic_number = 42
        self.args = {}
        self.kwargs = {}
        self.str = 'test'

    def test_notification_worker_ok(self):
        task = Mock(task_id=self.magic_number, data={self.callback_url_str: self.url, 'id': self.magic_number})
        task_queue = Mock()

        with patch('notification_pusher.requests.post') as mock_post:
            notification_worker(task, task_queue, *self.args, **self.kwargs)

        task.data.pop(self.callback_url_str)
        mock_post.assert_called_with(self.url, data=json.dumps(task.data), *self.args, **self.kwargs)

        task_queue.put.assert_called_with((task, 'ack'))

    def test_notification_worker_with_except(self):
        task = Mock(task_id=self.magic_number, data={self.callback_url_str: self.url, 'id': self.magic_number})
        task_queue = Mock()

        with patch('notification_pusher.requests.post', side_effect=requests.RequestException) as mock_post:
            notification_worker(task, task_queue, *self.args, **self.kwargs)

        task.data.pop(self.callback_url_str)
        mock_post.assert_called_with(self.url, data=json.dumps(task.data), *self.args, **self.kwargs)

        task_queue.put.assert_called_with((task, 'bury'))

    def test_done_with_processed_tasks(self):
        task = Mock()
        task_name = Mock()

        task_queue = Mock()
        task_queue.get_nowait.return_value = (task, task_name)
        task_queue.qsize.return_value = 1

        with patch('notification_pusher.getattr', create=True) as mock_getattr:
            done_with_processed_tasks(task_queue)

        mock_getattr.assert_called_with(task, task_name)
        self.assertEqual(mock_getattr.call_count, 1)

    def test_done_with_processed_tasks_empty_exception(self):
        task_queue = Mock()
        task_queue.get_nowait.side_effect = gevent_queue.Empty
        task_queue.qsize.return_value = 1

        with patch('notification_pusher.getattr', create=True) as mock_getattr:
            done_with_processed_tasks(task_queue)

        self.assertFalse(mock_getattr.called)

    def test_done_with_processed_tasks_database_error_exception(self):
        task = Mock()
        task_name = Mock()

        task_queue = Mock()
        task_queue.get_nowait.return_value = (task, task_name)
        task_queue.qsize.return_value = 1

        with patch('notification_pusher.getattr', Mock(side_effect=tarantool.DatabaseError), create=True):
            with patch('notification_pusher.logger.exception') as mock_exception:
                done_with_processed_tasks(task_queue)

        self.assertTrue(mock_exception.called)

    def test_stop_handler(self):
        notification_pusher.run_application = True

        signum = self.magic_number
        notification_pusher.stop_handler(signum)

        self.assertFalse(notification_pusher.run_application)
        self.assertEqual(notification_pusher.exit_code,
                         notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)

    def test_main_loop(self):
        config = Mock(QUEUE_HOST=self.magic_number,
                      QUEUE_PORT=self.magic_number,
                      QUEUE_SPACE=self.magic_number,
                      QUEUE_TUBE=self.str,
                      WORKER_POOL_SIZE=2)
        
        sleep = Mock(side_effect=KeyboardInterrupt)
        mock_tarantool_queue = Mock(spec=tarantool_queue)
        
        with patch('notification_pusher.sleep', sleep):
            with self.assertRaises(KeyboardInterrupt):
                with patch('notification_pusher.tarantool_queue', mock_tarantool_queue):
                    main_loop(config)
        # TODO asserts


    def test_parse_cmd_args(self):
        # TODO
        pass

    def test_daemonize(self):
        # TODO
        pass

    def test_load_config_from_pyfile(self):
        # TODO
        pass

    def test_install_signal_handlers(self):
        # TODO
        pass

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
        # TODO
        pass
