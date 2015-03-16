#!/usr/bin/env python2.7

import os
import socket
import sys
import unittest
from contextlib import contextmanager

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from source.tests.test_notification_pusher import NotificationPusherTestCase
from source.tests.test_redirect_checker import RedirectCheckerTestCase
from source.tests.test_lib__init.test_check_for_meta import LibInitCheckForMetaTestCase
from source.tests.test_lib__init.test_fix_market_url import LibInitFixMarketUrlTestCase
from source.tests.test_lib__init.test_prepare_url import LibInitPrepareUrlTestCase
from source.tests.test_lib__init.test_to_code import LibInitToCodeTestCase
from source.tests.test_lib__init.test_get_url import LibInitGetUrlTestCase
from source.tests.test_lib__init.test_make_pycurl_request import LibInitMakePycurlRequestTestCase
from source.tests.test_lib__init.test_get_counters import LibInitGetCountersTestCase
from source.tests.test_lib__init.test_get_redirect_history import LibInitGetRedirectHistoryTestCase
from source.tests.test_lib_utils.test_check_network_status import LibUtilsCheckNetworkStatusTestCase
from source.tests.test_lib_utils.test_create_pidfile import LibUtilsCreatePidfileTestCase
from source.tests.test_lib_utils.test_daemonize import LibUtilsDaemonizeTestCase
from source.tests.test_lib_utils.test_get_tube import LibUtilsGetTubeTestCase
from source.tests.test_lib_utils.test_load_config_from_pyfile import LibUtilsLoadConfigFromPyfileTestCase
from source.tests.test_lib_utils.test_parse_cmd_args import LibUtilsParseCmdArgsTestCase
from source.tests.test_lib_utils.test_spawn_workers import LibUtilsSpawnWorkersTestCase
from source.tests.test_lib_worker.test_get_redirect_history_from_task import LibWorkerGetRedirectHistoryFromTaskTestCase
from source.tests.test_lib_worker.test_worker import LibWorkerWorkerTestCase

@contextmanager
def mocked_connection():
    def _create_connection(*args, **kwargs):
        raise RuntimeError('Unmocked http request')

    original_connection = socket.create_connection
    socket.create_connection = _create_connection
    yield
    socket.create_connection = original_connection

if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        # libInit
        unittest.makeSuite(LibInitCheckForMetaTestCase),
        unittest.makeSuite(LibInitFixMarketUrlTestCase),
        unittest.makeSuite(LibInitPrepareUrlTestCase),
        unittest.makeSuite(LibInitToCodeTestCase),
        unittest.makeSuite(LibInitGetUrlTestCase),
        unittest.makeSuite(LibInitMakePycurlRequestTestCase),
        unittest.makeSuite(LibInitGetCountersTestCase),
        unittest.makeSuite(LibInitGetRedirectHistoryTestCase),
        # libUtils
        unittest.makeSuite(LibUtilsCheckNetworkStatusTestCase),
        unittest.makeSuite(LibUtilsCreatePidfileTestCase),
        unittest.makeSuite(LibUtilsDaemonizeTestCase),
        unittest.makeSuite(LibUtilsGetTubeTestCase),
        unittest.makeSuite(LibUtilsLoadConfigFromPyfileTestCase),
        unittest.makeSuite(LibUtilsParseCmdArgsTestCase),
        unittest.makeSuite(LibUtilsSpawnWorkersTestCase ),
        # libWorker
        unittest.makeSuite(LibWorkerGetRedirectHistoryFromTaskTestCase),
        unittest.makeSuite(LibWorkerWorkerTestCase),
    ))
    with mocked_connection():
        result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
