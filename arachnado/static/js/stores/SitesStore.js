require("babel-core/polyfill");
var Reflux = require("reflux");
var { FancyWebSocket } = require("../utils/FancyWebSocket");
var API = require("../utils/SitesAPI");
var Rpc = require("../utils/Rpc")


export var Actions = Reflux.createActions([
    "setAll",
    "create",
    "update",
    "delete",
    "serverCreate",
    "serverUpdate",
    "serverDelete",
]);

// Show failed sites last
var siteCmp = function(site1, site2) {
    return site1.url < site2.url ? -1 : 1;
}

export var store = Reflux.createStore({
    init: function () {
        this.sites = [];
        this.listenToMany(Actions);
    },

    getInitialState: function () {
        return this.sites;
    },

    onSetAll: function (sites) {
        this.sites = sites;
        this.sites.sort(siteCmp);
        this.trigger(this.sites);
    },

    onServerCreate: function (site) {
        this.sites.push(site);
        this.sites.sort(siteCmp);
        this.trigger(this.sites);
    },

    onServerUpdate: function(site) {
        var siteIndex = this.sites.findIndex((site_) => {
            return site_._id == site._id;
        });
        if(siteIndex !== -1) {
            Object.assign(this.sites[siteIndex], site);
            this.sites.sort(siteCmp);
            this.trigger(this.sites);
        }
    },

    onServerDelete: function(site) {
        var siteIndex = this.sites.findIndex((site_) => {
            return site_._id == site._id;
        });
        if(siteIndex !== -1) {
            this.sites.splice(siteIndex, 1);
            this.trigger(this.sites);
        }
    },

    onCreate: function(url) {
        Rpc.call('sites.post', {site: {url: url}});
    },

    onUpdate: function(site) {
        Rpc.call('sites.patch', {site: site});
    },

    onDelete: function(siteId) {
        Rpc.call('sites.delete', {site: {_id: siteId}});
    }
});

Rpc.socket.on("open", () => {
    Rpc.call("sites.list").then(function(sites) {
        Actions.setAll(sites);
        Rpc.call('sites.subscribe');
    });
});

Rpc.socket.on("sites.created", (site) => {
    Actions.serverCreate(site);
});

Rpc.socket.on("sites.updated", (site) => {
    Actions.serverUpdate(site);
});

Rpc.socket.on("sites.deleted", (site) => {
    Actions.serverDelete(site);
});

