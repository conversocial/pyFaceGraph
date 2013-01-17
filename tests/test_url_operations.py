from unittest import TestCase
from facegraph import graph
from facegraph import url_operations as ops
from facegraph.fql import FQL
from mock import patch, Mock
import httplib

class CustomExceptionsTest(TestCase):
    def _set_up_mock_httplib(self, desired_response):
        mock_file = Mock()
        mock_file.read = Mock(return_value=desired_response)

        mock_r = Mock()

        mock_getresponse = Mock(return_value=mock_file)
        mock_r.getresponse = mock_getresponse

        mock_httplib = Mock(spec=httplib)
        mock_httplib.HTTPSConnection = Mock(return_value=mock_r)

        return mock_httplib

    def test_empty_response(self):
        mock_httplib = self._set_up_mock_httplib('')
        with self.assertRaises(graph.EmptyStringReturnedException):
            graph.Graph.post_mime('url', httplib=mock_httplib)

    def test_bad_json_response(self):
        mock_httplib = self._set_up_mock_httplib('invalid')
        with self.assertRaises(graph.WrappedJSONDecodeError):
            graph.Graph.post_mime('url', httplib=mock_httplib)


class UrlOperationsTests(TestCase):
    def test_get_path(self):
        self.assertEquals('', ops.get_path(u'http://a.com'))
        self.assertEquals('/', ops.get_path(u'http://a.com/'))
        self.assertEquals('/a', ops.get_path(u'http://a.com/a'))
        self.assertEquals('/a/', ops.get_path(u'http://a.com/a/'))
        self.assertEquals('/a/b', ops.get_path(u'http://a.com/a/b'))

    def test_get_host(self):
        self.assertEquals('a.com', ops.get_host('http://a.com'))
        self.assertEquals('a.com', ops.get_host('http://a.com/a/b'))
        self.assertEquals('a.com', ops.get_host('http://a.com/a?a=b'))

    def test_add_path(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com/', ops.add_path(url, ''))
        self.assertEquals('http://a.com/path', ops.add_path(url, 'path'))
        self.assertEquals('http://a.com/path', ops.add_path(url, '/path'))
        self.assertEquals('http://a.com/path/', ops.add_path(url, 'path/'))
        self.assertEquals('http://a.com/path/', ops.add_path(url, '/path/'))

    def test_add_path_trailing_slash(self):
        url = u'http://a.com/'
        self.assertEquals('http://a.com/path', ops.add_path(url, 'path'))
        self.assertEquals('http://a.com/path', ops.add_path(url, '/path'))
        self.assertEquals('http://a.com/path/', ops.add_path(url, 'path/'))
        self.assertEquals('http://a.com/path/', ops.add_path(url, '/path/'))

    def test_add_path_existing_path(self):
        url = u'http://a.com/path1'
        self.assertEquals('http://a.com/path1/path2', ops.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2', ops.add_path(url, '/path2'))
        self.assertEquals('http://a.com/path1/path2/', ops.add_path(url, 'path2/'))
        self.assertEquals('http://a.com/path1/path2/', ops.add_path(url, '/path2/'))

    def test_add_path_trailing_slash_and_existing_path(self):
        url = u'http://a.com/path1/'
        self.assertEquals('http://a.com/path1/path2', ops.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2', ops.add_path(url, '/path2'))
        self.assertEquals('http://a.com/path1/path2/', ops.add_path(url, 'path2/'))
        self.assertEquals('http://a.com/path1/path2/', ops.add_path(url, '/path2/'))

    def test_add_path_fragment(self):
        url = u'http://a.com/path1/#anchor'
        self.assertEquals('http://a.com/path1/path2#anchor', ops.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2/#anchor', ops.add_path(url, 'path2/'))

    def test_add_path_query_string(self):
        url = u'http://a.com/path1/?a=b'
        self.assertEquals('http://a.com/path1/path2?a=b', ops.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2/?a=b', ops.add_path(url, 'path2/'))

    def test_query_param(self):
        self.assertEquals(('a', 'b'), ops._query_param('a', 'b'))

    def test_query_param_unicode(self):
        # unicode objects should be encoded as utf-8 bytes
        self.assertEquals(('a', 'b'), ops._query_param('a', u'b'))
        self.assertEquals(('a', '\xc3\xa9'), ops._query_param('a', u'\xe9'))

        # bytes should be remain as bytes
        self.assertEquals(('a', '\xc3\xa9'), ops._query_param('a', '\xc3\xa9'))

    def test_add_query_params(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com?a=b', ops.add_query_params(url, ('a', 'b')))
        self.assertEquals('http://a.com?a=b', ops.add_query_params(url, {'a': 'b'}))
        self.assertEquals('http://a.com?a=%C3%A9', ops.add_query_params(url, {'a': '\xc3\xa9'}))

        url = u'http://a.com/path'
        self.assertEquals('http://a.com/path?a=b', ops.add_query_params(url, {'a': 'b'}))

        url = u'http://a.com?a=b'
        self.assertEquals('http://a.com?a=b&a=c', ops.add_query_params(url, ('a', 'c')))
        self.assertEquals('http://a.com?a=b&c=d', ops.add_query_params(url, ('c', 'd')))

    def test_update_query_params(self):
        url = u'http://a.com?a=b'
        self.assertEquals('http://a.com?a=b', ops.update_query_params(url, {}))
        self.assertEquals('http://a.com?a=c', ops.update_query_params(url, ('a', 'c')))
        self.assertEquals('http://a.com?a=b&c=d', ops.update_query_params(url, {'c': 'd'}))
        self.assertEquals('http://a.com?a=%C4%A9', ops.update_query_params(url, {'a': '\xc4\xa9'}))

        url = u'http://a.com/path?a=b'
        self.assertEquals('http://a.com/path?a=c', ops.update_query_params(url, {'a': 'c'}))

    def test_escaping(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com?my+key=c', ops.add_query_params(url, ('my key', 'c')))
        self.assertEquals('http://a.com?c=my+val', ops.add_query_params(url, ('c', 'my val')))

    def test_no_double_escaping_existing_params(self):
        url = 'http://a.com?a=%C4%A9'
        self.assertEquals('http://a.com?a=%C4%A9&c=d', ops.update_query_params(url, {'c': 'd'}))

        url = 'http://a.com?a=my+val'
        self.assertEquals('http://a.com?a=my+val&c=d', ops.update_query_params(url, {'c': 'd'}))

class GraphUrlTests(TestCase):
    def setUp(self):
        self.graph = graph.Graph()

    def test_initial_state(self):
        self.assertEquals(graph.Graph.API_ROOT, self.graph.url)

    def test_getitem(self):
        expected = 'https://graph.facebook.com/path'
        self.assertEquals(expected, self.graph.path.url)

        expected = 'https://graph.facebook.com/path/path2'
        self.assertEquals(expected, self.graph.path.path2.url)

    def test_getitem_slice(self):
        url = self.graph[0:20].url
        self.assertTrue(url.startswith('https://graph.facebook.com/?'))
        self.assertTrue('offset=0' in url)
        self.assertTrue('limit=20' in url)

    def test_getattr(self):
        expected = 'https://graph.facebook.com/path'
        self.assertEquals(expected, self.graph['path'].url)

        expected = 'https://graph.facebook.com/path/path2'
        self.assertEquals(expected, self.graph['path']['path2'].url)


class FQLTests(TestCase):
    def setUp(self):
        self.fql = FQL(access_token='abc123')

    @patch('facegraph.fql.FQL.fetch_json')
    def test_call(self, mock_fetch):
        self.fql('my_query')
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.query?'))
        self.assertTrue('query=my_query' in url)
        self.assertTrue('access_token=abc123' in url)

    @patch('facegraph.fql.FQL.fetch_json')
    def test_call_with_arbitrary_params(self, mock_fetch):
        self.fql('my_query', key='value')
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.query?'))
        self.assertTrue('query=my_query' in url)
        self.assertTrue('access_token=abc123' in url)
        self.assertTrue('key=value' in url)

    @patch('facegraph.fql.FQL.fetch_json')
    def test_multi(self, mock_fetch):
        self.fql.multi(['my_query1', 'my_query2'])
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.multiquery?'))
        self.assertTrue("&queries=%5B%22my_query1%22%2C+%22my_query2%22%5D" in url)
