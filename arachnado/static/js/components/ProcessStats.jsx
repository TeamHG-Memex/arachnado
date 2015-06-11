/* A widget for monitoring CPU and RAM usage of a process */

var React = require("react");
var Reflux = require("reflux");
var ProcessStatsStore = require("../stores/ProcessStatsStore");
var filesize = require("filesize");

export var FixedProcessStats = React.createClass({
    mixins: [Reflux.connect(ProcessStatsStore.store, "stats")],
    render: function () {
        var {cpu_percent, ram_percent} = this.state.stats;
        return (
            <pre>
            CPU: {(cpu_percent || 0).toFixed(1)}%<br/>
            RAM: {(ram_percent || 0).toFixed(1)}%
            </pre>
        );
    }
});

export var HeaderProcessStats = React.createClass({
    mixins: [Reflux.connect(ProcessStatsStore.store, "stats")],
    render: function () {
        var {cpu_percent, ram_percent} = this.state.stats;
        return <p className="navbar-text">
            CPU: {(cpu_percent || 0).toFixed(1)}% &nbsp;
            RAM: {(ram_percent || 0).toFixed(1)}%
        </p>;
    }
});


export function install(elemId) {
    React.render(<HeaderProcessStats />, document.getElementById(elemId));
}
