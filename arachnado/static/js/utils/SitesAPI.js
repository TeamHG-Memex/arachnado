var {jsonAjax} = require("./AjaxUtils");


export function createSite(url){
    var data = {
        url: url,
    };
    return jsonAjax(window.SITES_URL, data);
};

export function deleteSite(siteId) {
    var data = {
        _id: siteId,
    }
    return jsonAjax(window.SITES_URL, data, 'delete');
};

export function updateSite(site) {
    return jsonAjax(window.SITES_URL, site, 'patch');
}