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
        this.trigger(sites);
    },

    onServerCreate: function (site) {
        this.sites.push(site);
        this.trigger(this.sites);
    },

    onServerUpdate: function(site) {
        var siteIndex = this.sites.findIndex((site_) => {
            return site_._id == site._id;
        });
        if(siteIndex !== -1) {
            Object.assign(this.sites[siteIndex], site);
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
        API.createSite(url);
        //Rpc.call('sites.post', {site: {url: url}});
    },

    onUpdate: function(site) {
        API.updateSite(site);
        //Rpc.call('sites.patch', {site: site});
    },

    onDelete: function(siteId) {
        API.deleteSite(siteId);
        //Rpc.call('sites.delete', {site: {_id: siteId}});
    }
});

// Rpc.socket.on("open", () => {
//     Rpc.call("sites.list").then(function(sites) {
//         Actions.setAll(sites);
//     })
// });


var socket = FancyWebSocket.instance(window.WS_SITES_SERVER_ADDRESS);

socket.on("sites:set", (sites) => {
    Actions.setAll(sites);
});

socket.on("sites:created", (site) => {
    Actions.serverCreate(site);
});

socket.on("sites:updated", (site) => {
    Actions.serverUpdate(site);
});

socket.on("sites:deleted", (site) => {
    Actions.serverDelete(site);
});

