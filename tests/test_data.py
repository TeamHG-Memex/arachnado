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
    def test_set_message_size(self):
        test_command = self.get_command("test_set_0",'set_max_message_size', {"max_size":100})
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.jobs_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(test_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        res = json_response.get("result", False)
        self.assertTrue(res)

    @tornado.testing.gen_test
    def test_jobs_no_filter(self):
        jobs_command = self.get_command("test_jobs_0",'subscribe_to_jobs', {})
        self.execute_jobs_command(jobs_command, wait_result=True)

    @tornado.testing.gen_test
    def test_jobs_filter_include(self):
        jobs_command = self.get_command("test_jobs_1",'subscribe_to_jobs', {"include":["127.0.0.1"],})
        self.execute_jobs_command(jobs_command, wait_result=True)

    def execute_jobs_command(self, jobs_command, wait_result=True):
        raise(TimeoutError())
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.jobs_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("result").get("id", -1)
        self.assertNotEqual(subs_id, -1)
        cnt = 0
        if wait_result:
            while cnt < 1:
                response = yield ws_client.read_message()
                json_response = json.loads(response)
                if json_response is None:
                    self.fail("incorrect response")
                    break
                else:
                    self.assertTrue('stats' in json_response)
                    self.assertTrue(isinstance(json_response["stats"], dict))
                cnt += 1
        self.execute_cancel(ws_client, subs_id, True)

    def test_jobs_filter_include_not_exists(self):
        @tornado.gen.coroutine
        def f():
            jobs_command = self.get_command("test_jobs_2",'subscribe_to_jobs', {"include":["notexists.com"],})
            self.execute_jobs_command(jobs_command, wait_result=True)
        self.assertRaises(TimeoutError, self.io_loop.run_sync, f, timeout=3)

    @tornado.testing.gen_test
    def test_pages_filter_url_groups(self):
        url_value = 'http://example2.com'
        pages_command = self.get_command("test_pages_0",'subscribe_to_pages', {'url_groups': {1: {url_value: None}}})
        self.execute_pages_command(pages_command, wait_result=True, required_url=url_value)

    @tornado.testing.gen_test
    def test_pages_no_filter(self):
        pages_command = self.get_command("test_pages_1",'subscribe_to_pages', {})
        self.execute_pages_command(pages_command, wait_result=True)

    @tornado.testing.gen_test
    def test_pages_filter_urls(self):
        url_value = 'http://example.com'
        pages_command = self.get_command("test_pages_2",'subscribe_to_pages', {'urls': {url_value: None}})
        self.execute_pages_command(pages_command, wait_result=True, required_url=url_value)

    def get_command(self, id, method, params):
        return {
                'id': id,
                'jsonrpc': '2.0',
                'method': method,
                'params': params
               }

    def execute_pages_command(self, pages_command, wait_result=False, required_url=None):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("data", {}).get("result").get("single_subscription_id", -1)
        self.assertNotEqual(subs_id, -1)
        if wait_result:
            while True:
                response = yield ws_client.read_message()
                print(response)
                json_response = json.loads(response)
                if json_response is None:
                    self.assertTrue(False)
                    break
                else:
                    self.assertTrue('url' in json_response["data"])
                    if required_url:
                        self.assertTrue(required_url in json_response["data"]["url"])
            self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_wrong_cancel(self):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        self.execute_cancel(ws_client, -1, False)

    def execute_cancel(self, ws_client, subscription_id, expected):
        jobs_command = {
            'id': "test_cancel",
            'jsonrpc': '2.0',
            'method': 'cancel_subscription',
            'params': {
                "subscription_id": subscription_id
            },
        }
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        self.assertEqual(json_response.get("data", {}).get("result"), expected)
