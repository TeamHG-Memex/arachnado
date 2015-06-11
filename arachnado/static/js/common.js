var { FancyWebSocket } = require("./utils/FancyWebSocket");
var ConnectionMonitor = require("./components/ConnectionMonitor.jsx");
var ProcessStats = require("./components/ProcessStats.jsx");

$(window).ready(function() {
    var socket = FancyWebSocket.instance();
    ConnectionMonitor.install(socket, "arachnado-connection-monitor");
    ProcessStats.install("arachnado-process-stats");
});
