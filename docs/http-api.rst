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


/project/upload
---------------

Upload a Scrapy project archive. This endpoint accepts a multipart/form-data POST request
with the following fields:

* ``project_name``: Name for the project (alphanumeric, underscores, and hyphens only)
* ``project_file``: The project archive file (zip or tar.gz format)

The uploaded project should be a standard Scrapy project structure with:

* A ``scrapy.cfg`` file at the root
* A Python package containing spiders

Example using curl::

    curl -X POST -F "project_name=myproject" -F "project_file=@myproject.zip" \
        http://localhost:8888/project/upload

On success, returns::

    {
        "status": "ok",
        "project_name": "myproject",
        "spider_packages": ["myproject.spiders"]
    }

On error, returns::

    {"status": "error", "message": "<error description>"}

After uploading, spiders from the project can be used by specifying
``spider://<spider_name>`` as the domain when starting a crawl.


/project/list
-------------

List all uploaded projects. Requires no parameters.

Returns::

    {"projects": ["project1", "project2", ...]}
