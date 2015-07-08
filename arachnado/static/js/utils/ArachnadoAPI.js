/* Wrapper for Arachnado HTTP API */

function jsonPost(url, data) {
    return $.ajax(url, {
        type: 'post',
        contentType: 'application/json',
        data: JSON.stringify(data)
    });
}

export function startCrawl(domain, options){
    var startCrawlUrl = window.START_CRAWL_URL;  // set in base.html
    var data = {
        domain: domain,
        options: options
    };
    return jsonPost(startCrawlUrl, data);
}

export function stopCrawl(jobId){
    return jsonPost(window.STOP_CRAWL_URL, {job_id: jobId});
}

export function pauseCrawl(jobId){
    return jsonPost(window.PAUSE_CRAWL_URL, {job_id: jobId});
}

export function resumeCrawl(jobId){
    return jsonPost(window.RESUME_CRAWL_URL, {job_id: jobId});
}

export function login(jobId, username, password){
    return jsonPost(window.LOGIN_URL, {
        job_id: jobId,
        username: username,
        password: password
    });
}