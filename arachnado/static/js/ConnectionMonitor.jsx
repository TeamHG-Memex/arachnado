/*
A widget which shows if a server is idle/crawling or if we're not connected.
*/

var React = require('react');
var { Label } = require('react-bootstrap');

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
    getInitialState: function() {
        return {status: 'offline'};
    },

    componentWillMount: function () {
        window.socket.on("open", (function () {
            this.setState({status: 'online'});
        }).bind(this));

        window.socket.on("close", (function () {
            this.setState({status: 'offline'});
        }).bind(this));
    },

    render: function () {
        return <ConnectionMonitorWidget status={this.state.status}/>;
    }
});

export function install(id) {
    React.render(<ConnectionMonitor/>, document.getElementById(id));
}
