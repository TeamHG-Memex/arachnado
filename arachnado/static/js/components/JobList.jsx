/* A list of active crawl jobs */

var React = require("react");
var Reflux = require("reflux");
var filesize = require("filesize");
var { Link, Navigation } = require('react-router');

var { Table, Glyphicon, Button } = require("react-bootstrap");
var JobStore = require("../stores/JobStore");
var { JobsMixin } = require("./RefluxMixins");

require("babel-core/polyfill");


var STATUS_CLASSES = {
    'crawling': 'success',
    'stopping': 'info',
    'suspended': 'warning',
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
    mixins: [Navigation],
    render: function () {
        var job = this.props.job;
        var status = simplifiedStatus(job.status);
        var cls = STATUS_CLASSES[status] || "";
        var stats = job.stats || {};
        var downloaded = stats['downloader/response_bytes'] || 0;
        var todo = (stats['scheduler/enqueued'] || 0) - (stats['scheduler/dequeued'] || 0);

        var stopButton = (
            <a href='#' title="Stop" onClick={this.onStopClicked.bind(null, job.id)}>
                <Glyphicon glyph="stop" />
            </a>
        );

        var pauseButton = (
            <a href='#' title="Pause" onClick={this.onPauseClicked.bind(null, job.id)}>
                <Glyphicon glyph="pause" />
            </a>
        );

        var resumeButton = (
            <a href='#' title="Resume" onClick={this.onResumeClicked.bind(null, job.id)}>
                <Glyphicon glyph="play" />
            </a>
        );

        var icons = "";
        if (status == "crawling") {
            icons = (<span>{pauseButton}&nbsp;&nbsp;{stopButton}</span>);
        }
        else if (status == "suspended") {
            icons = (<span>{resumeButton}&nbsp;&nbsp;{stopButton}</span>);
        }

        /*
        else if (status == "finished" || status == "closed" || status == "shutdown") {
            icon = <a href='#' title="Remove job from list"
                      onClick={this.onRemoveFromListClicked.bind(null, job.id)}>
                <Glyphicon glyph="trash"/>
            </a>;
        }
        */

        var style = {cursor: "pointer"};
        var cb = () => { this.transitionTo("job", {id: job.id}) };

        return (
            <tr className={cls}>
                <td>{icons}</td>
                <th scope="row">{job.id}</th>
                <td style={style} onClick={cb}>{job.seed}</td>
                <td style={style} onClick={cb}>{status}</td>
                <td style={style} onClick={cb}>{stats['item_scraped_count'] || 0}</td>
                <td style={style} onClick={cb}>{todo}</td>
                <td style={style} onClick={cb}>{filesize(downloaded)}</td>
            </tr>
        );
    },

    onStopClicked: function (jobId, ev) {
        ev.preventDefault();
        if (confirm("Stop job #" + jobId + "?")){
            JobStore.Actions.stopCrawl(jobId);
        }
    },

    onPauseClicked: function (jobId, ev) {
        ev.preventDefault();
        JobStore.Actions.pauseCrawl(jobId);
    },

    onResumeClicked: function (jobId, ev) {
        ev.preventDefault();
        JobStore.Actions.resumeCrawl(jobId);
    }

    /*
    onRemoveFromListClicked: function (jobId, ev) {
        ev.preventDefault();
        console.log("onRemoveFromListClicked", jobId);
    }
    */

});


var JobListWidget = React.createClass({
    render: function () {
        var rows = this.props.jobs.map(job => {return <JobRow job={job} key={job.id}/>});

        return <Table fill hover>
            <thead>
                <tr>
                    <th></th>
                    <th>ID</th>
                    <th>Seed URL</th>
                    <th>Status</th>
                    <th>Items</th>
                    <th>Todo</th>
                    <th className="col-md-2">Data</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </Table>;
    }
});


export var JobList = React.createClass({
    mixins: [JobsMixin],
    render: function () {
        if (!this.state.jobs.length) {
            return <NoJobs/>;
        }
        return <JobListWidget jobs={this.state.jobs}/>;
    }
});
