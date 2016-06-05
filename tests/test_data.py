# -*- coding: utf-8 -*-
import tornado
import json

import utils as u


class TestJobsAPI(tornado.testing.AsyncHTTPTestCase):
    ws_uri = r"/ws-data"

    def get_app(self):
        return u.get_app(self.ws_uri)

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


