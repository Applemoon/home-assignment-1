import unittest
import mock
from source import lib


class LibInitMakePycurlRequestTestCase(unittest.TestCase):
    # def test_make_pycurl_request_redirect_url(self):
    #     url = 'http://url.ru'
    #     timeout = 30
    #     content = 'content'
    #     redirect_url = 'http://redirect-url.ru'
    #     useragent = 'useragent'
    #     buff = mock.MagicMock()
    #     buff.getvalue = mock.Mock(return_value=content)
    #     curl = mock.MagicMock()
    #     curl.setopt = mock.Mock()
    #     curl.perform = mock.Mock()
    #     curl.getinfo = mock.Mock(return_value=redirect_url)
    #     with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
    #         with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
    #             self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout))
    #             self.assertEquals((content, redirect_url), lib.make_pycurl_request(url, timeout, useragent))
    def test_make_pycurl_request__first(self):
        url = 'http://ya.ru'
        timeout = 30
        lib.make_pycurl_request(url, timeout)
