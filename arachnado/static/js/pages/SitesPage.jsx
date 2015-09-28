
var React = require("react");
var Reflux = require("reflux");
var moment = require('moment');
var debounce = require("debounce");
var { Link } = require('react-router');
var { Input, Panel, Table, Button, Glyphicon, ButtonToolbar, Modal } = require("react-bootstrap");

var JobStore = require("../stores/JobStore");
var SitesStore = require("../stores/SitesStore");

var SiteTable = React.createClass({
    render() {
        var rows = this.props.sites.map((site, index) =>
            <SiteRow site={site} key={site._id}/>
        );
        return (<Table striped bordered hover>
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Detected spider</th>
                    <th>Last crawled</th>
                    <th>
                        CRON &nbsp;&nbsp;
                        <a target="_blank" title="More about CRON format" href="http://www.nncron.ru/help/EN/working/cron-format.htm">?</a>
                    </th>
                    <th>Notes</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </Table>);
    }
});

var NoRows = React.createClass({
    render() {
        return (<tr>
            <td colSpan="8">No sites to show. Feel free to add one using button above</td>
        </tr>);
    }
})

var SiteRow = React.createClass({
    getInitialState() {
        return {
            notes: this.props.site.notes,
            schedule: this.props.site.schedule,
        }
    },
    render() {
        var scheduleValid = !this.props.site.schedule || this.props.site.schedule_valid !== false;
        var scheduleStyle = scheduleValid
            ? {}
            : {backgroundColor: '#FFDDDC'};
        scheduleStyle.width = '100px';
        var scheduleText = '';
        if(this.props.site.schedule) {
            scheduleText = scheduleValid
                ? "Next run: " + this.formatTime(this.props.site.schedule_at)
                : "Invalid entry"
        }
        return (<tr>
            <td><a href={this.props.site.url} target="_blank">{this.props.site.url}</a></td>
            <td>{this.props.site.title}</td>
            <td>{this.props.site.status}</td>
            <td>{this.props.site.engine}</td>
            <td>{this.formatTime(this.props.site.last_crawled)}</td>
            <td>
                <input type="text" bsSize="small" onChange={this.onScheduleChange}
                    style={scheduleStyle} ref="schedule" value={this.state.schedule}/>
                <br/>
                <small>{scheduleText}</small>
            </td>
            <td><textarea onChange={this.onNotesChange} ref="notes" value={this.state.notes}></textarea></td>
            <td>
                <Button bsSize="small" bsStyle="danger" title="Delete" onClick={this.delete}>
                    <Glyphicon glyph="remove" />
                </Button>
                <Button bsSize="small" bsStyle="success" title="Start crawl" onClick={this.startCrawl}>
                    <Glyphicon glyph="play"/>
                </Button>
            </td>
        </tr>);
    },
    delete() {
        SitesStore.Actions.delete(this.props.site._id);
    },
    startCrawl() {
        SitesStore.Actions.update({
            _id: this.props.site._id,
            last_crawled: new Date(),
        });
        if(this.props.site.engine == 'generic') {
            JobStore.Actions.startCrawl(this.props.site.url);
        } else {
            JobStore.Actions.startCrawl(
                'spider://' + this.props.site.engine,
                {
                    args: {
                        'start_urls': [this.props.site.url],
                        'post_days': -1  // TODO: move to custom settings
                    }
                }
            )
        }
    },
    formatTime(dt) {
        if(!dt) {
            return 'never';
        } else {
            return moment(dt).fromNow();
        }
    },
    onNotesChange() {
        SitesStore.Actions.update({
            _id: this.props.site._id,
            notes: this.refs.notes.getDOMNode().value,
        });
    },
    onNotesChangeDebounced() {
        return debounce(this.onNotesChange, 200);
    },
    onScheduleChange() {
        this.setState({schedule: this.refs.schedule.getDOMNode().value})
        SitesStore.Actions.update({
            _id: this.props.site._id,
            schedule: this.state.schedule,
        })
    },
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
        var urlRegex = /[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?/gi;
        var urls = this.refs.newSites.getDOMNode().value.match(urlRegex);
        if(urls !== null) {
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
                <Button bsStyle="primary" onClick={this.open}><Glyphicon glyph="plus"/>&nbsp;&nbsp;Add site</Button>
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


export var SitePage = React.createClass({
    render: function() {

    }
})