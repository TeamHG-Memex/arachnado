/* Job page */

var React = require("react");
var { Panel, Table } = require("react-bootstrap");
var { ProcessStatsTable } = require("../components/ProcessStats");
var { JobStats } = require("../components/JobStats");
var { SingleJobMixin } = require("../components/RefluxMixins");

var JobInfo = React.createClass({
    mixins: [SingleJobMixin],
    render: function () {
        var job = this.state.job;
        if (!job){
            return <p></p>;
        }
        return (
            <Table>
                <caption>General Job Information</caption>
                <tbody>
                    <tr>
                        <td>Crawling domain</td>
                        <td>{job.seed}</td>
                    </tr>
                    <tr>
                        <td>Status</td>
                        <td>{job.status}</td>
                    </tr>
                    <tr>
                        <td>ID</td>
                        <td>{job.id}</td>
                    </tr>
                </tbody>
            </Table>
        );
    }
});


export var JobPage = React.createClass({
    render: function () {
        var jobId = this.props.params.id;
        return (
            <div className="row">
                <div className="col-lg-6">
                    <Panel collapsible defaultExpanded>
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

