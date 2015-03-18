import unittest
from mock import Mock, patch, mock_open, MagicMock
from source.lib.utils import *


class LibUtilsTestCase(unittest.TestCase):

    def test_create_pidfile(self):
        pid = 42
        pidfile = '/file/path'
        m_open = mock_open()
        with patch('source.lib.utils.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                create_pidfile(pidfile)

        m_open.assert_called_once_with(pidfile, 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_daemonize_ok(self):
        pid = 42
        with patch('os.fork', Mock(return_value=pid)) as os_fork:
            with patch('os._exit', Mock()) as os_exit:
                daemonize()

        os_fork.assert_called_once_with()
        os_exit.assert_called_once_with(0)

    def test_daemonize_exception(self):
        pid = OSError("err")
        with patch('os.fork', Mock(side_effect=pid)) as os_fork:
            self.assertRaises(Exception, daemonize)

    def test_daemonize_ok_after_setsid(self):
        pid = 0
        fork_pid = 42
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()) as os_exit:
                    daemonize()

                    self.assertEquals(1, os_fork.call_count == 2)
                    os_setsid.assert_called_once_with()
                    os_exit.assert_called_once_with(0)

    def test_daemonize_exception_after_setsid(self):
        pid = 0
        fork_pid = OSError("err")
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()) as os_exit:
                    self.assertRaises(Exception, daemonize)

    def test_daemonize__not_exit(self):
        pid = 0
        fork_pid = 0
        with patch('os.fork', Mock(side_effect=[pid, fork_pid])) as os_fork:
            with patch('os.setsid', Mock()) as os_setsid:
                with patch('os._exit', Mock()) as os_exit:
                    daemonize()

                    self.assertTrue(os_fork.call_count == 2)
                    os_setsid.assert_called_once_with()
                    self.assertTrue(os_exit.call_count == 0)

    def test_load_config_from_pyfile(self):
        filepath = 'filepath/'

        def execfile(sefilepath, variables):
            variables['UPPER'] = {'key1': 1, 'key2': 'value2'}
            variables['lower'] = 42

        with patch('__builtin__.execfile', side_effect=execfile):
            cfg = load_config_from_pyfile(filepath)

            self.assertEquals(cfg.UPPER, {'key1': 1, 'key2': 'value2'})
            self.assertEquals(hasattr(cfg, 'lower_case'), False)

    def test_parse_cmd_args__abbr(self):
        cfg = '/conf'
        pidfile = '/pidfile'
        app_description = 'app_description'
        parsed_args = parse_cmd_args(['-c', cfg, '-P', pidfile, '-d'], app_description)
        self.assertEquals(parsed_args.config, cfg)
        self.assertEquals(parsed_args.pidfile, pidfile)
        self.assertTrue(parsed_args.daemon)

    def test_parse_cmd_args__full(self):
        cfg = '/conf'
        pidfile = '/pidfile'
        app_description = 'app_description'
        parsed_args = parse_cmd_args(['--config', cfg, '--pid', pidfile], app_description)
        self.assertEquals(parsed_args.config, cfg)
        self.assertEquals(parsed_args.pidfile, pidfile)
        self.assertFalse(parsed_args.daemon)

    def test_get_tube(self):
        host = 'localhost'
        port = 80
        space = 'space'
        name = 'tube_name'
        queue = MagicMock()
        with patch('source.lib.utils.tarantool_queue.Queue', Mock(return_value=queue)) as Queue:
            get_tube(host, port, space, name)
        Queue.assert_called_once_with(host=host, port=port, space=space)

    def test_spawn_workers(self):
        num = 3
        target = Mock()
        args = ''
        parent_pid = 42
        process = MagicMock()
        process.daemon = False
        process.start = Mock()
        with patch('source.lib.utils.Process', Mock(return_value=process)) as Process:
            spawn_workers(num, target, args, parent_pid)

        self.assertEquals(num, Process.call_count)
        self.assertEquals(num, process.start.call_count)
        self.assertTrue(process.daemon)

    def test_check_network_status__true(self):
        with patch('urllib2.urlopen', Mock()):
            self.assertTrue(check_network_status('http://url.ru', 5))

    def test_check_network_status__false(self):
        with patch('urllib2.urlopen', Mock(side_effect=[urllib2.URLError('error'), socket.error(), ValueError])):
            self.assertFalse(check_network_status('http://url.ru', 5))
