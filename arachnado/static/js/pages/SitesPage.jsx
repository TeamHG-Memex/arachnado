
var React = require("react");
var Reflux = require("reflux");
var { Link } = require('react-router');
var { Panel, Table, Button, Glyphicon, ButtonToolbar } = require("react-bootstrap");

var JobStore = require("../stores/JobStore");

var SiteTable = React.createClass({
    render: function() {
        var rows = this.props.sites.map((site, index) =>
            <SiteRow url={site.url}/>
        );
        console.log(rows);
        return (<Table striped bordered condensed hover>
            <tr>
                <td>URL</td>
                <td>Title</td>
                <td>Status</td>
                <td>Last crawled</td>
                <td>Notes</td>
                <td></td>
            </tr>
            {rows}
        </Table>);
    }
});

var SiteRow = React.createClass({
    render: function() {
        return (<tr>
            <td>{this.props.url}</td>
            <td>{this.props.title}</td>
            <td>{this.props.status}</td>
            <td>{this.props.lastCrawled}</td>
            <td>{this.props.notes}</td>
            <td>
                <Glyphicon glyph="remove"/>
                <Glyphicon glyph="play"/>
            </td>
        </tr>);
    }
})


export var SitesPage = React.createClass({
    render: function() {
        var data = [{url: 'http://dupa.pl'}];
        return <SiteTable sites={data}/>
    }
});


export var SitePage = React.createClass({
    render: function() {

    }
})