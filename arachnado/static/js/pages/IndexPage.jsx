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
                <div className="col-lg-6 col-md-7">
                    <CrawlForm action={window.START_CRAWL_URL} />
                    <Panel collapsible defaultExpanded header="Jobs" bsStyle="primary">
                        <JobList/>
                    </Panel>
                    <Panel collapsible defaultExpanded header="Arachnado Stats" className="hidden-lg">
                        <ProcessStatsTable />
                    </Panel>
                </div>
                <div className="col-lg-4 col-md-5">
                    <Panel collapsible defaultExpanded header="Aggregate Crawl Stats">
                        <AggregateJobStats/>
                    </Panel>
                </div>

                <div className="col-lg-2 visible-lg-block">
                    <Panel collapsible defaultExpanded header="Arachnado Stats">
                        <ProcessStatsTable />
                    </Panel>
                </div>
            </div>
        );
    }
});
