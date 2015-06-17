var React = require("react");
var Reflux = require("reflux");
var JobStore = require("../stores/JobStore");

export var JobsMixin = Reflux.connect(JobStore.store, "jobs");

export var SingleJobMixin = Reflux.connectFilter(
    JobStore.store,
    "job",
    function(jobs) {
        return jobs.filter(job => job.id == this.props.id)[0];
    }
);

