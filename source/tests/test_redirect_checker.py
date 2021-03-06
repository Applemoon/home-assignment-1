import unittest
from mock import Mock, patch
from source.redirect_checker import main_loop, main


class RedirectCheckerTestCase(unittest.TestCase):

    def run_main_loop(self, worker_pool_size):
        config = Mock(WORKER_POOL_SIZE=worker_pool_size, SLEEP=0)
        with patch('source.redirect_checker.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                main_loop(config)

    @patch('source.redirect_checker.spawn_workers')
    @patch('source.redirect_checker.check_network_status')
    def test_main_loop_ok_network(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = True
        self.run_main_loop(3)
        self.assertEqual(mock_spawn_workers.call_count, 1)

    @patch('source.redirect_checker.spawn_workers')
    @patch('source.redirect_checker.check_network_status')
    def test_main_loop_ok_network_no_spawning(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = True
        self.run_main_loop(0)
        self.assertFalse(mock_spawn_workers.called)

    @patch('source.redirect_checker.spawn_workers')
    @patch('source.redirect_checker.check_network_status')
    def test_main_loop_network_not_ok(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = False

        config = Mock(WORKER_POOL_SIZE=3, SLEEP=0)
        child = Mock()

        with patch('source.redirect_checker.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                with patch('source.redirect_checker.active_children', return_value=[child]):
                    main_loop(config)

        self.assertFalse(mock_spawn_workers.called)
        self.assertEqual(child.terminate.call_count, 1)

    @patch('source.redirect_checker.main_loop')
    @patch('source.redirect_checker.dictConfig')
    @patch('source.redirect_checker.load_config_from_pyfile')
    @patch('source.redirect_checker.create_pidfile')
    @patch('source.redirect_checker.daemonize')
    def test_main_daemonize_create_pidfile(self, mock_daemonize, mock_create_pidfile,
                                           mock_load_config_from_pyfile, mock_dict_config, mock_main_loop):
        exit_code = 42
        mock_load_config_from_pyfile.return_value = Mock(LOGGING={}, EXIT_CODE=exit_code)
        args = ['1', '-c', '/conf_path', '-d', '-P', '/pidfile']

        main_result = main(args)

        self.assertEqual(mock_daemonize.call_count, 1)
        self.assertEqual(mock_create_pidfile.call_count, 1)
        self.assertEqual(mock_dict_config.call_count, 1)
        self.assertEqual(mock_main_loop.call_count, 1)
        self.assertEqual(main_result, exit_code)

