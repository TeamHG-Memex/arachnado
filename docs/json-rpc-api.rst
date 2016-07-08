JSON RPC API
============

Arachnado provides JSON-RPC_ API for working with jobs and crawled items
(pages). The API works over WebSocket transport.

**FIXME**: JSON-RPC request objects are wrapped:
``{"event": "rpc:request", "data": <JSON-RPC request>}``.
Responses are also wrapped:
``{"event": "rpc:response", "data": <JSON-RPC response>}``.


JSON-RPC requests have the following format::

    {
        "jsonrpc": "2.0",

        # pass unique request id here; this id will be included in response
        "id": 362810,

        # command to execute
        "method": "<method name>",
        "params": {"name": "value"},
    }

JSON-RPC responses::

    {
        "jsonrpc": "2.0",

        # id of the request
        "id": 362810,

        # what command returns
        "result": ...
    }

Working with jobs
-----------------

JSON-RPC API allows to

* get information about scraping jobs;
* start new crawls;
* subscribe to job updates.

jobs.subscribe
    Get information about jobs and subscribe for new jobs.

    Parameters:

    * last_id - optional, ObjectID value of a last previously seen job.
      When passed, only new job data is returned.
    * query - optional, MongoDB query
    * fields - optional, ...


New API
=======

Working with jobs
-----------------

Open a websocket connection to ``/ws-jobs-data`` in order to use
jobs JSON-RPC API for scraping jobs.

subscribe_to_jobs
    Get information about jobs and subscribe for new jobs.
    Parameters:

    * include - an array of regexes which should match URLs to include;
    * exclude - an array of regexes; URLs matched by these regexes are excluded
      from the result;
    * update_delay - int, a minimum number of ms between websocket mesages
      (FIXME).

    Response contains subscription ID in ``['data']['result']['id']`` field::

        {'data': {'id': '<request id>',
                  'jsonrpc': '2.0',
                  'result': {'datatype': 'job_subscription_id', 'id': '0'}},
         'event': 'rpc:response'}

    Use this ID to cancel the subscription.

    After the subscription Arachnado will start to send information
    about new jobs. Messages look like this::

        {'data': {'_id': '574718bba7a4edb9b026f248',
                  'finished_at': '2016-05-26 16:03:17',
                  'id': '97ca610fa8c347dbafeca9fcd02213dd',
                  'options': {'args': {},
                              'crawl_id': '97ca610fa8c347dbafeca9fcd02213dd',
                              'domain': 'scrapy.org',
                              'settings': {}},
                  'spider': 'generic',
                  'started_at': '2016-05-26 16:03:16',
                  'stats': {...},
                  'status': 'finished'},
         'event': 'jobs.tailed'}


cancel_subscription
    Stop receiving updates about jobs. Parameters:

    * subscription_id


Working with pages (items)
--------------------------




.. _JSON-RPC: http://www.jsonrpc.org/specification
