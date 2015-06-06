var { FancyWebSocket } = require("./FancyWebSocket");
var ConnectionMonitor = require("./ConnectionMonitor.jsx");

$(window).ready(function() {
    var loc = document.location;
    var serverUrl = "ws://" + loc.hostname + ":" + loc.port + "/ws";
    window.socket = new FancyWebSocket(serverUrl);

    ConnectionMonitor.install("connection-monitor");
});
