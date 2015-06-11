var Reflux = require("reflux");
var { FancyWebSocket } = require("../utils/FancyWebSocket");
require("babel-core/polyfill");

export var Actions = Reflux.createActions([
    "update",
]);


export var store = Reflux.createStore({
    init: function () {
        this.stats = {};
        this.listenTo(Actions.update, this.onUpdate);
    },

    getInitialState: function () {
        return this.stats;
    },

    onUpdate: function (stats) {
        this.stats = stats;
        this.trigger(stats);
    }
});


var socket = FancyWebSocket.instance();
socket.on("process:stats", (stats) => {
    Actions.update(stats);
});

Actions.update(window.INITIAL_DATA.processStats);
