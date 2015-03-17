import unittest
import mock
from source.lib import worker


class LibWorkerTestCase(unittest.TestCase):
    # def test_worker_dead_parent(self):
    #     config = mock.MagicMock()
    #     parent_pid = 42
    #     tube = mock.MagicMock()
    #     input_tube = mock.MagicMock()
    #     output_tube = mock.MagicMock()
    #     with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
    #         with mock.patch('os.path.exists', mock.Mock(return_value=False)):
    #             with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
    #                 worker.worker(config, parent_pid)
    #
    #     self.assertFalse(input_tube.called)

    def test_get_redirect_history_from_task_error_and_not_recheck(self):
        task = mock.Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
            'suspicious': 'suspicious'
        }
        is_input = True
        data_modified = task.data.copy()
        data_modified['recheck'] = True
        timeout = 3
        with mock.patch(
                'source.lib.worker.get_redirect_history',
                mock.Mock(return_value=(['ERROR'], [], []))
        ) as get_redirect_history:
            self.assertEquals((is_input, data_modified), (worker.get_redirect_history_from_task(task, timeout)))

        get_redirect_history.assert_called_once()

    def test_get_redirect_history_from_task_else(self):
        task = mock.Mock()
        task.data = {
            'url': 'url',
            'recheck': True,
            'url_id': 'url_id'
        }
        return_value = [['ERROR'], [], []]
        is_input = False
        data_modified = {
            'url_id': task.data['url_id'],
            'result': return_value,
            'check_type': 'normal'
        }
        timeout = 3
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            self.assertEquals((is_input, data_modified), worker.get_redirect_history_from_task(task, timeout))

    def test_get_redirect_history_from_task_else_suspicious(self):
        task = mock.Mock()
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 'url_id',
            'suspicious': 'suspicious'
        }
        return_value = [[], [], []]
        is_input = False
        data_modified = {
            'url_id': task.data['url_id'],
            'result': return_value,
            'check_type': 'normal',
            'suspicious': task.data['suspicious']
        }
        timeout = 3
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            self.assertEquals((is_input, data_modified), worker.get_redirect_history_from_task(task, timeout))