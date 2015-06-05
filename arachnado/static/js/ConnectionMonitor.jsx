/*
A widget which shows if a server is idle/crawling or if we're not connected.
*/

var ConnectionMonitorWidget = React.createClass({
    STATE_CLASSES: {
        'offline': 'danger',
        'online': 'info',
        'crawling': 'success'
    },

    render: function () {
        var className = "label label-" + this.STATE_CLASSES[this.props.status] || "default";
        return <span className={className}>{this.props.status}</span>;
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


React.render(<ConnectionMonitor/>, document.getElementById('connection-monitor'));
