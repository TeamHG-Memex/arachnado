
var React = require("react");
var Reflux = require("reflux");
var moment = require('moment');
var debounce = require("debounce");
var { Table, Button, ButtonGroup, Glyphicon, Modal, FormControl, Well } = require("react-bootstrap");
var { KeyValueList } = require("../components/KeyValueList");
var { keyValueListToDict } = require('../utils/SitesAPI');
var JobStore = require("../stores/JobStore");
var SitesStore = require("../stores/SitesStore");

var SiteTable = React.createClass({
    render() {
        var rows = this.props.sites.map((site, index) =>
            <SiteRow site={site} key={site._id}/>
        );
        return (<Table>
            <thead>
                <tr>
                    <th></th>
                    <th>URL</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Detected spider</th>
                    <th>Last crawled</th>
                    <th>
                        CRON &nbsp;&nbsp;
                        <a title="More about CRON format" href="http://www.nncron.ru/help/EN/working/cron-format.htm" target="_blank" >?</a>
                    </th>
                    <th>Notes</th>
                    <th></th>
                </tr>
            </thead>
            {rows}
        </Table>);
    }
});

var NoRows = React.createClass({
    render() {
        return (<tr>
            <td colSpan="8">No sites to show. Feel free to add one using button above</td>
        </tr>);
    }
});

