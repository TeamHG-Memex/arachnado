var React = require("react");
var { KeyValueList } = require("./KeyValueList");


export var CrawlOptions = React.createClass({
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
                        <KeyValueList title="Scrapy settings" list={this.props.settings} onChange={this.props.onSettingsChange}/>
                        <KeyValueList title="Spider args" list={this.props.args} onChange={this.props.onArgsChange}/>
                    </div>
                </div>
            </div>
        );
    }

});
