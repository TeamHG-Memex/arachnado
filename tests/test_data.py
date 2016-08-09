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
        test_command = self.get_command("test_set_0",'set_max_message_size', {"max_size":10000})
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
        yield self.execute_jobs_command(jobs_command, wait_result=True)

    @tornado.testing.gen_test
    def test_jobs_filter_include(self):
        jobs_command = self.get_command("test_jobs_1",'subscribe_to_jobs', {"include":["127.0.0.1"],})
        yield self.execute_jobs_command(jobs_command, wait_result=True)

    @tornado.gen.coroutine
    def execute_jobs_command(self, jobs_command, wait_result=True):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.jobs_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(jobs_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("result").get("id", -1)
        self.assertNotEqual(subs_id, -1)
        if wait_result:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response is None:
                self.fail("incorrect response")
            else:
                self.assertTrue('stats' in json_response)
                self.assertTrue(isinstance(json_response["stats"], dict))
        yield self.execute_cancel(ws_client, subs_id, True)

    def test_jobs_filter_include_not_exists(self):
        @tornado.gen.coroutine
        def f():
            jobs_command = self.get_command("test_jobs_2",'subscribe_to_jobs', {"include":["notexists.com"],})
            yield self.execute_jobs_command(jobs_command, wait_result=True)
        self.assertRaises(TimeoutError, self.io_loop.run_sync, f, timeout=3)

    @tornado.testing.gen_test
    def test_pages_filter_url_groups(self):
        url_value = 'http://example.com'
        pages_command = self.get_command("test_pages_0",'subscribe_to_pages', {'url_groups': {1: {url_value: None}}})
        yield self.execute_pages_command(pages_command, wait_result=True, required_url=url_value)

    def test_pages_no_result(self):
        @tornado.gen.coroutine
        def f():
            url_value = 'http://mysite.com'
            pages_command = self.get_command("test_pages_3",'subscribe_to_pages', {'url_groups': {1: {url_value: None}}})
            yield self.execute_pages_command(pages_command,
                                             wait_result=True,
                                             required_url=url_value,
                                             max_count=0)
        self.assertRaises(TimeoutError, self.io_loop.run_sync, f, timeout=3)

    def test_pages_exact_count(self):
        @tornado.gen.coroutine
        def f():
            url_value = 'http://example.com'
            pages_command = self.get_command("test_pages_4",'subscribe_to_pages', {'url_groups': {1: {url_value: None}}})
            yield self.execute_pages_command(pages_command,
                                             wait_result=True,
                                             required_url=url_value,
                                             max_count=1)
        self.assertRaises(TimeoutError, self.io_loop.run_sync, f, timeout=3)

    @tornado.testing.gen_test
    def test_pages_no_filter(self):
        pages_command = self.get_command("test_pages_1",'subscribe_to_pages', {})
        yield self.execute_pages_command(pages_command, wait_result=True)

    @tornado.testing.gen_test
    def test_pages_filter_urls(self):
        url_value = 'http://example.com'
        pages_command = self.get_command("test_pages_2",'subscribe_to_pages', {'urls': {url_value: None}})
        yield self.execute_pages_command(pages_command, wait_result=True, required_url=url_value)

    def get_command(self, id, method, params):
        return {
                'id': id,
                'jsonrpc': '2.0',
                'method': method,
                'params': params
               }

    @tornado.gen.coroutine
    def execute_pages_command(self, pages_command, wait_result=False, required_url=None, max_count=None):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        ws_client.write_message(json.dumps(pages_command))
        response = yield ws_client.read_message()
        json_response = json.loads(response)
        subs_id = json_response.get("result").get("single_subscription_id", -1)
        if not subs_id:
            group_sub_ids = json_response.get("result").get("id", {})
            for group_id in group_sub_ids.keys():
                if group_sub_ids[group_id] != -1:
                    subs_id = group_sub_ids[group_id]
        self.assertNotEqual(subs_id, -1)
        if wait_result:
            if max_count is None:
                response = yield ws_client.read_message()
                json_response = json.loads(response)
                if json_response is None:
                    self.fail("incorrect response")
            else:
                cnt = 0
                while True:
                    response = yield ws_client.read_message()
                    json_response = json.loads(response)
                    if json_response is None:
                        self.fail("incorrect response")
                    cnt += 1
                    if cnt > max_count:
                        self.fail("max count of pages exceeded")
        yield self.execute_cancel(ws_client, subs_id, True)

    @tornado.testing.gen_test
    def test_wrong_cancel(self):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + self.pages_uri
        ws_client = yield tornado.websocket.websocket_connect(ws_url)
        yield self.execute_cancel(ws_client, -1, False)

    @tornado.gen.coroutine
    def execute_cancel(self, ws_client, subscription_id, expected):
        cmd_id = "test_cancel"
        cancel_command = self.get_command(cmd_id,'cancel_subscription', {"subscription_id": subscription_id})
        ws_client.write_message(json.dumps(cancel_command))
        while True:
            response = yield ws_client.read_message()
            json_response = json.loads(response)
            if json_response.get("id", None) == cmd_id:
                self.assertEqual(json_response.get("result"), expected)
                break
