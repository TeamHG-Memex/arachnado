var React = require("react");
var { Panel } = require("react-bootstrap");

var { JobList } = require("./components/JobList.jsx");
var { AggregateJobStats } = require("./components/JobStats.jsx");
var { ProcessStatsTable } = require("./components/ProcessStats.jsx");


var Index = React.createClass({
    render: function () {
        return (
            <div className="row">
                <div className="col-md-5">
                    <Panel collapsible defaultExpanded header="Jobs" bsStyle="primary">
                        <JobList/>
                    </Panel>
                </div>
                <div className="col-md-4">
                    <Panel collapsible defaultExpanded header="Aggregate Crawl Stats">
                        <AggregateJobStats/>
                    </Panel>
                </div>
                <div className="col-md-3">
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
