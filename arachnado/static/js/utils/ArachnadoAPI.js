/* Wrapper for Arachnado HTTP API */

var {jsonAjax} = require("./AjaxUtils");


export function startCrawl(domain, options){
    var startCrawlUrl = window.START_CRAWL_URL;  // set in base.html
    var data = {
        domain: domain,
        options: options
    };
    return jsonAjax(startCrawlUrl, data);
}

export function stopCrawl(jobId){
    return jsonAjax(window.STOP_CRAWL_URL, {job_id: jobId});
}

export function pauseCrawl(jobId){
    return jsonAjax(window.PAUSE_CRAWL_URL, {job_id: jobId});
}

export function resumeCrawl(jobId){
    return jsonAjax(window.RESUME_CRAWL_URL, {job_id: jobId});
}
