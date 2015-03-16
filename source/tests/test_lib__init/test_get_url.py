import unittest
import mock
from source import lib


class LibInitGetUrlTestCase(unittest.TestCase):
    def test_get_url_not_redirect(self):
        url = 'http://url.ru'
        timeout = 30
        content = 'content'
        new_redirect_url = 'http://odnoklassniki.ru/redirect-url/st.redirect'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=[content, new_redirect_url])):
            redirect_url, redirect_type, return_content = lib.get_url(url, timeout)

        self.assertEquals(None, redirect_url)
        self.assertEquals(None, redirect_type)
        self.assertEquals(content, return_content)