import unittest
from mock import MagicMock, Mock, patch
from glogcli.input import CliInterface


class CliInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self.admin_user = {'permissions': ['*'], 'roles': ['Admin']}
        self.regular_user = {'permissions': ['dashboard'], 'roles': ['some_role']}
        self.streams = {'streams': [
            {'title': 'Main stream', 'id': '123'},
            {'title': 'Other stream', 'id': '456'}
        ]}
        self.saved_queries = {'searches': [
            {'query': {'query': '*', 'fields': 'timestamp,level,message'}, 'title': 'All'},
            {'query': {'query': 'level:DEBUG', 'fields': 'timestamp,message'}, 'title': 'Debug'}
        ]}

    def test_select_stream_given_stream_passed(self):
        graylog_api = self._mock_graylog_api_streams(user=self.admin_user)
        stream_filter = CliInterface.select_stream(graylog_api, '123456')
        self.assertEquals('streams:123456', stream_filter)

    def test_select_stream_with_default_stream_set(self):
        graylog_api = self._mock_graylog_api_streams(user=self.admin_user, default_stream='abc')
        stream_filter = CliInterface.select_stream(graylog_api, None)
        self.assertEquals('streams:abc', stream_filter)

    def test_select_stream_with_no_stream_set_and_admin_user(self):
        graylog_api = self._mock_graylog_api_streams(user=self.admin_user)
        stream_filter = CliInterface.select_stream(graylog_api, '*')
        self.assertEquals(None, stream_filter)

    def test_select_stream_with_regular_user(self):
        graylog_api = self._mock_graylog_api_streams(stream_list=self.streams, user=self.regular_user)
        self._mock_prompt_stream(1)
        stream_filter = CliInterface.select_stream(graylog_api, None)
        self.assertEquals('streams:456', stream_filter)

    def test_select_stream_with_admin_user_and_all_streams_options_chosen(self):
        graylog_api = self._mock_graylog_api_streams(stream_list=self.streams, user=self.admin_user)
        self._mock_prompt_stream(2)
        stream_filter = CliInterface.select_stream(graylog_api, None)
        self.assertEquals(None, stream_filter)

    def test_select_saved_query(self):
        graylog_api = self._mock_graylog_api_saved_query(self.saved_queries)
        self._mock_prompt_stream(0)
        query, fields = CliInterface.select_saved_query(graylog_api)
        self.assertEquals('*', query)
        self.assertEquals(['timestamp', 'level', 'message'], fields)

        self._mock_prompt_stream(1)
        query, fields = CliInterface.select_saved_query(graylog_api)
        self.assertEquals('level:DEBUG', query)
        self.assertEquals(['timestamp', 'message'], fields)

    def test_select_saved_query_no_queries_found_for_user(self):
        graylog_api = self._mock_graylog_api_saved_query({'searches': []})
        self._mock_prompt_stream(0)
        with self.assertRaises(SystemExit):
            CliInterface.select_saved_query(graylog_api)

    def _mock_graylog_api_streams(self, stream_list=None, default_stream=None, user=None):
        mock = MagicMock()
        mock.default_stream = default_stream
        mock.user = user
        mock.streams = Mock(return_value=stream_list)
        return mock

    def _mock_graylog_api_saved_query(self, saved_queries):
        mock = MagicMock()
        mock.get_saved_queries = Mock(return_value=saved_queries)
        return mock

    def _mock_prompt_stream(self, prompt_return):
        mock = patch('click.prompt').start()
        mock.return_value = prompt_return
