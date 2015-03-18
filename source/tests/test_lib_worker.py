import unittest
from mock import Mock, patch, mock_open, MagicMock
from source.lib.worker import *

URL = 'http://url.ru'
TIMEOUT = 5


class LibWorkerTestCase(unittest.TestCase):
    def to_code_side_effect(self, ignore):
        return self

    @patch('source.lib.to_unicode', Mock(side_effect=to_code_side_effect))
    def test_get_redirect_history_from_task__error_and_not_recheck(self):
        task = Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
        }
        data_modified = task.data.copy()
        data_modified['recheck'] = True
        with patch('source.lib.worker.get_redirect_history',
                   Mock(return_value=(['ERROR'], [], []))):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(True, is_input_result)
            self.assertEquals(data_modified, result_data)

    @patch('source.lib.to_unicode', Mock(side_effect=to_code_side_effect))
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
        with patch('source.lib.worker.get_redirect_history', Mock(return_value=return_value)):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(False, is_input_result)
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
        with patch('source.lib.worker.get_redirect_history', Mock(return_value=return_value)):
            is_input_result, result_data = get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(False, is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_worker__parent_proc_not_exist(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(return_value=False)) as os_path_exist:
                worker(config, parent_pid)

        self.assertTrue(os_path_exist.call_count == 1)

    def test_worker__not_task(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        tube.take = Mock(return_value=None)
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(side_effect=[True, False])):
                with patch('source.lib.worker.get_redirect_history_from_task',
                           Mock()) as get_redirect_history_from_task:
                    worker(config, parent_pid)

        self.assertTrue(get_redirect_history_from_task.call_count == 0)

    def test_worker__not_result(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        task = MagicMock()
        tube.take = Mock(return_value=task)
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(side_effect=[True, False])):
                with patch('source.lib.worker.get_redirect_history_from_task',
                           Mock(return_value=None)):
                    with patch('source.lib.worker.logger', Mock()) as logger:
                        worker(config, parent_pid)

        self.assertTrue(logger.debug.call_count == 0)

    def test_worker__input_tube_put(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        input_tube = MagicMock()
        output_tube = MagicMock()
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(side_effect=[True, False])):
                with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
                    with patch('source.lib.worker.get_redirect_history_from_task',
                               Mock(return_value=['is_input', 'data'])):
                        with patch('source.lib.worker.logger', Mock()):
                            worker(config, parent_pid)

        self.assertTrue(input_tube.put.call_count == 1)

    def test_worker__output_tube_put(self):
        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        input_tube = MagicMock()
        output_tube = MagicMock()
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(side_effect=[True, False])):
                with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
                    with patch('source.lib.worker.get_redirect_history_from_task',
                               Mock(return_value=[None, 'data'])):
                        with patch('source.lib.worker.logger', Mock()):
                            worker(config, parent_pid)

        self.assertTrue(output_tube.put.call_count == 1)

    def test_worker__database_error_exception(self):
        from source.lib.worker import DatabaseError

        config = MagicMock()
        parent_pid = 42
        tube = MagicMock()
        task = MagicMock()
        tube.take = Mock(return_value=task)
        task.ack = Mock(side_effect=DatabaseError)
        with patch('source.lib.worker.get_tube', Mock(return_value=tube)):
            with patch('os.path.exists', Mock(side_effect=[True, False])):
                with patch('source.lib.worker.get_redirect_history_from_task',
                                Mock(return_value=None)):
                    with patch('source.lib.worker.logger', Mock()) as logger:
                        worker(config, parent_pid)

        self.assertTrue(logger.exception.called)