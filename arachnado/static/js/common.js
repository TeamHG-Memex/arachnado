var { FancyWebSocket } = require("./utils/FancyWebSocket");
var ConnectionMonitor = require("./components/ConnectionMonitor.jsx");
var ProcessStats = require("./components/ProcessStats.jsx");

$(window).ready(function() {
    ConnectionMonitor.install("arachnado-connection-monitor");
    ProcessStats.installHeader("arachnado-process-stats");
});
