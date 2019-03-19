from __future__ import division, print_function
import unittest
import json
import arrow
import httpretty
import pygray.graylog_api as api


class GraylogAPITestCase(unittest.TestCase):

    def setUp(self):
        self.api = api.GraylogAPI("dummyhost", 80, "dummy", password="dummy")

    def test_search_range(self):
        sr = api.SearchRange("10 minutes ago", arrow.now())
        self.assertEqual(600, sr.range_in_seconds())

        sr = api.SearchRange("10 minutes ago", relative=True)
        self.assertEqual(600, sr.range_in_seconds())

        sr = api.SearchRange("10 minutes ago")
        with self.assertRaises(Exception):
            sr.range_in_seconds()

        sr = api.SearchRange("10 minutes ago", "10 minutes ago")
        self.assertEqual(1, sr.range_in_seconds())

    @httpretty.activate
    def test_graylog_api_search(self):
        httpretty.register_uri(
            httpretty.POST, "http://dummyhost:80/api/system/sessions",
            body=self.generate_mock_auth(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/users/dummy",
            body=self.generate_mock_user(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/search/universal/absolute",
            body=self.generate_search_result(),
            content_type="application/json"
        )

        # More of some dummy tests now
        sr = api.SearchRange("10 minutes ago", arrow.now())
        q = api.SearchQuery(sr)
        result = self.api.search(q)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual("*", result.query)

        q = api.SearchQuery(sr, fields=["level", "module", "message", "timestamp"], sort="level", ascending=True)
        qq = q.copy_with_range(sr)
        result = self.api.search(qq)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual("*", result.query, )

        q = api.SearchQuery(sr, fields=["level", "module", "message", "timestamp"], sort="level", ascending=False)
        result = self.api.search(q)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual("*", result.query)

        result = self.api.search(q, fetch_all=True)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual("*", result.query)

    @httpretty.activate
    def test_too_many_results(self):
        httpretty.register_uri(
            httpretty.POST, "http://dummyhost:80/api/system/sessions",
            body=self.generate_mock_auth(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/users/dummy",
            body=self.generate_mock_user(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/search/universal/absolute",
            body=self.generate_search_result(1000000),
            content_type="application/json"
        )

        sr = api.SearchRange("10 minutes ago", arrow.now())
        q = api.SearchQuery(sr)

        with self.assertRaises(RuntimeError):
            self.api.search(q, fetch_all=True)

    @httpretty.activate
    def test_userinfo(self):
        httpretty.register_uri(
            httpretty.POST, "http://dummyhost:80/api/system/sessions",
            body=self.generate_mock_auth(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/users/dummy",
            body=self.generate_mock_user(),
            content_type="application/json"
        )

        result = self.api.user_info()
        self.assertEqual(json.loads(self.generate_mock_user()), result)

    @httpretty.activate
    def test_streams(self):
        httpretty.register_uri(
            httpretty.POST, "http://dummyhost:80/api/system/sessions",
            body=self.generate_mock_auth(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/users/dummy",
            body=self.generate_mock_user(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/streams/enabled",
            body='[{"somestream" : "a" }]',
            content_type="application/json"
        )

        result = self.api.streams()
        self.assertEqual([{"somestream": "a"}], result)

    @httpretty.activate
    def test_saved_searches(self):
        httpretty.register_uri(
            httpretty.POST, "http://dummyhost:80/api/system/sessions",
            body=self.generate_mock_auth(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/users/dummy",
            body=self.generate_mock_user(),
            content_type="application/json"
        )
        httpretty.register_uri(
            httpretty.GET, "http://dummyhost:80/api/search/saved",
            body='{"searches" : [{"query": {"query": "level:INFO", "fields":"timestamp,message"}}]}',
            content_type="application/json"
        )

        saved_searches = self.api.get_saved_queries()
        self.assertEqual("level:INFO", saved_searches['searches'][0]['query']['query'])
        self.assertEqual("timestamp,message", saved_searches['searches'][0]['query']['fields'])

    def generate_mock_auth(self):
        return """{
          "session_id": "12345", "valid_until": "1234"
        }"""
        
    def generate_search_result(self, total_results=1000):
        result = """{{
          "query": "*",
          "built_query": "{{\\"from\\":0,\\"size\\":150,\\"query\\":{{\\"match_all\\":{{}},\\"post_filter\\":{{\\"range\\":{{\\"timestamp\\":{{\\"from\\":\\"2015-04-20 10:33:01.000\\",\\"to\\":\\"2015-04-20 10:43:01.795\\",\\"include_lower\\":true,\\"include_upper\\":true}}}},\\"sort\\":[{{\\"timestamp\\":{{\\"order\\":\\"desc\\"}}]}}",
          "used_indices": [
            {{
              "index": "graylog2_20",
              "calculation_took_ms": 3,
              "calculated_at": "2015-04-18T20:00:10.000Z",
              "starts": "2015-04-18T20:00:10.000Z"
            }}
          ],
          "messages": [
            {{
              "message": {{
                "level": 7,
                "module": "Database",
                "streams": [
                  "1111111"
                ],
                "source": "host1",
                "message": "Some message",
                "gl2_source_input": "1111111",
                "version": "1.1",
                "full_message": "Some extended message",
                "gl2_source_node": "c03b2ce1-8246-408b-9ca6-32309640d252",
                "_id": "0bc08503-e74a-11e4-a01b-52540021a4c5",
                "timestamp": "2015-04-20T10:43:01.793Z"
              }},
              "index": "graylog2_20"
            }}
          ],
          "fields": [
            "line",
            "source",
            "file",
            "text",
            "tag",
            "level",
            "module",
            "message",
            "version",
            "name",
            "facility"
          ],
          "time": 1,
          "total_results": {total_results},
          "from": "2015-04-20T10:33:01.000Z",
          "to": "2015-04-20T10:43:01.795Z"
        }}
        """
        return result.format(total_results=total_results)

    def generate_mock_user(self):
        return """{  "timezone": "America/Sao_Paulo" }"""




