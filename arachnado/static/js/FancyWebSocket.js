/*
WebSocket wrapper.
It allows multiple callbacks and forces a common message format.
*/

var EventEmitter = require("eventemitter3");

export class FancyWebSocket {

    constructor(url) {
        this._ee = new EventEmitter();
        this._conn = new WebSocket(url);
        this._conn.onmessage = (evt) => {
            var json = JSON.parse(evt.data);
            this._ee.emit(json.event, json.data);
        };
        this._conn.onclose = () => { this._ee.emit('close', null) };
        this._conn.onopen = () => { this._ee.emit('open', null) };
    }

    /* Listen to incoming messages */
    on(event, callback) { this._ee.on(event, callback) }
    off(event, callback) { this._ee.off(event, callback) }
    once(event, callback) { this._ee.once(event, callback) }

    /* Send data to the websocket */
    send(event, data) {
        var payload = JSON.stringify({event: event, data: data});
        this._conn.send(payload);
    }

    /* Return a new FancyWebSocket on the same domain/port as current URL */
    static forEndpoint(endpoint){
        var loc = document.location;
        var url = "ws://" + loc.hostname + ":" + loc.port + "/" + endpoint;
        return new FancyWebSocket(url);
    }
}
