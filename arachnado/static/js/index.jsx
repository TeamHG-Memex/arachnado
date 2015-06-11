var React = require("react");
var { JobList } = require("./components/JobList.jsx");
var { ProcessStats }= require("./components/ProcessStats.jsx");
var { AggregateJobStats }= require("./components/JobStats.jsx");

var Index = React.createClass({
    render: function () {
        return (
            <div className="row">
                <div className="col-xs-6">
                    <JobList/>
                </div>
                <div className="col-xs-6">
                    <div className="well">
                        <AggregateJobStats/>
                    </div>
                </div>
            </div>
        );
    }
});


$(window).ready(function() {
    React.render(<Index/>, document.getElementById("arachnado-index-page"));
});
