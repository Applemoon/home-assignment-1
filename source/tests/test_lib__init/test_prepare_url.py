import unittest
from source import lib


class LibInitPrepareUrlTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.noneUrl = None
        cls.urlOk = 'http://netloc/path;parameters?query=argument#fragment'
        cls.urlQsRaw = 'http://netloc/path;qs quote plus?query=argument#fragment'
        cls.urlQsResult = 'http://netloc/path;qs+quote+plus?query=argument#fragment'
        cls.urlPathRaw = 'http://netloc/ p a t h ;parameters?query=argument#fragment'
        cls.urlPathResult = 'http://netloc/%20p%20a%20t%20h%20;parameters?query=argument#fragment'
        cls.urlBadNetloc = 'http://.netloc/path;parameters?query=argument#fragment'

    def test_prepare_url__none_url(self):
        self.assertEquals(lib.prepare_url(self.noneUrl), self.noneUrl)

    def test_prepare_url__ok(self):
        self.assertEquals(self.urlOk, lib.prepare_url(self.urlOk))

    def test_prepare_url__qs_quote_plus(self):
        self.assertEquals(self.urlQsResult, lib.prepare_url(self.urlQsRaw))

    def test_prepare_url__path_quote(self):
        self.assertEquals(self.urlPathResult, lib.prepare_url(self.urlPathRaw))

    def test_prepare_url__encode_exception(self):
        with self.assertRaises(UnicodeError):
            lib.prepare_url(self.urlBadNetloc)