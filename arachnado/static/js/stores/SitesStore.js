require("babel-core/polyfill");
var Reflux = require("reflux");
var debounce = require("debounce");
var { FancyWebSocket } = require("../utils/FancyWebSocket");


export var Actions = Reflux.createActions([
    "setAll",
    "update",
]);


export var store = Reflux.createStore({
    init: function () {
        this.sites = [];
        this.listenToMany(Actions);
        this.triggerDebounced = debounce(this.trigger, 200);
    },

    getInitialState: function () {
        return this.sites;
    },

    onSetAll: function (jobs) {
        this.sites = sites;
        this.triggerDebounced(sites);
    },
});


var socket = FancyWebSocket.instance();

socket.on("sites:set", (sites) => {
    Actions.setAll(sites);
});
