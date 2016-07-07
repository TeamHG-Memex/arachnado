HTTP API
========

Arachnado provides HTTP API for starting/stopping crawls.

To use HTTP API send a POST request with
``Content-Type: application/json`` header; parameters should be in
JSON-encoded POST body.

/crawler/start
--------------

Start a crawling job. Prameters::

    {
        "domain": "<URL to crawl>",
        "args": {<Scrapy spider arguments, optional>},
        "settings": {<Scrapy settings, optional>}
    }

If job is started successfuly, endpoint returns
``{"status": "ok", "job_id": "<job id>"}`` object with an ID of a started job.

In case of errors ``{"status": "error"}`` is returned.

/crawler/stop
-------------

Stop a job. Prameters::

    {"job_id": "<job id>"}

If job is stopped successfuly, endpoint returns
``{"status": "ok"}``, otherwise it returns ``{"status": "error"}``.


/crawler/pause
--------------

Pause a job. Prameters::

    {"job_id": "<job id>"}

If job is stopped successfuly, endpoint returns
``{"status": "ok"}``, otherwise it returns ``{"status": "error"}``.


/crawler/resume
---------------

Resume paused job. Prameters::

    {"job_id": "<job id>"}

If job is stopped successfuly, endpoint returns
``{"status": "ok"}``, otherwise it returns ``{"status": "error"}``.


/crawler/status
---------------

TODO
