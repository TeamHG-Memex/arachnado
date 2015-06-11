/* A widget for displaying crawl stats */
var React = require("react");
var Reflux = require("reflux");
var filesize = require("filesize");
var { Table } = require("react-bootstrap");

var JobListStore = require("../stores/JobListStore");


var SUM_KEYS = [
    'downloader/request_bytes',
    'downloader/request_count',
    'downloader/request_method_count/GET',
    'downloader/response_bytes',
    'downloader/response_count',
    'downloader/response_status_count/200',
    'downloader/response_status_count/301',
    'downloader/response_status_count/302',
    'dupefilter/filtered',
    'item_scraped_count',
    'log_count/DEBUG',
    'log_count/INFO',
    'log_count/WARNING',
    'log_count/ERROR',
    'response_received_count',
    'scheduler/dequeued',
    'scheduler/dequeued/memory',
    'scheduler/enqueued',
    'scheduler/enqueued/memory'
];


export var AggregateJobStats = React.createClass({
    mixins: [Reflux.connect(JobListStore.store, "jobs")],
    render: function () {
        var stats = this.getAggregateStats();
        var rows = Object.keys(stats).map(key => {
            var value = stats[key];
            if (/_bytes$/.test(key)){
                value = filesize(value);
            }
            return (
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
            );
        });
        return <Table condensed>
            <tbody>{rows}</tbody>
        </Table>;
    },

    getAggregateStats: function () {
        var stats = {};
        SUM_KEYS.forEach(key => {stats[key] = 0});

        this.state.jobs.forEach(job => {
            SUM_KEYS.forEach(key => {
                stats[key] += job.stats[key] || 0;
            });
        });
        return stats;
    }
});
