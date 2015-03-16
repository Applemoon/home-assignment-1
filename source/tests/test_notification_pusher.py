import unittest
import mock
from source import notification_pusher


class NotificationPusherTestCase(unittest.TestCase):

    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        self.logger_temp = notification_pusher.logger
        notification_pusher.logger = mock.Mock()
        m_open = mock.mock_open()
        with mock.patch('source.notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                notification_pusher.create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))


