var { FancyWebSocket } = require("./utils/FancyWebSocket");
var ConnectionMonitor = require("./components/ConnectionMonitor.jsx");

$(window).ready(function() {
    var socket = FancyWebSocket.forEndpoint(window.WS_SERVER_ADDRESS);
    ConnectionMonitor.install(socket, "arachnado-connection-monitor");
});
