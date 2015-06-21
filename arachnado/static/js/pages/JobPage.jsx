/* Job page */

var React = require("react");
var Reflux = require("reflux");
var { Link } = require('react-router');
var { Panel, Table, Button, Glyphicon, ButtonToolbar } = require("react-bootstrap");

var JobStore = require("../stores/JobStore");
var { ProcessStatsTable } = require("../components/ProcessStats");
var { JobStats } = require("../components/JobStats");
var { JobListWidget, JobList } = require("../components/JobList");


var ShortJobInfo = React.createClass({
    render: function () {
        var job = this.props.job;
        var jobs = [job];
        return <JobListWidget jobs={jobs} link={false}/>;
    }
});

var JobInfo = React.createClass({
    render: function () {
        var job = this.props.job;
        var kvpairs = [
            ["Target", job.seed],
            ["Status", job.status],
            ["Job ID", job.id],
            ["Started at", job.stats.start_time],
        ];
        if (job.stats.finish_time){
            kvpairs.push(["Finished at", job.stats.finish_time]);
        }

        var rows = kvpairs.map(p => <tr key={p[0]}><td>{p[0]}</td><td>{p[1]}</td></tr>);
        return (
            <div>
                <Table>
                    <caption>General Job Information</caption>
                    <tbody>{rows}</tbody>
                </Table>
            </div>
        );
    }
});


var NoJobPage = React.createClass({
    render: function () {
        return (
            <div>
                <h2>Job is not found</h2>
                <p>This job is either not available or never existed.</p>
                <Link to="index">
                    <Glyphicon glyph="menu-left"/>&nbsp;
                    Back to Full Job List
                </Link>
            </div>
        );
    }
});


export var JobPage = React.createClass({
    mixins: [
        Reflux.connectFilter(JobStore.store, "job", function(jobs) {
            return jobs.filter(job => job.id == this.props.params.id)[0];
        })
    ],

    render: function () {
        var job = this.state.job;
        if (!job){
            return <NoJobPage/>;
        }

        var header = (
            <span>
                <Link to="index">
                    <Glyphicon glyph="menu-left"/>&nbsp;
                    Back to Full Job List
                </Link>
            </span>
        );

        return (
            <div>
                <div className="row">
                    <div className="col-lg-6">
                        <Panel>
                            {header}
                        </Panel>
                    </div>
                    <div className="col-lg-6">
                        <ShortJobInfo job={job}/>
                    </div>
                </div>
                <div className="row">
                    <div className="col-lg-6">
                        <Panel>
                            <JobInfo job={job}/>
                        </Panel>
                    </div>
                    <div className="col-lg-6">
                        <Panel collapsible defaultExpanded header="Scrapy Stats">
                            <JobStats job={job} />
                        </Panel>
                    </div>
                </div>
            </div>
        );
    }
});

