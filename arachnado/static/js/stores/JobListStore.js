var Reflux = require("reflux");
var { FancyWebSocket } = require("../utils/FancyWebSocket");
require("babel-core/polyfill");


export var Actions = Reflux.createActions([
    "setAll",
    "updateStats",
]);


export var store = Reflux.createStore({
    init: function () {
        this.jobs = [];
        this.listenTo(Actions.setAll, this.onSetAll);
        this.listenTo(Actions.updateStats, this.onUpdateStats);
    },

    getInitialState: function () {
        return this.jobs;
    },
    
    onSetAll: function (jobs) {
        this.jobs = jobs;
        this.trigger(jobs);
    },

    onUpdateStats: function (crawlId, changes) {
        this.jobs.filter(job => job.id == crawlId).forEach(job => {
            job.stats = Object.assign(job.stats || {}, changes);
        });
        this.trigger(this.jobs);
    }
});


var socket = FancyWebSocket.instance();
socket.on("jobs:state", (jobs) => {
    console.log("jobs:state", jobs);
    Actions.setAll(jobs);
});

socket.on("stats:changed", (data) => {
    var [crawlId, changes] = data;
    Actions.updateStats(crawlId, changes);
    //console.log("stats:changed", crawlId, changes);
});

Actions.setAll(window.INITIAL_DATA.jobs);

