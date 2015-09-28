export function jsonAjax(url, data, type) {
    if(typeof(type) === 'undefined') {
        type = 'post';
    }
    return $.ajax(url, {
        type: type,
        contentType: 'application/json',
        data: JSON.stringify(data)
    });
}