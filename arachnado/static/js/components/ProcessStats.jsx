/* A widget for monitoring CPU and RAM usage of a process */

var filesize = require("filesize");
var ms = require("ms");
var React = require("react");
var Reflux = require("reflux");
var { Table } = require("react-bootstrap");

var ProcessStatsStore = require("../stores/ProcessStatsStore");
var ConnectionStatusStore = require("../stores/ConnectionStatusStore");
var { KeyValueTable } = require("./KeyValueTable");


function formatTimeMs(timeMs){
    return ms(parseFloat((timeMs || 0).toFixed(3))*1000);
}

export var HeaderProcessStats = React.createClass({
    mixins: [
        Reflux.connect(ProcessStatsStore.store, "stats"),
        Reflux.connect(ConnectionStatusStore.store, "connectionStatus"),
    ],
    render: function () {
        if (this.state.connectionStatus == "offline"){
            return <span></span>;
        }
        var s = this.state.stats;
        var style = {marginTop: 15}; // for yeti theme
        return <div className="navbar-text" style={style}>
            {filesize(s.ram_rss || 0)}, CPU: {(s.cpu_percent || 0).toFixed(1)}%
        </div>;
    }
});


export var ProcessStatsTable = React.createClass({
    mixins: [Reflux.connect(ProcessStatsStore.store, "stats")],
    render: function () {
        var s = this.state.stats;
        var items = [
            ["CPU %", (s.cpu_percent || 0).toFixed(1)],
            ["utime", formatTimeMs(s.cpu_time_user)],
            ["stime", formatTimeMs(s.cpu_time_system)],
            ["RAM %", (s.ram_percent || 0).toFixed(2)],
            ["RSS", filesize(s.ram_rss || 0, {round: 1})],
            ["VMS", filesize(s.ram_vms || 0)],
            ["FDs", s.num_fds],
            ["threads", s.num_threads],
        ];
        var noheader = this.props.fill;
        var rows = items.map(kv => {return <tr key={kv[0]}><td>{kv[0]}</td><td>{kv[1]}</td></tr>});
        return <KeyValueTable noheader={noheader}>{rows}</KeyValueTable>;
    }
});


export function installHeader(elemId) {
    React.render(<HeaderProcessStats />, document.getElementById(elemId));
}
