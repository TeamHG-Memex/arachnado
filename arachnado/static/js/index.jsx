var React = require("react");
var { Panel } = require("react-bootstrap");

var { JobList } = require("./components/JobList.jsx");
var { AggregateJobStats } = require("./components/JobStats.jsx");
var { ProcessStatsTable } = require("./components/ProcessStats.jsx");
var { CrawlForm } = require("./components/CrawlForm.jsx");


var Index = React.createClass({
    render: function () {
        return (
            <div className="row">
                <div className="col-lg-6 col-md-7">
                    <Panel collapsible defaultExpanded header="New Crawl" bsStyle="default">
                        <CrawlForm action={window.START_CRAWL_URL} />
                    </Panel>
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


$(window).ready(function() {
    React.render(<Index/>, document.getElementById("arachnado-index-page"));
});
