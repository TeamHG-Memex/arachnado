/* Wrapper for Arachnado HTTP API */

export function startCrawl(domain, options){
    var startCrawlUrl = window.START_CRAWL_URL;  // set in base.html
    var data = {
        domain: domain,
        options: options
    };
    $.post(startCrawlUrl, data);
}
