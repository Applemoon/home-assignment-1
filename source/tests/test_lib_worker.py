import unittest
import mock
from source.lib import worker


class LibWorkerTestCase(unittest.TestCase):
    def test_worker_dead_parent(self):
        config = mock.MagicMock()
        parent_pid = 42
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)):
            with mock.patch('os.path.exists', mock.Mock(return_value=False)):
                with mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
                    worker.worker(config, parent_pid)

        self.assertFalse(input_tube.called)