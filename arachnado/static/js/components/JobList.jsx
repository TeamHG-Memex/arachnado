/* A list of active crawl jobs */

var React = require("react");
var Reflux = require("reflux");
var filesize = require("filesize");
var prettyMs = require('pretty-ms');
var { History, withRouter } = require('react-router');

var { Table, Glyphicon, Button } = require("react-bootstrap");
var JobStore = require("../stores/JobStore");
var { JobsMixin } = require("./RefluxMixins");
var ProcessStatsStore = require("../stores/ProcessStatsStore");


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

var GlyphA = React.createClass({
    render: function () {
        var txt = this.props.button ? " " + this.props.title : "";
        return (
            <a href='#' {...this.props}>
                <Glyphicon glyph={this.props.glyph} />{txt}
            </a>
        )
    },
});


export var JobStopButton = React.createClass({
    render: function () {
        return <GlyphA title="Stop" glyph="stop" onClick={this.onClick}
                       button={this.props.button} className={this.props.className} />;
    },

    onClick: function (ev) {
        ev.preventDefault();
        var id = this.props.job.id;
        if (confirm("Stop job #" + id + "?")){
            JobStore.Actions.stopCrawl(id);
        }
    }
});


export var JobPauseButton = React.createClass({
    render: function () {
        return <GlyphA title="Pause" glyph="pause" onClick={this.onClick}
                       button={this.props.button} className={this.props.className}  />;
    },

    onClick: function (ev) {
        ev.preventDefault();
        JobStore.Actions.pauseCrawl(this.props.job.id);
    }
});


export var JobResumeButton = React.createClass({
    render: function () {
        return <GlyphA title="Resume" glyph="play" onClick={this.onClick}
                       button={this.props.button} className={this.props.className}  />;
    },

    onClick: function (ev) {
        ev.preventDefault();
        JobStore.Actions.resumeCrawl(this.props.job.id);
    }
});


export function buttonsForStatus(status){
    var status = simplifiedStatus(status);
    if (status == "crawling") {
        return {pause: true, stop: true}
    }
    else if (status == "suspended") {
        return {resume: true, stop: true}
    }
    return {}
}

export var JobControlIcons = React.createClass({
    render: function () {
        var job = this.props.job;
        var active = buttonsForStatus(job.status);
        var props = {job: job};

        var items = [];
        if (active.pause) {
            items.push(<span key="pause"><JobPauseButton {...props} />&nbsp;&nbsp;</span>);
        }
        if (active.resume) {
            items.push(<span key="resume"><JobResumeButton {...props} />&nbsp;&nbsp;</span>);
        }
        if (active.stop) {
            items.push(<JobStopButton key="stop" {...props} />);
        }
        return <span>{items}</span>;
    }
});


export var JobControlButtons = React.createClass({
    render: function () {
        var job = this.props.job;
        var active = buttonsForStatus(job.status);
        var props = {button: true, job: job};

        var items = [];
        if (active.pause) {
            items.push(<span key="pause"><JobPauseButton className="btn" {...props} />&nbsp;&nbsp;</span>);
        }
        if (active.resume) {
            items.push(<span key="resume"><JobResumeButton className="btn" {...props} />&nbsp;&nbsp;</span>);
        }
        if (active.stop) {
            items.push(<JobStopButton key="stop" className="btn" {...props} />);
        }
        return <span>{items}</span>;
    }
});


/* Parse a date returned by Scrapy */
var _parseDate = function (dt) {
    var dt = dt.replace(" ", "T");
    return new Date(dt+"Z");
};

/* Return a string like 1202 @ 15/sec */
function _formatItemSpeed(info) {
    var count = info.stats['item_scraped_count'] || 0;
    var speed = Math.round(info.itemsSpeed * 60);
    return count + " @ " + speed + "/min";
}


/* Return a number of requests in a queue */
function getNumQueued(stats) {
    var initialSize = stats['scheduler/initial'] || 0;
    var enqueued = stats['scheduler/enqueued'] || 0;
    var dequeued = stats['scheduler/dequeued'] || 0;
    return initialSize + enqueued - dequeued;
}


