import unittest
from source import lib


class LibInitToCodeTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.unicode = u'unicode'
        cls.str = 'str'

    def test_to_unicode__from_unicode(self):
        self.assertIsInstance(lib.to_unicode(self.unicode), unicode)

    def test_to_unicode__from_str(self):
        self.assertIsInstance(lib.to_unicode(self.str), unicode)

    def test_to_str__from_unicode(self):
        self.assertIsInstance(lib.to_str(self.unicode), str)

    def test_to_str__from_str(self):
        self.assertIsInstance(lib.to_str(self.str), str)