/* Main (index) page */

var React = require("react");
var { Panel } = require("react-bootstrap");

var { JobList } = require("../components/JobList");
var { AggregateJobStats } = require("../components/JobStats");
var { ProcessStatsTable } = require("../components/ProcessStats");
var { CrawlForm } = require("../components/CrawlForm");


export var IndexPage = React.createClass({
    render: function () {
        return (
            <div className="row">
                <div className="col-lg-7 col-md-7">
                    <CrawlForm action={window.START_CRAWL_URL} />
                    <Panel collapsible defaultExpanded header="Jobs" bsStyle="primary">
                        <JobList/>
                    </Panel>
                    <Panel collapsible defaultExpanded header="Arachnado Stats" className="hidden-lg">
                        <ProcessStatsTable />
                    </Panel>
                </div>
                <div className="col-lg-5 col-md-5">
                    <Panel collapsible defaultExpanded header="Arachnado Stats" className="visible-lg-block">
                        <ProcessStatsTable />
                    </Panel>
                    <Panel collapsible defaultExpanded header="Aggregate Crawl Stats">
                        <AggregateJobStats/>
                    </Panel>
                </div>
            </div>
        );
    }
});
