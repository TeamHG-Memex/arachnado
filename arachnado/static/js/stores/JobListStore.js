var Reflux = require("reflux");
var { FancyWebSocket } = require("../utils/FancyWebSocket");


export var Actions = Reflux.createActions(["setAll"]);


export var store = Reflux.createStore({
    init: function () {
        this.jobs = [];
        this.listenTo(Actions.setAll, this.onSetAll);
    },

    getInitialState: function () {
        return this.jobs;
    },
    
    onSetAll: function (jobs) {
        this.jobs = jobs;
        this.trigger(jobs);
    }
});


// XXX: is it OK to listen to the web socket here?
var socket = FancyWebSocket.forEndpoint(window.WS_SERVER_ADDRESS);
socket.on("jobs:state", (jobs) => {
    console.log("jobs:state", jobs);
    Actions.setAll(jobs);
});

Actions.setAll(window.INITIAL_DATA.jobs);

