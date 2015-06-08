/* A list of active crawl jobs */

var React = require("react");
var Reflux = require("reflux");

var { Table } = require("react-bootstrap");
var JobListStore = require("../stores/JobListStore");

var STATUS_CLASSES = {
    'crawling': 'success',
    'done': ''
};

var NoJobs = React.createClass({
    render: function () {
        return (<div>
            <p>No jobs to show.</p>
            <p>
                Start a crawling job either by using "Crawl" button
                in the header or by using Arachnado HTTP API.
            </p>
        </div>);
    }
});


var JobRow = React.createClass({
    render: function () {
        var job = this.props.job;
        var cls = STATUS_CLASSES[job.status];
        return (
            <tr className={cls}>
                <th scope="row">{job.id}</th>
                <td>{job.seed}</td>
                <td>{job.status}</td>
            </tr>
        );
    }
});


var JobListWidget = React.createClass({
    render: function () {
        var rows = this.props.jobs.map(job => {return <JobRow job={job} key={job.id}/>});

        return <Table condensed>
            <caption></caption>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Seed URL</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </Table>;
    }
});


var JobList = React.createClass({
    mixins: [Reflux.connect(JobListStore.store, "jobs")],
    render: function () {
        if (!this.state.jobs.length) {
            return <NoJobs/>;
        }
        return <JobListWidget jobs={this.state.jobs}/>;
    }
});


export function install(elemId){
    React.render(<JobList/>, document.getElementById(elemId));
}
