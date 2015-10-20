var Reflux = require("reflux");

export var Actions = Reflux.createActions(["create", "update", "delete"]);


export var store = Reflux.createStore({
    init: function () {
        this.list = [];
        this.listenTo(Actions.create, this.onCreate);
        this.listenTo(Actions.update, this.onUpdate);
        this.listenTo(Actions.delete, this.onDelete);
    },

    getInitialState: function () {
        return this.stats;
    },

    onUpdate: function (stats) {
        this.stats = stats;
        if (stats.server_time) {
            this.stats.serverTime = new Date(stats.server_time);
        }
        this.trigger(this.stats);
    }
});