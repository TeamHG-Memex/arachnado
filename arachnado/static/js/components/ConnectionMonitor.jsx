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
        this.props.socket.on("open", () => {
            this.setState({status: 'online'});
        });

        this.props.socket.on("close", () => {
            this.setState({status: 'offline'});
        });
    },

    render: function () {
        return <ConnectionMonitorWidget status={this.state.status}/>;
    }
});

export function install(socket, elemId) {
    var elem = document.getElementById(elemId);
    React.render(<ConnectionMonitor socket={socket}/>, elem);
}
