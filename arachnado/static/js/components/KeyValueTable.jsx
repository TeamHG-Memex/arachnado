/* A widget for displaying key-value tables */
var React = require("react");
var { Table } = require("react-bootstrap");

export var KeyValueTable = React.createClass({
    render: function () {
        if (this.props.noheader){
            var header = <thead></thead>;
        }
        else {
            var header = <thead><th>Name</th><th>Value</th></thead>;
        }

        return <Table>
            {header}
            <tbody>{this.props.children}</tbody>
        </Table>;
    }
});
