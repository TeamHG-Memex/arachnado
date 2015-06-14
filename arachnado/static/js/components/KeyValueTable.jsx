/* A widget for displaying key-value tables */
var React = require("react");
var { Table } = require("react-bootstrap");

export var KeyValueTable = React.createClass({
    render: function () {
        return <Table>
            <thead><th>Name</th><th>Value</th></thead>
            <tbody>{this.props.children}</tbody>
        </Table>;
    }
});
