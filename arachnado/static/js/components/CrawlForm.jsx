/* A form for starting the crawl */

var React = require("react");
var { Panel, Glyphicon } = require("react-bootstrap");

var JobStore = require("../stores/JobStore");


// it must be rendered inside a small bootstrap Panel
var noPadding = {
    paddingLeft: 0, paddingRight: 0, marginLeft: 0, marginRight: 0
};

var KeyValueRow = React.createClass({
    getInitialState: function() {
        return {key: '', value: ''};
    },
    render: function() {
        return (
            <div>
                <div className="col-xs-5">
                    <input type="text" placeholder={this.props.keyPlaceholder} style={{width: '100%'}} onChange={this.onKeyChange}/>
                </div>
                <div className="col-xs-6">
                    <input type="text" placeholder={this.props.valuePlaceholder} style={{width: '100%'}} onChange={this.onValueChange}/>
                </div>
                <div className="col-xs-1">
                    <button className="btn btn-danger btn-xs pull-right" onClick={this.props.deleteRow}>
                        <Glyphicon glyph="minus" />
                    </button>
                </div>
            </div>
        )
    },

    onKeyChange: function(e) {
        this.state.key = e.target.value;
        this.props.updateRow(this.state.key, this.state.value);
    },

    onValueChange: function(e) {
        this.state.value = e.target.value;
        this.props.updateRow(this.state.key, this.state.value);
    }
})


var CrawlOptions = React.createClass({
    render: function() {
        return (
            <div className="panel panel-danger" style={{marginTop: '-15px'}}>
                <div className="panel-heading">
                    <h4 className="panel-title">
                        <a href="#" aria-expanded="true">Crawl options</a>
                    </h4>
                </div>
                <div className="panel-collapse collapse in">
                    <div className="panel-body">
                        <ScrapySettings
                            scrapySettings={this.props.scrapySettings}
                            addScrapySetting={this.props.addScrapySetting}
                            delScrapySetting={this.props.delScrapySetting}
                            setScrapySetting={this.props.setScrapySetting} />
                        <SpiderArgs
                            spiderArgs={this.props.spiderArgs}
                            addSpiderArg={this.props.addSpiderArg}
                            delSpiderArg={this.props.delSpiderArg}
                            setSpiderArg={this.props.setSpiderArg} />
                    </div>
                </div>
            </div>
        );
    }

});

var ScrapySettings = React.createClass({
    render: function() {
        var settingRows = this.props.scrapySettings.map((setting, index) =>
            <KeyValueRow keyPlaceholder="Setting name, e.g. USER_AGENT" valuePlaceholder="Setting value"
                deleteRow={this.props.delScrapySetting.bind(this, index)}
                updateRow={this.props.setScrapySetting.bind(this, index)}/>
        );
        return (
            <div>
                <h5>Scrapy settings &nbsp;&nbsp;
                    <button className="btn btn-success btn-xs" onClick={this.props.addScrapySetting}>
                        <Glyphicon glyph="plus" />
                    </button>
                </h5>
                {settingRows}
            </div>
        );
    }
});


var SpiderArgs = React.createClass({
    render: function() {
        var argsRows = this.props.spiderArgs.map((setting, index) =>
            <KeyValueRow keyPlaceholder="Argument name" valuePlaceholder="Argument value"
                deleteRow={this.props.delSpiderArg.bind(this, index)}
                updateRow={this.props.setSpiderArg.bind(this, index)}/>
        );
        return (
            <div>
                <h5>Spider arguments &nbsp;&nbsp;
                    <button className="btn btn-success btn-xs" onClick={this.props.addSpiderArg}>
                        <Glyphicon glyph="plus" />
                    </button>
                </h5>
                {argsRows}
            </div>
        );
    }
});


export var CrawlForm = React.createClass({
    getInitialState: function () {
        return {value: "", isOptionsVisible: false, scrapySettings: [], spiderArgs: []};
    },

    render: function () {
        var toggleOptionsClass = 'form-control btn' + (this.state.isOptionsVisible ? ' active btn-success' : '');
        return (
            <div>
                <form method="post" className="container-fluid" style={noPadding}
                      action={this.props.action} onSubmit={this.onSubmit}>
                    <div className="form-group row" style={noPadding}>
                        <div className="col-xs-2"  style={noPadding}>
                            <button type="submit" className="btn btn-success" style={{width:"100%"}}>Crawl</button>
                        </div>
                        <div className="col-xs-9" style={noPadding}>
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
                    ? <CrawlOptions
                        scrapySettings={this.state.scrapySettings}
                        addScrapySetting={this.addKeyValue.bind(this, 'scrapySettings')}
                        delScrapySetting={this.delKeyValue.bind(this, 'scrapySettings')}
                        setScrapySetting={this.setKeyValue.bind(this, 'scrapySettings')}
                        spiderArgs={this.state.spiderArgs}
                        addSpiderArg={this.addKeyValue.bind(this, 'spiderArgs')}
                        delSpiderArg={this.delKeyValue.bind(this, 'spiderArgs')}
                        setSpiderArg={this.setKeyValue.bind(this, 'spiderArgs')} />
                    : null
                }

            </div>
        );
    },

    onChange: function (ev) {
        this.setState({value: this.refs.domainInput.getDOMNode().value});
    },

    onSubmit: function (ev) {
        var options = {
            settings: this.keyValuelistToDict(this.state.scrapySettings),
            args: this.keyValuelistToDict(this.state.spiderArgs),
        }
        ev.preventDefault();
        if (this.state.value != "") {
            JobStore.Actions.startCrawl(this.state.value, options);
            this.setState({value: ""});
        }
        this.setState({isOptionsVisible: false})
    },

    toggleOptions: function(e) {
        e.preventDefault();
        this.setState({isOptionsVisible: !this.state.isOptionsVisible});
    },

    addKeyValue: function(name, key, value) {
        var newState = {};
        newState[name] = this.state[name];
        newState[name].push({key: '', value: ''});
        this.setState(newState);
    },

    delKeyValue: function(name, index) {
        var newState = {};
        newState[name] = this.state[name];
        newState[name].splice(index, 1);
        this.setState(newState);
    },

    setKeyValue: function(name, index, key, value) {
        var newState = {};
        newState[name] = this.state[name];
        newState[name][index]['key'] = key;
        newState[name][index]['value'] = value;
        this.setState(newState);
        console.log(this.state);
    },

    keyValuelistToDict: function(list) {
        var dict = {};
        list.forEach(function(row) {
            dict[row.key] = row.value;
        });
        return dict;
    }
});

