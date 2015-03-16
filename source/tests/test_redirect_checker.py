import unittest
from mock import Mock, patch
from redirect_checker import main_loop, main


class RedirectCheckerTestCase(unittest.TestCase):

    def run_main_loop(self, worker_pool_size, mock_spawn_workers, expected_spawns_count):
        sleep = Mock(side_effect=KeyboardInterrupt)

        config = Mock(WORKER_POOL_SIZE=worker_pool_size, SLEEP=0)

        with patch('redirect_checker.sleep', sleep):
            with self.assertRaises(KeyboardInterrupt):
                main_loop(config)

        self.assertEqual(len(mock_spawn_workers.mock_calls), expected_spawns_count)

    @patch('redirect_checker.spawn_workers')
    @patch('redirect_checker.check_network_status')
    def test_main_loop_ok_network(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = True
        self.run_main_loop(3, mock_spawn_workers, 1)

    @patch('redirect_checker.spawn_workers')
    @patch('redirect_checker.check_network_status')
    def test_main_loop_ok_network_no_spawning(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = True
        self.run_main_loop(0, mock_spawn_workers, 0)

    @patch('redirect_checker.spawn_workers')
    @patch('redirect_checker.check_network_status')
    def test_main_loop_network_not_ok(self, mock_check_network_status, mock_spawn_workers):
        mock_check_network_status.return_value = False
        self.run_main_loop(3, mock_spawn_workers, 0)

    @patch('redirect_checker.main_loop')
    @patch('redirect_checker.dictConfig')
    @patch('redirect_checker.load_config_from_pyfile')
    @patch('redirect_checker.create_pidfile')
    @patch('redirect_checker.daemonize')
    def test_main_daemonize_create_pidfile(self, mock_daemonize, mock_create_pidfile,
                                           mock_load_config_from_pyfile, mock_dictConfig, mock_main_loop):
        exit_code = 42
        mock_load_config_from_pyfile.return_value = Mock(LOGGING={}, EXIT_CODE=exit_code)
        args = ['1', '-c', '/conf_path']
        main_result = main(args)

        self.assertFalse(mock_daemonize.called)
        self.assertFalse(mock_create_pidfile.called)
        self.assertEqual(main_result, exit_code)

        args = ['1', '-c', '/conf_path', '-d', '-P', '/pidfile']
        main_result = main(args)

        self.assertTrue(mock_daemonize.called)
        self.assertTrue(mock_create_pidfile.called)
        self.assertEqual(main_result, exit_code)
