# -*- coding: utf-8 -*-
import tornado
import json
from tornado import web, websocket

import tests.utils as u


class TestJobsAPI(tornado.testing.AsyncHTTPTestCase):
    ws_uri = r"/ws-data"

    def setUp(self):
        print("setUp:")
        tornado.ioloop.IOLoop.current().run_sync(u.init_db)
        super(TestJobsAPI, self).setUp()

    def get_app(self):
        return u.get_app(self.ws_uri)

    # @tornado.testing.gen_test
    # def test_fail(self):
    #     self.assertTrue(False)

    @tornado.testing.gen_test
    def test_jobs_no_filter(self):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id':0,
                'jsonrpc': '2.0',
                'method': 'subscribe_to_jobs',
                'params': {
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.ws_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        print(json_response)
        self.assertTrue("id" in json_response.get("data", {}))
        self.execute_cancel(ws_client, json_response.get("data", {}).get("id", -1), True)

    @tornado.testing.gen_test
    def test_jobs_filter_include(self):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id':0,
                'jsonrpc': '2.0',
                'method': 'subscribe_to_jobs',
                'params': {
                    "include":["127.0.0.1"],
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.ws_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        print(json_response)
        self.assertTrue("id" in json_response.get("data", {}))
        cnt = 0
        while cnt < 1:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.assertFail()
                break
            cnt += 1
        self.execute_cancel(ws_client, json_response.get("data", {}).get("id", -1), True)

    @tornado.testing.gen_test
    def test_pages_no_filter(self):
        pages_command = {
            'event': 'rpc:request',
            'data': {
                'id':0,
                'jsonrpc': '2.0',
                'method': 'subscribe_to_pages',
                'params': {
                },
            },
        }
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.ws_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        print(json_response)
        self.assertTrue("id" in json_response.get("data", {}))
        self.execute_cancel(ws_client, json_response.get("data", {}).get("id", -1), True)

    @tornado.testing.gen_test
    def test_wrong_cancel(self):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.ws_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        self.execute_cancel(ws_client, -1, False)

    def execute_cancel(self, ws_client, subscription_id, expected):
        jobs_command = {
            'event': 'rpc:request',
            'data': {
                'id':0,
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
        print(json_response)
        self.assertEqual(json_response.get("data", {}).get("result"), expected)
