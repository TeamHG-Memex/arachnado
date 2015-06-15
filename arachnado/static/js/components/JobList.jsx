/* A list of active crawl jobs */

var React = require("react");
var Reflux = require("reflux");
var filesize = require("filesize");

var { Table } = require("react-bootstrap");
var JobListStore = require("../stores/JobListStore");
require("babel-core/polyfill");


var STATUS_CLASSES = {
    'crawling': 'success',
    'done': ''
};

var SIMPLER_STATUSES = [
    [/closespider/, "closed"],
];

function simplifiedStatus(status) {
    for (var i=0; i< SIMPLER_STATUSES.length; i++) {
        var [re, simple] = SIMPLER_STATUSES[i];
        if (re.test(status)){
            return simple;
        }
    }
    return status;
}


var NoJobs = React.createClass({
    render: function () {
        return (<div>
            <p>No jobs to show.</p>
            <p>
                Start a crawling job either by using "Crawl" button
                or by using Arachnado HTTP API.
            </p>
        </div>);
    }
});


var JobRow = React.createClass({
    render: function () {
        var job = this.props.job;
        var status = simplifiedStatus(job.status);
        var cls = STATUS_CLASSES[status] || "";
        var stats = job.stats || {};
        var downloaded = stats['downloader/response_bytes'] || 0;
        var todo = (stats['scheduler/enqueued'] || 0) - (stats['scheduler/dequeued'] || 0);
        return (
            <tr className={cls}>
                <th scope="row">{job.id}</th>
                <td>{job.seed}</td>
                <td>{status}</td>
                <td>{stats['item_scraped_count'] || 0}</td>
                <td>{todo}</td>
                <td>{filesize(downloaded)}</td>
            </tr>
        );
    }
});


var JobListWidget = React.createClass({
    render: function () {
        var rows = this.props.jobs.map(job => {return <JobRow job={job} key={job.id}/>});

        return <Table fill>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Seed URL</th>
                    <th>Status</th>
                    <th>Items</th>
                    <th>Todo</th>
                    <th>Data</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </Table>;
    }
});


export var JobList = React.createClass({
    mixins: [Reflux.connect(JobListStore.store, "jobs")],
    render: function () {
        if (!this.state.jobs.length) {
            return <NoJobs/>;
        }
        return <JobListWidget jobs={this.state.jobs}/>;
    }
});
