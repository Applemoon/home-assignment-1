import unittest
import mock
from source import lib

REDIRECT_META = 'meta_tag'
REDIRECT_HTTP = 'http_status'

URL = 'http://url.ru'
TIMEOUT = 5


class LibInitTestCase(unittest.TestCase):

    def test_check_for_meta__meta_skip(self):
        content = """<nothing>"""
        self.assertEquals(None, lib.check_for_meta(content, 'http://first.com/'))

    def test_check_for_meta__meta_exist_content_skip(self):
        content = """<meta/>"""
        self.assertEquals(None, lib.check_for_meta(content, 'http://first.com/'))

    def test_check_for_meta__http_equiv_skip(self):
        content = """<meta content="5; url=http://second.com/"/>"""
        self.assertEquals(None, lib.check_for_meta(content, 'http://first.com/'))

    def test_check_for_meta__http_equiv_not_refresh(self):
        content = """<meta Http-equiv=None" content="5; url=http://second.com/">"""
        self.assertEquals(None, lib.check_for_meta(content, 'http://first.com/'))

    def test_check_for_meta__content_splitter_not_equals_2(self):
        content = """<meta Http-equiv="Refresh" content="5">"""
        self.assertEquals(None, lib.check_for_meta(content, 'url'))

    def test_check_for_meta__incorrect_url(self):
        content = """<meta Http-equiv="Refresh" content="5; url is %$!@*">"""
        self.assertEquals(None, lib.check_for_meta(content, 'http://first.com/'))

    def test_check_for_meta__ok(self):
        this_url = 'http://url.ru'
        redirect_url = 'http://redirect-url.ru'
        content = """<meta http-equiv="refresh" content="5; url=""" + redirect_url + """">"""
        with mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)):
            self.assertEquals(lib.urljoin(this_url, redirect_url), lib.check_for_meta(content, this_url))

    def test_fix_market_url__ok_market_url(self):
        market_url = 'market://bestOfTheBestUrl'
        begin_http_url = 'http://play.google.com/store/apps/'
        end_of_market_url = 'bestOfTheBestUrl'
        self.assertEquals(begin_http_url+end_of_market_url, lib.fix_market_url(market_url))

    def test_fix_market_url__not_market_url(self):
        not_market_url = 'not-market://bestOfTheBestUrl'
        begin_http_url = 'http://play.google.com/store/apps/'
        self.assertEquals(begin_http_url+not_market_url, lib.fix_market_url(not_market_url))

    def test_get_counters_yandex_google(self):
        content = 'mc.yandex.ru/metrika/watch.js google-analytics.com/ga.js'
        return_counters = lib.get_counters(content)
        self.assertEquals(['GOOGLE_ANALYTICS', 'YA_METRICA'], return_counters)

    def test_get_counters_null(self):
        content = 'content_without_counters'
        return_counters = lib.get_counters(content)
        self.assertEquals([], return_counters)

    def side_effect(self, url):
        return url

    def test_get_redirect_history__mm_url(self):
        mm_url = 'https://my.mail.ru/apps/'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            history_types, history_urls, return_counters = lib.get_redirect_history(mm_url, TIMEOUT)

            self.assertEquals([], history_types)
            self.assertEquals([mm_url], history_urls)
            self.assertEquals([], return_counters)

    def test_get_redirect_history__ok_url(self):
        ok_url = 'https://www.odnoklassniki.ru/'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            history_types, history_urls, return_counters = lib.get_redirect_history(ok_url, TIMEOUT)

            self.assertEquals([], history_types)
            self.assertEquals([ok_url], history_urls)
            self.assertEquals([], return_counters)

    def test_get_redirect_history__not_redirect_url(self):
        none_url = ''
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            history_types, history_urls, return_counters = lib.get_redirect_history(none_url, TIMEOUT)

            self.assertEquals([], history_types)
            self.assertEquals([''], history_urls)
            self.assertEquals([], return_counters)

    def test_get_redirect_history__not_redirect_url_with_content(self):
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[None, None, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value='counters')):
                    history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT)

                self.assertEquals([], history_types)
                self.assertEquals([URL], history_urls)
                self.assertEquals(counters, return_counters)

    def test_get_redirect_history__redirect_type_error(self):
        type_error = 'ERROR'
        redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, type_error, 'content'])):
                history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT, 1)

                self.assertEquals([type_error], history_types)
                self.assertEquals([URL, redirect_url], history_urls)
                self.assertEquals([], return_counters)

    def test_get_redirect_history__redirect_url_in_history_urls(self):
        redirect_type = 'redirect_type'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[URL, redirect_type, 'content'])):
                history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT)

                self.assertEquals([redirect_type], history_types)
                self.assertEquals([URL, URL], history_urls)
                self.assertEquals([], return_counters)

    def test_get_redirect_history__max_redirects(self):
        redirect_type = 'redirect_type'
        redirect_url = 'http://redirect-url.ru'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type, 'content'])):
                history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT, 0)

                self.assertEquals([redirect_type], history_types)
                self.assertEquals([URL, redirect_url], history_urls)
                self.assertEquals([], return_counters)

    def test_get_redirect_history__redirect_url_in_history_urls_with_content(self):
        redirect_type = 'redirect_type'
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[URL, redirect_type, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value=counters)):
                    history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT)

                    self.assertEquals([redirect_type], history_types)
                    self.assertEquals([URL, URL], history_urls)
                    self.assertEquals(counters, return_counters)

    def test_get_redirect_history__max_redirects_with_content(self):
        redirect_type = 'redirect_type'
        redirect_url = 'http://redirect-url.ru'
        counters = 'counters'
        with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
            with mock.patch('source.lib.get_url', mock.Mock(return_value=[redirect_url, redirect_type, 'content'])):
                with mock.patch('source.lib.get_counters', mock.Mock(return_value=counters)):
                    history_types, history_urls, return_counters = lib.get_redirect_history(URL, TIMEOUT, 0)

                    self.assertEquals([redirect_type], history_types)
                    self.assertEquals([URL, redirect_url], history_urls)
                    self.assertEquals(counters, return_counters)

    def test_get_url__not_redirect(self):
        not_redirect_url = 'http://odnoklassniki.ru/redirect-url/st.redirect'
        with mock.patch("source.lib.make_pycurl_request",
                        mock.Mock(return_value=['content', not_redirect_url])):
            redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

        self.assertEquals(None, redirect_url)
        self.assertEquals(None, redirect_type)
        self.assertEquals('content', return_content)

    def test_get_url__new_redirect_url(self):
        new_redirect_url = 'http://odnoklassniki.ru/redirect-url/'
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content', new_redirect_url])):
            with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
                redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

            self.assertEquals(new_redirect_url, redirect_url)
            self.assertEquals(REDIRECT_HTTP, redirect_type)
            self.assertEquals('content', return_content)

    def test_get_url__redirect_none_after_check_for_meta(self):
        none_url = None
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content', none_url])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=none_url)):
                with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
                    redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

                    self.assertEquals(None, redirect_url)
                    self.assertEquals(None, redirect_type)
                    self.assertEquals('content', return_content)

    def test_get_url__redirect_not_none_after_check_for_meta(self):
        none_url = None
        new_redirect_url = 'http://odnoklassniki.ru/redirect-url/'
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content', none_url])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
                    redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

                    self.assertEquals(new_redirect_url, redirect_url)
                    self.assertEquals(REDIRECT_META, redirect_type)
                    self.assertEquals('content', return_content)

    def test_get_url__redirect_market(self):
        market_redirect_url = 'market://bestOfTheBestUrl'
        fix_redirect_url = 'http://play.google.com/store/apps/bestOfTheBestUrl'
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content', market_redirect_url])):
                with mock.patch('source.lib.fix_market_url', mock.Mock(return_value=fix_redirect_url)):
                    with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
                        redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

                        self.assertEquals(fix_redirect_url, redirect_url)
                        self.assertEquals(REDIRECT_HTTP, redirect_type)
                        self.assertEquals('content', return_content)

    def test_get_url__redirect_market_after_check_for_meta(self):
        market_redirect_url = 'market://bestOfTheBestUrl'
        fix_redirect_url = 'http://play.google.com/store/apps/bestOfTheBestUrl'
        none_url = None
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content', none_url])):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=market_redirect_url)):
                with mock.patch('source.lib.fix_market_url', mock.Mock(return_value=fix_redirect_url)):
                    with mock.patch('source.lib.prepare_url', mock.Mock(side_effect=self.side_effect)):
                        redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

                        self.assertEquals(fix_redirect_url, redirect_url)
                        self.assertEquals(REDIRECT_META, redirect_type)
                        self.assertEquals('content', return_content)

    def test_get_url__exception(self):
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=['content'])):
            redirect_url, redirect_type, return_content = lib.get_url(URL, TIMEOUT)

        self.assertEquals(URL, redirect_url)
        self.assertEquals('ERROR', redirect_type)
        self.assertEquals(None, return_content)

    def test_make_pycurl_request__redirect_url(self):
        buff = mock.Mock()
        buff.getvalue = mock.Mock(return_value='content')
        curl = mock.Mock()
        redirect_url = 'http://redirect-url.ru'
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.to_str', mock.Mock(return_value=URL)):
            with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
                with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                    self.assertEquals(('content', redirect_url), lib.make_pycurl_request(URL, TIMEOUT))
                    self.assertEquals(('content', redirect_url), lib.make_pycurl_request(URL, TIMEOUT, 'useragent'))

    def test_make_pycurl_request__redirect_url_none(self):
        url_none = None
        buff = mock.Mock()
        buff.getvalue = mock.Mock(return_value='content')
        curl = mock.Mock()
        curl.getinfo = mock.Mock(return_value=url_none)
        with mock.patch('source.lib.to_str', mock.Mock(return_value=URL)):
            with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
                with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                    self.assertEquals(('content', url_none), lib.make_pycurl_request(URL, TIMEOUT))
                    self.assertEquals(('content', url_none), lib.make_pycurl_request(URL, TIMEOUT, 'useragent'))

    def test_prepare_url__none_url(self):
        none_url = None
        self.assertEquals(lib.prepare_url(none_url), none_url)

    def test_prepare_url__ok(self):
        url_ok = 'http://netloc/path;parameters?query=argument#fragment'
        self.assertEquals(url_ok, lib.prepare_url(url_ok))

    def test_prepare_url__qs_quote_plus(self):
        url_qs_raw = 'http://netloc/path;qs quote plus?query=argument#fragment'
        url_qs_result = 'http://netloc/path;qs+quote+plus?query=argument#fragment'
        self.assertEquals(url_qs_result, lib.prepare_url(url_qs_raw))

    def test_prepare_url__path_quote(self):
        url_path_raw = 'http://netloc/ p a t h ;parameters?query=argument#fragment'
        url_path_result = 'http://netloc/%20p%20a%20t%20h%20;parameters?query=argument#fragment'
        self.assertEquals(url_path_result, lib.prepare_url(url_path_raw))

    def test_prepare_url__encode_exception(self):
        url_bad_netloc = 'http://.netloc/path;parameters?query=argument#fragment'
        with self.assertRaises(UnicodeError):
            lib.prepare_url(url_bad_netloc)

    def test_to_unicode__from_unicode(self):
        self.assertIsInstance(lib.to_unicode(u'unicode'), unicode)

    def test_to_unicode__from_str(self):
        self.assertIsInstance(lib.to_unicode('str'), unicode)

    def test_to_str__from_unicode(self):
        self.assertIsInstance(lib.to_str(u'unicode'), str)

    def test_to_str__from_str(self):
        self.assertIsInstance(lib.to_str('str'), str)