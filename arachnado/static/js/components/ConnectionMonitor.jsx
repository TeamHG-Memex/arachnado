/*
A widget which shows if a server is idle/crawling or if we're not connected.
*/

var React = require('react');
var Reflux = require('reflux');
var { Label } = require('react-bootstrap');
var ConnectionStatusStore = require("../stores/ConnectionStatusStore.js");


var ConnectionMonitorWidget = React.createClass({
    STATE_CLASSES: {
        'offline': 'danger',
        'online': 'info',
        'crawling': 'success'
    },

    render: function () {
        var cls = this.STATE_CLASSES[this.props.status] || "default";
        return <Label bsStyle={cls}>{this.props.status}</Label>;
    }
});


var ConnectionMonitor = React.createClass({
    mixins: [Reflux.connect(ConnectionStatusStore.store, "status")],
    render: function () {
        return <ConnectionMonitorWidget status={this.state.status}/>;
    }
});

export function install(elemId) {
    React.render(<ConnectionMonitor />, document.getElementById(elemId));
}
