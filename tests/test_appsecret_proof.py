from unittest import TestCase

from mock import Mock, patch

from facegraph.api import Api, get_appsecret_proof
from facegraph.graph import Graph


TEST_APP_SECRET = 'test_app_secret'
TEST_ACCESS_TOKEN = 'test_access_token'
TEST_FQL = 'test_query'
EXPECTED_APPSECRET_PROOF = 'f86b8540509cdb3ad6b1ed956b4c197aff473ad0b9cf075e0b0dca4a8302f6fc'


class GetAppsecretProofTests(TestCase):

    def test_hash(self):
        self.assertEqual(
            EXPECTED_APPSECRET_PROOF,
            get_appsecret_proof(TEST_APP_SECRET, TEST_ACCESS_TOKEN)
        )


class GraphAppsecretProofNoInjectionTests(TestCase):

    @patch('facegraph.graph.session')
    def test_get_without_secret_and_token(self, mock_session):
        mock_session.get.return_value.content = '{}'
        graph = Graph()
        graph.me.call_fb()
        mock_session.get.assert_called_once_with(
            'https://graph.facebook.com/me')

    @patch('facegraph.graph.session')
    def test_get_without_secret(self, mock_session):
        mock_session.get.return_value.content = '{}'
        graph = Graph(access_token=TEST_ACCESS_TOKEN)
        graph.me.call_fb()
        mock_session.get.assert_called_once_with(
            'https://graph.facebook.com/me?access_token=%s' % TEST_ACCESS_TOKEN)

    @patch('facegraph.graph.session')
    def test_get_without_token(self, mock_session):
        mock_session.get.return_value.content = '{}'
        graph = Graph(app_secret=TEST_APP_SECRET)
        graph.me.call_fb()
        mock_session.get.assert_called_once_with(
            'https://graph.facebook.com/me')

    @patch('facegraph.graph.session')
    def test_post_without_secret_and_token(self, mock_session):
        mock_session.post.return_value.content = '{}'
        graph = Graph()
        graph.me.post(test_param='data needed to force POST request')
        mock_session.post.assert_called_once_with(
            'https://graph.facebook.com/me', data='test_param=data+needed+to+force+POST+request')

    @patch('facegraph.graph.session')
    def test_post_without_secret(self, mock_session):
        mock_session.post.return_value.content = '{}'
        graph = Graph(access_token=TEST_ACCESS_TOKEN)
        graph.me.post()
        mock_session.post.assert_called_once_with(
            'https://graph.facebook.com/me', data='access_token=%s' % TEST_ACCESS_TOKEN)

    @patch('facegraph.graph.session')
    def test_post_without_token(self, mock_session):
        mock_session.post.return_value.content = '{}'
        graph = Graph(app_secret=TEST_APP_SECRET)
        graph.me.post(test_param='data needed to force POST request')
        mock_session.post.assert_called_once_with(
            'https://graph.facebook.com/me', data='test_param=data+needed+to+force+POST+request')


class GraphAppsecretProofInjectionTests(TestCase):

    def setUp(self):
        super(GraphAppsecretProofInjectionTests, self).setUp()
        self.graph = Graph(app_secret=TEST_APP_SECRET, access_token=TEST_ACCESS_TOKEN)

    @patch('facegraph.graph.session')
    def test_get(self, mock_session):
        mock_session.get.return_value.content = '{}'
        self.graph.me.call_fb()
        mock_session.get.assert_called_once_with(
            'https://graph.facebook.com/me?access_token=%s&appsecret_proof=%s' % (
                TEST_ACCESS_TOKEN, EXPECTED_APPSECRET_PROOF
            )
        )

    @patch('facegraph.graph.session')
    def test_post(self, mock_session):
        mock_session.post.return_value.content = '{}'
        self.graph.me.post()
        mock_session.post.assert_called_once_with(
            'https://graph.facebook.com/me',
            data='access_token=%s&appsecret_proof=%s' % (
                TEST_ACCESS_TOKEN, EXPECTED_APPSECRET_PROOF
            )
        )


class ApiAppsecretProofNoInjectionTests(TestCase):

    def setUp(self):
        super(ApiAppsecretProofNoInjectionTests, self).setUp()
        self.mock_urllib = Mock()
        self.mock_urllib.urlopen.return_value.read.return_value = '{}'

    def test_query_without_secret_and_token(self):
        api = Api(urllib2=self.mock_urllib)
        api.fql.query(query=TEST_FQL)
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/fql?q=%s' % TEST_FQL, timeout=api.timeout)

    def test_query_without_secret(self):
        api = Api(access_token=TEST_ACCESS_TOKEN, urllib2=self.mock_urllib)
        api.fql.query(query=TEST_FQL)
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/fql?access_token=%s&q=%s' % (TEST_ACCESS_TOKEN, TEST_FQL),
            timeout=api.timeout)

    def test_query_without_token(self):
        api = Api(app_secret=TEST_APP_SECRET, urllib2=self.mock_urllib)
        api.fql.query(query=TEST_FQL)
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/fql?q=%s' % TEST_FQL, timeout=api.timeout)

    def test_verify_token_without_secret(self):
        api = Api(access_token=TEST_ACCESS_TOKEN, urllib2=self.mock_urllib)
        api.verify_token()
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/me?access_token=%s' % TEST_ACCESS_TOKEN,
            timeout=api.timeout)

    def test_exists_without_secret(self):
        api = Api(access_token=TEST_ACCESS_TOKEN, urllib2=self.mock_urllib)
        api.exists('object_id')
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/object_id?access_token=%s' % TEST_ACCESS_TOKEN,
            timeout=api.timeout)


class ApiAppsecretProofInjectionTests(TestCase):

    def setUp(self):
        super(ApiAppsecretProofInjectionTests, self).setUp()
        self.mock_urllib = Mock()
        self.mock_urllib.urlopen.return_value.read.return_value = '{}'
        self.api = Api(
            access_token=TEST_ACCESS_TOKEN, app_secret=TEST_APP_SECRET, urllib2=self.mock_urllib)

    def test_query(self):
        self.api.fql.query(query=TEST_FQL)
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/fql?access_token=%s&q=%s&appsecret_proof=%s' % (
                TEST_ACCESS_TOKEN, TEST_FQL, EXPECTED_APPSECRET_PROOF),
            timeout=self.api.timeout)

    def test_verify_token(self):
        self.api.verify_token()
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/me?access_token=%s&appsecret_proof=%s' % (
                TEST_ACCESS_TOKEN, EXPECTED_APPSECRET_PROOF),
            timeout=self.api.timeout)

    def test_exists(self):
        self.api.exists('object_id')
        self.mock_urllib.urlopen.assert_called_once_with(
            'https://graph.facebook.com/object_id?access_token=%s&appsecret_proof=%s' % (
                TEST_ACCESS_TOKEN, EXPECTED_APPSECRET_PROOF),
            timeout=self.api.timeout)
