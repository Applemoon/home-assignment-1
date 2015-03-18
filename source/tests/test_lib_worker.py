import unittest
import mock
from source.lib import worker

URL = 'http://url.ru'
TIMEOUT = 5


class LibWorkerTestCase(unittest.TestCase):
    def to_code_side_effect(self, ignore):
        return self

    @mock.patch('source.lib.to_unicode', mock.Mock(side_effect=to_code_side_effect))
    def test_get_redirect_history_from_task__error_and_not_recheck(self):
        task = mock.Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
        }
        data_modified = task.data.copy()
        data_modified['recheck'] = True
        with mock.patch('source.lib.worker.get_redirect_history',
                        mock.Mock(return_value=(['ERROR'], [], []))):
            is_input_result, result_data = worker.get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(True, is_input_result)
            self.assertEquals(data_modified, result_data)

    @mock.patch('source.lib.to_unicode', mock.Mock(side_effect=to_code_side_effect))
    def test_get_redirect_history_from_task__else(self):
        task = mock.Mock()
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
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            is_input_result, result_data = worker.get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(False, is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_get_redirect_history_from_task_else_suspicious(self):
        task = mock.Mock()
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
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            is_input_result, result_data = worker.get_redirect_history_from_task(task, TIMEOUT)
            self.assertEquals(False, is_input_result)
            self.assertEquals(data_modified, result_data)

    def test_worker__parent_proc_not_exist(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(return_value=False)) as os_path_exist:
                worker.worker(config, parent_pid)

        self.assertTrue(os_path_exist.call_count == 1)

    def test_worker__not_task(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        tube.take = mock.Mock(return_value=None)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task',
                                mock.Mock()) as get_redirect_history_from_task:
                    worker.worker(config, parent_pid)

        self.assertTrue(get_redirect_history_from_task.call_count == 0)

    def test_worker__not_result(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        task = mock.MagicMock()
        tube.take = mock.Mock(return_value=task)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task',
                                mock.Mock(return_value=None)):
                    with mock.patch('source.lib.worker.logger', mock.Mock()) as logger:
                        worker.worker(config, parent_pid)

        self.assertTrue(logger.debug.call_count == 0)

    def test_worker__input_tube_put(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task',
                                    mock.Mock(return_value=['is_input', 'data'])):
                        with mock.patch('source.lib.worker.logger', mock.Mock()):
                            worker.worker(config, parent_pid)

        self.assertTrue(input_tube.put.call_count == 1)

    def test_worker__output_tube_put(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task',
                                    mock.Mock(return_value=[None, 'data'])):
                        with mock.patch('source.lib.worker.logger', mock.Mock()):
                            worker.worker(config, parent_pid)

        self.assertTrue(output_tube.put.call_count == 1)

    def test_worker__database_error_exception(self):
        from source.lib.worker import DatabaseError

        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        task = mock.MagicMock()
        tube.take = mock.Mock(return_value=task)
        task.ack = mock.Mock(side_effect=DatabaseError)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
                with mock.patch('source.lib.worker.get_redirect_history_from_task',
                                mock.Mock(return_value=None)):
                    with mock.patch('source.lib.worker.logger', mock.Mock()) as logger:
                        worker.worker(config, parent_pid)

        self.assertTrue(logger.exception.called)