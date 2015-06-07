var { FancyWebSocket } = require("./FancyWebSocket");
var ConnectionMonitor = require("./ConnectionMonitor.jsx");

$(window).ready(function() {
    var socket = FancyWebSocket.forEndpoint("ws");
    ConnectionMonitor.install(socket, "connection-monitor");
});
