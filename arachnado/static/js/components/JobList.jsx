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


var JobStopButton = React.createClass({
    render: function () {
        return (
            <a href='#' title="Stop" onClick={this.onClick.bind(this)}>
                <Glyphicon glyph="stop" />
            </a>
        )
    },

    onClick: function (ev) {
        ev.preventDefault();
        var id = this.props.job.id;
        if (confirm("Stop job #" + id + "?")){
            JobStore.Actions.stopCrawl(id);
        }
    }
});


var JobPauseButton = React.createClass({
    render: function () {
        return (
            <a href='#' title="Pause" onClick={this.onClick.bind(this)}>
                <Glyphicon glyph="pause" />
            </a>
        )
    },

    onClick: function (ev) {
        ev.preventDefault();
        JobStore.Actions.pauseCrawl(this.props.job.id);
    }
});


var JobResumeButton = React.createClass({
    render: function () {
        return (
            <a href='#' title="Resume" onClick={this.onClick.bind(this)}>
                <Glyphicon glyph="play" />
            </a>
        )
    },

    onClick: function (ev) {
        ev.preventDefault();
        JobStore.Actions.resumeCrawl(this.props.job.id);
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

        var icons = "";
        if (status == "crawling") {
            icons = (
                <span>
                    {<JobPauseButton job={job}/>}&nbsp;&nbsp;
                    {<JobStopButton job={job}/>}
                </span>
            );
        }
        else if (status == "suspended") {
            icons = (
                <span>
                    {<JobResumeButton job={job}/>}&nbsp;&nbsp;
                    {<JobStopButton job={job}/>}
                </span>
            );
        }

        /*
        else if (status == "finished" || status == "closed" || status == "shutdown") {
            icon = <a href='#' title="Remove job from list"
                      onClick={this.onRemoveFromListClicked.bind(null, job.id)}>
                <Glyphicon glyph="trash"/>
            </a>;
        }
        */

        if (this.props.link){
            var style = {cursor: "pointer"};
            var cb = () => { this.transitionTo("job", {id: job.id}) };
        }
        else {
            var style = {};
            var cb = () => {};
        }

        var shortId = job.job_id.slice(-5);
        return (
            <tr className={cls}>
                <td>{icons}</td>
                <th scope="row" style={style} onClick={cb}>{job.id}: {shortId}</th>
                <td style={style} onClick={cb}>{job.seed}</td>
                <td style={style} onClick={cb}>{status}</td>
                <td style={style} onClick={cb}>{stats['item_scraped_count'] || 0}</td>
                <td style={style} onClick={cb}>{todo}</td>
                <td style={style} onClick={cb}>{filesize(downloaded)}</td>
            </tr>
        );
    }
});


export var JobListWidget = React.createClass({
    render: function () {
        var rows = this.props.jobs.map(job => {
            return <JobRow job={job} key={job.id} link={this.props.link} />;
        });

        return <Table fill hover={this.props.link}>
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
        var jobs = this.state.jobs;
        if (!jobs.length) {
            return <NoJobs/>;
        }
        return <JobListWidget jobs={jobs} link={true}/>;
    }
});
