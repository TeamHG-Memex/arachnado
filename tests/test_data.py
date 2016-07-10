# -*- coding: utf-8 -*-
import tornado
import json
from tornado import web, websocket
import tornado.testing
from tornado.ioloop import TimeoutError

import tests.utils as u


class TestDataAPI(tornado.testing.AsyncHTTPTestCase):
    pages_uri = r"/ws-pages-data"
    jobs_uri = r"/ws-jobs-data"

    @classmethod
    def setUpClass(cls):
        u.init_db()

    @classmethod
    def tearDownClass(cls):
        u.clear_db()

    def get_app(self):
        return u.get_app(self.pages_uri, self.jobs_uri)

    @tornado.testing.gen_test
    def test_jobs_no_filter(self):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_jobs_0",
                'jsonrpc': '2.0',
                'method': 'subscribe_to_jobs',
                'params': {
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.jobs_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("id", -1)
        self.assertNotEqual(subs_id, -1)
        self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_jobs_filter_include(self):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_jobs_1",
                'jsonrpc': '2.0',
                'method': 'subscribe_to_jobs',
                'params': {
                    "include":["127.0.0.1"],
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.jobs_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("id", -1)
        self.assertNotEqual(subs_id, -1)
        cnt = 0
        while cnt < 1:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.assertTrue(False)
                break
            else:
                self.assertTrue('stats' in json_response["data"])
                self.assertTrue(isinstance(json_response["data"]["stats"], dict))
            cnt += 1
        self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_pages_no_filter(self):
        pages_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_pages_0",
                'jsonrpc': '2.0',
                'method': 'subscribe_to_pages',
                'params': {
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("single_subscription_id", -1)
        self.assertNotEqual(subs_id, -1)
        cnt = 0
        while cnt < 1:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.assertTrue(False)
                break
            else:
                self.assertTrue('url' in json_response["data"])
            cnt += 1
        self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_pages_filter_url_groups(self):
        url_value = 'http://example.com'
        pages_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_pages_0",
                'jsonrpc': '2.0',
                'method': 'subscribe_to_pages',
                'params': {'url_groups': {1: {url_value: None}}
                }
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("single_subscription_id", -1)
        self.assertNotEqual(subs_id, -1)
        cnt = 0
        while cnt < 1:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.assertTrue(False)
                break
            else:
                self.assertTrue('url' in json_response["data"])
                self.assertTrue(url_value in json_response["data"]["url"])
            cnt += 1
        self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_pages_filter_urls(self):
        url_value = 'http://example.com'
        pages_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_pages_0",
                'jsonrpc': '2.0',
                'method': 'subscribe_to_pages',
                'params': {'urls': {url_value: None}
                }
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("single_subscription_id", -1)
        self.assertNotEqual(subs_id, -1)
        cnt = 0
        while cnt < 1:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.assertTrue(False)
                break
            else:
                self.assertTrue('url' in json_response["data"])
                self.assertTrue(url_value in json_response["data"]["url"])
            cnt += 1
        self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_wrong_cancel(self):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        self.execute_cancel(ws_client, -1, False)

    def execute_cancel(self, ws_client, subscription_id, expected):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id': "test_cancel",
                'jsonrpc': '2.0',
                'method': 'cancel_subscription',
                'params': {
                    "subscription_id": subscription_id
                },
            },
        }
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        self.assertEqual(json_response.get("data", {}).get("result"), expected)
