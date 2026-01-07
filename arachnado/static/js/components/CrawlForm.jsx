/* A form for starting the crawl */

var React = require("react");
var { Panel, Glyphicon } = require("react-bootstrap");

var {CrawlOptions} = require("../components/CrawlOptions");
var JobStore = require("../stores/JobStore");
var {keyValueListToDict} = require('../utils/SitesAPI');


// it must be rendered inside a small bootstrap Panel
var noPadding = {
    paddingLeft: 0, paddingRight: 0, marginLeft: 0, marginRight: 0
};

var tinyPadding = {
    paddingLeft: 0, paddingRight: 1, marginLeft: 0, marginRight: 0
};

export var CrawlForm = React.createClass({
    getInitialState: function () {
        return {value: "", isOptionsVisible: false, settings: [], args: []};
    },

    render: function () {
        var toggleOptionsClass = 'form-control btn btn-info' + (this.state.isOptionsVisible ? ' active' : '');
        return (
            <div>
                <form method="post" className="container-fluid" style={noPadding}
                      action={this.props.action} onSubmit={this.onSubmit}>
                    <div className="form-group row" style={noPadding}>
                        <div className="col-xs-2"  style={noPadding}>
                            <button type="submit" className="btn btn-success" style={{width:"100%"}}>Crawl</button>
                        </div>
                        <div className="col-xs-9" style={tinyPadding}>
                            <input type="text" className="form-control" name="domain"
                                   ref="domainInput" value={this.state.value}
                                   onChange={this.onChange}
                                   placeholder="website URL, e.g. scrapy.org"/>
                        </div>
                        <div className="col-xs-1" style={noPadding}>
                            <button className={toggleOptionsClass} onClick={this.toggleOptions}>
                                <Glyphicon glyph="cog"/>
                            </button>
                        </div>
                    </div>
                </form>
                {this.state.isOptionsVisible
                    ? <CrawlOptions args={this.state.args} settings={this.state.settings}
                        onArgsChange={this.onArgsChange} onSettingsChange={this.onSettingsChange} />
                    : null
                }
            </div>
        );
    },

    onChange: function (ev) {
        this.setState({value: this.refs.domainInput.value});
    },

    onSubmit: function (ev) {
        ev.preventDefault();
        var options = {
            settings: keyValueListToDict(this.state.settings),
            args: keyValueListToDict(this.state.args),
        };
        if (this.state.value != "") {
            JobStore.Actions.startCrawl(this.state.value, options);
            this.setState({value: ""});
        }
        this.setState({isOptionsVisible: false})
    },

    onSettingsChange: function(settings) {
        this.setState({settings: settings});
    },

    onArgsChange: function(args) {
        this.setState({args: args});
    },

    toggleOptions: function(e) {
        e.preventDefault();
        this.setState({isOptionsVisible: !this.state.isOptionsVisible});
    },

});

