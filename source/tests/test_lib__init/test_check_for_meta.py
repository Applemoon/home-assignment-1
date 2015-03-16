import unittest
import mock
from source import lib


class LibInitCheckForMetaTestCase(unittest.TestCase):

    def setUp(self):
        self.url = 'url'

    def test_check_for_meta__meta_skip(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head></head>
                <body></body>
            </html>
        """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__meta_exist_content_skip(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta/>
                </head>
                <body></body>
            </html>
        """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__http_equiv_skip(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta content="5; url=http://example.com/"/>
                </head>
                <body></body>
            </html>
        """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__http_equiv_not_refresh(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta Http-equiv=None" content="5; url=http://example.com/">
                </head>
                <body></body>
            </html>
        """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__content_splitter_not_equals_2(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta Http-equiv="Refresh" content="5">
                </head>
                <body></body>
            </html>
        """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__uncorrect_url(self):
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta Http-equiv="Refresh" content="5; url is %$!@*">
                </head>
                <body></body>
            </html>
         """
        self.assertEquals(None, lib.check_for_meta(content, self.url))

    def test_check_for_meta__ok(self):
        url = 'http://url.ru'
        redirect_url = 'http://redirect-url.ru'
        content = """
            <!DOCTYPE html>
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=""" + redirect_url + """">
                </head>
                <body></body>
            </html>
        """
        with mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)):
            self.assertEquals(lib.urljoin(url, redirect_url), lib.check_for_meta(content, url))