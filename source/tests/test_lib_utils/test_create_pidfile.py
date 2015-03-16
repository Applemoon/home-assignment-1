import unittest
import mock
from source.lib import utils


class LibUtilsCreatePidfileTestCase(unittest.TestCase):
    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))