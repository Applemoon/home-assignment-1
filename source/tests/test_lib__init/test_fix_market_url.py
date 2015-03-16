import unittest
from source import lib


class LibInitFixMarketUrlTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.marketUrl = 'market://bestOfTheBestUrl'
        cls.notMarketUrl = 'notmarket://bestOfTheBestUrl'
        cls.endOfMarketUrl = 'bestOfTheBestUrl'
        cls.beginHttpUrl = 'http://play.google.com/store/apps/'

    def test_fix_market_url__ok_market_url(self):
        self.assertEquals(self.beginHttpUrl+self.endOfMarketUrl, lib.fix_market_url(self.marketUrl))

    def test_fix_market_url__not_market_url(self):
        self.assertEquals(self.beginHttpUrl+self.notMarketUrl, lib.fix_market_url(self.notMarketUrl))