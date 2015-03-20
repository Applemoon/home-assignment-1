import unittest
from mock import Mock, patch, MagicMock
from source.lib.worker import *

URL = 'http://url.ru'
TIMEOUT = 5


class LibWorkerTestCase(unittest.TestCase):

    def test_get_redirect_history_from_task__error_and_not_recheck(self):
        task = Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
        }
        data_modified = task.data.copy()
        data_modified['recheck'] = True
        with patch('source.lib.worker.get_redirect_history', return_value=(['ERROR'], [], [])):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertTrue(is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_get_redirect_history_from_task__else(self):
        task = Mock()
        task.data = {
            'url': 'url',
            'recheck': True,
            'url_id': 'url_id'
        }
        return_value = [['ERROR'], [], []]
        data_modified = {
            'url_id': task.data['url_id'],
            'result': return_value,
            'check_type': 'normal'
        }
        with patch('source.lib.worker.get_redirect_history', return_value=return_value):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertFalse(is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_get_redirect_history_from_task_else_suspicious(self):
        task = Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
            'suspicious': 'suspicious'
        }
        return_value = [[], [], []]
        data_modified = {
            'url_id': task.data['url_id'],
            'result': return_value,
            'check_type': 'normal',
            'suspicious': task.data['suspicious']
        }
        with patch('source.lib.worker.get_redirect_history', return_value=return_value):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertFalse(is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_worker__parent_proc_not_exist(self):
        config = Mock()
        parent_pid = 42
        tube = MagicMock()
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', return_value=False) as os_path_exist:
                worker(config, parent_pid)

        self.assertEquals(os_path_exist.call_count, 1)

    def test_worker__not_task(self):
        config = Mock()
        parent_pid = 42
        tube = MagicMock()
        tube.take.return_value = None
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', side_effect=[True, False]):
                with patch('source.lib.worker.get_redirect_history_from_task') as get_redirect_history_from_task:
                    worker(config, parent_pid)

        self.assertEquals(get_redirect_history_from_task.call_count, 0)

    def test_worker__not_result(self):
        config = Mock()
        parent_pid = 42
        tube = MagicMock()
        task = MagicMock()
        tube.take.return_value=task
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', side_effect=[True, False]):
                with patch('source.lib.worker.get_redirect_history_from_task', return_value=None):
                    with patch('source.lib.worker.logger', ) as logger:
                        worker(config, parent_pid)

        self.assertEquals(logger.debug.call_count, 0)

    def test_worker__input_tube_put(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        input_tube = MagicMock()
        output_tube = MagicMock()
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', side_effect=[True, False]):
                with patch('source.lib.worker.get_tube', side_effect=[input_tube, output_tube]):
                    with patch('source.lib.worker.get_redirect_history_from_task', return_value=['is_input', 'data']):
                        with patch('source.lib.worker.logger'):
                            worker(config, parent_pid)

        self.assertEquals(input_tube.put.call_count, 1)

    def test_worker__output_tube_put(self):
        config = Mock()
        parent_pid = 42
        tube = MagicMock()
        input_tube = MagicMock()
        output_tube = MagicMock()
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', side_effect=[True, False]):
                with patch('source.lib.worker.get_tube', side_effect=[input_tube, output_tube]):
                    with patch('source.lib.worker.get_redirect_history_from_task', return_value=[None, 'data']):
                        with patch('source.lib.worker.logger'):
                            worker(config, parent_pid)

        self.assertEquals(output_tube.put.call_count, 1)

    def test_worker__database_error_exception(self):
        from source.lib.worker import DatabaseError

        config = Mock()
        parent_pid = 42
        tube = MagicMock()
        task = Mock()
        tube.take.return_value = task
        task.ack.side_effect = DatabaseError
        with patch('source.lib.worker.get_tube', return_value=tube):
            with patch('os.path.exists', side_effect=[True, False]):
                with patch('source.lib.worker.get_redirect_history_from_task', return_value=None):
                    with patch('source.lib.worker.logger') as logger:
                        worker(config, parent_pid)

        self.assertTrue(logger.exception.called)