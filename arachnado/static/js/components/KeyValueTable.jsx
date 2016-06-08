/* A widget for displaying key-value tables */
var React = require("react");
var { Table } = require("react-bootstrap");

export var KeyValueTable = React.createClass({
    render: function () {
        if (this.props.noheader){
            var header = <thead></thead>;
        }
        else {
            var header = <thead><tr><th>Name</th><th className="col-md-3">Value</th></tr></thead>;
        }

        return <Table condensed style={{tableLayout: 'fixed'}}>
            {header}
            <tbody>{this.props.children}</tbody>
        </Table>;
    }
});
