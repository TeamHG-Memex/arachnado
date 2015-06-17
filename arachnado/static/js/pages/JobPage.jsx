/* Job page */

var React = require("react");
var { Link } = require('react-router');
var { Panel, Table, Button, Glyphicon, ButtonToolbar } = require("react-bootstrap");

var { ProcessStatsTable } = require("../components/ProcessStats");
var { JobStats } = require("../components/JobStats");
var { SingleJobMixin } = require("../components/RefluxMixins");


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
            <Table>
                <caption>General Job Information</caption>
                <tbody>{rows}</tbody>
            </Table>
        );
    }
});


export var JobPage = React.createClass({
    render: function () {
        var jobId = this.props.params.id;
        var header = (
            <span>
                <Link to="index">
                    <small>
                        <Glyphicon glyph="menu-left"/>&nbsp;
                        Back to Job List
                    </small>
                </Link>
                <span className="pull-right">Crawling Job #{jobId}</span>
            </span>
        );

        return (
            <div className="row">
                <div className="col-lg-6">
                    <Panel>
                        {header}
                    </Panel>
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
        );
    }
});