var SiteRow = React.createClass({
    getInitialState() {
        return {
            site: this.props.site,
            optionsVisible: false,
        }
    },
    render() {
        var scheduleValid = !this.props.site.schedule || this.props.site.schedule_valid !== false;
        var scheduleStyle = scheduleValid
            ? {}
            : {backgroundColor: '#FFDDDC'};
        scheduleStyle.width = '100px';
        var scheduleText = '';
        if (this.props.site.schedule) {
            scheduleText = scheduleValid
                ? "Next run: " + this.formatTime(this.props.site.schedule_at)
                : "Invalid entry"
        }
        var statusMessage = this.props.site.error
            ? (<div><small className="text-danger">{this.props.site.error}</small></div>)
            : (<div>{this.props.site.status}</div>);
        var trClass = this.props.site.error
            ? 'danger'
            : this.props.site.status != 200
                ? 'warning'
                : '';
        return (
            <tbody>
                <tr className={trClass}>
                    <td>
                        <ButtonGroup style={{display:"flex"}} bsSize="xsmall">
                            <Button bsStyle="success" onClick={this.startCrawl}>Crawl</Button>
                        </ButtonGroup>
                    </td>
                    <td>
                        <small>
                            <a href={this.props.site.url} target="_blank">
                                {this.shortenUrl(this.props.site.url)}
                            </a>
                        </small>
                    </td>
                    <td>{this.props.site.title}</td>
                    <td>{statusMessage}</td>
                    <td>{this.props.site.engine}</td>
                    <td>{this.formatTime(this.props.site.last_crawled)}</td>
                    <td>
                        <input type="text" bsSize="small" onChange={this.onScheduleChange}
                            style={scheduleStyle} ref="schedule" value={this.state.site.schedule}/>
                        <br/>
                        <small>{scheduleText}</small>
                    </td>
                    <td>
                        <textarea onChange={this.onNotesChange} ref="notes" value={this.state.site.notes}></textarea>
                    </td>
                    <td>
                        <ButtonGroup style={{display:"flex"}} bsSize="xsmall">
                            <Button bsStyle="info" onClick={this.toggleOptions} active={this.state.optionsVisible}>
                                <Glyphicon glyph="cog"/>
                            </Button>
                            &nbsp;
                            <Button bsStyle="danger" onClick={this.delete}>
                                <Glyphicon glyph="remove"/>
                            </Button>
                        </ButtonGroup>
                    </td>
                </tr>
                {this.state.optionsVisible ?
                <tr>
                    <td colSpan="4"></td>
                    <td colSpan="6">
                        <Well style={{marginTop:-4}}>
                            <KeyValueList title="Scrapy settings" list={this.state.site.settings} onChange={this.onSettingsChange}/>
                            <KeyValueList title="Spider args" list={this.state.site.args} onChange={this.onArgsChange}/>
                        </Well>
                    </td>
                </tr>
                : null}
            </tbody>
        )
    },
    delete(e) {
        e.preventDefault();
        if (confirm("Are you sure?")){
            SitesStore.Actions.delete(this.props.site._id);
        }
    },
    startCrawl(e) {
        e.preventDefault();
        SitesStore.Actions.update({
            _id: this.props.site._id,
            last_crawled: new Date(),
        });

        var options = {
            settings: keyValueListToDict(this.props.site.settings),
            args: keyValueListToDict(this.props.site.args)
        };

        // checking for == 'generic' to be backwards compatible
        if(!this.props.site.engine || this.props.site.engine == 'generic') {
            JobStore.Actions.startCrawl(this.props.site.url, options);
        } else {
            args.start_urls = [this.props.site.url];
            var url = 'spider://' + this.props.site.engine;
            JobStore.Actions.startCrawl(url, options);
        }
    },
    formatTime(dt) {
        if(!dt) {
            return 'never';
        } else {
            return moment(dt).fromNow();
        }
    },
    shortenUrl(url, maxLength=40) {
        if(url) {
            url = url.replace(/^https?:\/\//gi, '');
        }
        // if(url.length > maxLength) {
        //     url = url.substring(0, Math.min(url.length/2, maxLength/2));
        //     url += '...';
        //     url += url.substring(Math.min(url.length/2, maxLength/2), Math.max(url.length, maxLength));
        // }
        return url;
    },
    toggleOptions(e) {
        e.preventDefault();
        this.setState({optionsVisible: !this.state.optionsVisible});
    },
    onArgsChange(args) {
        this.state.site.args = args;
        this.setState(this.state);
        this.sendState();
    },
    onSettingsChange(settings) {
        this.state.site.settings = settings;
        this.setState(this.state);
        this.sendState();
    },
    onNotesChange(e) {
        var value = this.refs.notes.value;
        this.state.site.notes = value;
        this.setState(this.state);
        this.sendState();
    },
    onScheduleChange() {
        var value = this.refs.schedule.value;
        this.state.site.schedule = value;
        this.setState(this.state);
        this.sendState();
    },
    sendState() {
        SitesStore.Actions.update(this.state.site);
    }


});

var Header = React.createClass({
    render() {
        return (
            <div>
                <h2>Known sites <AddSite/></h2>
            </div>
        );
    }
});

var AddSite = React.createClass({
    getInitialState() {
        return { showModal: false, newSites: ''};
    },

    close() {
        this.setState({ showModal: false });
    },

    open() {
        this.setState({ showModal: true });
    },

    addSites() {
        var urlRegex = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,6}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
        var urls = this.refs.newSites.value.match(urlRegex);
        if (urls !== null) {
            urls.forEach((url) => {
                SitesStore.Actions.create(url);
            });
            alert('Added ' + urls.length + ' new URLs');

        } else {
            alert('No URLs found!')
        }
        this.close();
    },

    render() {
        return (
            <span className="pull-right">
                <Button bsStyle="primary" onClick={this.open}><Glyphicon glyph="plus"/>&nbsp;&nbsp;Add sites</Button>
                <Modal show={this.state.showModal} onHide={this.close} bsSize="large" style={{height: '100%'}}>
                    <Modal.Header closeButton>
                        <Modal.Title>Insert site URL(s) here</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <textarea ref="newSites" style={{width: '100%', height: '400px'}}></textarea>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button bsStyle="primary" onClick={this.addSites}>Add sites</Button>
                    </Modal.Footer>
                </Modal>
            </span>
        );
    }
});


export var SitesPage = React.createClass({
    mixins: [
        Reflux.connect(SitesStore.store, "sites"),
    ],
    render: function() {
        return (
            <div>
                <Header/>
                <SiteTable sites={this.state.sites}/>
            </div>
        );
    }
});