function _getRowInfo(job, curTime){
    var stats = job.stats || {};
    var status = simplifiedStatus(job.status);
    var downloaded = stats['downloader/response_bytes'] || 0;
    var shortId = job.id.slice(0, 5) + "…";

    var duration = 0;
    if (stats['start_time']) {
        var start = _parseDate(stats['start_time']);
        if (stats['finish_time']){
            var end = _parseDate(stats['finish_time']);
        }
        else {
            var end = curTime || new Date();
        }
        duration = end.getTime() - start.getTime();
    }

    var durationSec = duration / 1000;
    var downloadSpeed = duration ? downloaded / (durationSec): 0;
    var itemsSpeed = duration ? (stats['item_scraped_count'] || 0) / durationSec : 0;

    return {
        id: job.job_id || job.id,
        status: status,
        rowClass: STATUS_CLASSES[status] || "",
        stats: stats,
        downloaded: downloaded,
        downloadSpeed: downloadSpeed,
        itemsSpeed: itemsSpeed,
        todo: getNumQueued(stats),
        shortId: shortId,
        duration: duration
    }
}


var JobRow = withRouter(React.createClass({
    render: function () {
        var job = this.props.job;
        var info = _getRowInfo(job, this.props.serverTime);
        var style = {cursor: "pointer"};
        var cb = () => {
            this.props.router.push(`/job/${job.id}`);
        };

        var columns = [
            <td key='col-buttons'><JobControlIcons job={job}/></td>,
            <th key='col-id' scope="row" style={style} onClick={cb}>{info.shortId}</th>
        ];

        var data = [
            this.formatSeed(),
            info.status,
            _formatItemSpeed(info),
            filesize(info.downloaded),
            prettyMs(info.duration),
        ];

        columns = columns.concat(
            data.map((v,i) => <td style={style} onClick={cb} key={i}>{v}</td>)
        );

        return <tr className={info.rowClass}>{columns}</tr>;
    },
    formatSeed: function() {
        var job = this.props.job;
        if (job.seed.startsWith('spider://')) {
            var url = "";
            if (job.args.start_urls != undefined){
                url = job.args.start_urls[0];
            }
            var engine = job.seed.substring('spider://'.length);
            return `${url} (${engine})`;
        }
        return job.seed;
    },
}));


var JobRowVerbose = React.createClass({
    render: function () {
        var job = this.props.job;
        var info = _getRowInfo(job, this.props.serverTime);
        var columns = [
            <th key='col-id' scope="row">{job.id}</th>
        ];
        var data = [
            job.seed,
            info.stats['start_time'],
            info.status,
            _formatItemSpeed(info),
            info.todo,
            filesize(info.downloaded),
            filesize(info.downloadSpeed, {round: 1}) + "/s",
            prettyMs(info.duration),
        ];

        columns = columns.concat(data.map((v,i) => <td key={i}>{v}</td>));
        return <tr className={info.rowClass}>{columns}</tr>;
    }
});


export var JobListWidget = React.createClass({
    mixins: [
        Reflux.connect(ProcessStatsStore.store, "stats"),
    ],

    render: function () {
        var stats = this.state.stats;
        var rows = this.props.jobs.map(job => {
            return <JobRow job={job} key={job.id} serverTime={stats.serverTime} />;
        });
        return <Table fill hover={this.props.link}>
            <thead>
                <tr>
                    <th key='col-buttons'></th>
                    <th key='col-id'>ID</th>
                    <th key='col-seed'>Seed URL</th>
                    <th key='col-status'>Status</th>
                    <th key='col-items'>Items</th>
                    <th key='col-data' className="col-md-2">Data</th>
                    <th key='col-runtime' className="col-md-2">Duration</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </Table>;
    }
});


export var JobListWidgetVerbose = React.createClass({
    mixins: [
        Reflux.connect(ProcessStatsStore.store, "stats"),
    ],
    render: function () {
        var stats = this.state.stats;
        var rows = this.props.jobs.map(job => {
            return <JobRowVerbose job={job} key={job.id} serverTime={stats.serverTime} />;
        });
        return <Table fill>
            <thead>
                <tr>
                    <th key='col-id'>ID</th>
                    <th key='col-seed'>Seed URL</th>
                    <th key='col-started'>Started At</th>
                    <th key='col-status'>Status</th>
                    <th key='col-items'>Items</th>
                    <th key='col-queue'>Todo</th>
                    <th key='col-data' className="col-md-1">Data</th>
                    <th key='col-speed' className="col-md-1">↓ Speed</th>
                    <th key='col-runtime'>Duration</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
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
        return <JobListWidget jobs={jobs} />;
    }
});
