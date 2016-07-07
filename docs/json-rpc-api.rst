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


.. _JSON-RPC: http://www.jsonrpc.org/specification
