/* Job page */

var React = require("react");
var { Link } = require('react-router');
var { Panel, Table, Button, Glyphicon, ButtonToolbar } = require("react-bootstrap");

var { ProcessStatsTable } = require("../components/ProcessStats");
var { JobStats } = require("../components/JobStats");
var { JobListWidget, JobList } = require("../components/JobList");
var { SingleJobMixin, JobsMixin } = require("../components/RefluxMixins");


var ShortJobInfo = React.createClass({
    mixins: [SingleJobMixin],
    render: function () {
        var job = this.state.job;
        if (!job){ return <p></p>; }
        var jobs = [job];
        return <JobListWidget jobs={jobs} link={false}/>;
    }
});

var JobInfo = React.createClass({
    mixins: [SingleJobMixin],
    render: function () {
        var job = this.state.job;
        if (!job){ return <p></p>; }
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


export var JobPage = React.createClass({
    render: function () {
        var jobId = this.props.params.id;
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
                        <ShortJobInfo id={jobId}/>
                    </div>
                </div>
                <div className="row">
                    <div className="col-lg-6">
                        <Panel>
                            <JobInfo id={jobId}/>
                        </Panel>
                    </div>
                    <div className="col-lg-6">
                        <Panel collapsible defaultExpanded header="Scrapy Stats">
                            <JobStats id={jobId} />
                        </Panel>
                    </div>
                </div>
            </div>
        );
    }
});

