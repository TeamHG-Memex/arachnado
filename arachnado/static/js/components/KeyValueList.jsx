var React = require("react");
var { Glyphicon } = require("react-bootstrap");

export var KeyValueList = React.createClass({
    getInitialState: function() {
        return {
            list: this.props.list || [],
        }
    },
    render: function() {
        var rows = this.state.list.map((item, index) =>
            <KeyValueRow
                index={index}
                key={index}
                key_={item.key}
                value_={item.value}
                keyPlaceholder={this.props.keyPlaceholder}
                valuePlaceholder={this.props.valuePlaceholder}
                onDelete={this.onDelete}
                onChange={this.onChange}/>
        );
        return (
            <div className="clearfix">
                <h5>
                    <button className="btn btn-success btn-xs" onClick={this.onCreate}>
                        <Glyphicon glyph="plus" /> Add
                    </button>
                    &nbsp;&nbsp;
                    {this.props.title}
                </h5>
                {rows}
            </div>
        );
    },
    onCreate: function() {
        this.state.list.push({key: '', value: ''});
        this.setStateNotify(this.state.list);
    },
    onDelete: function(index) {
        this.state.list.splice(index, 1);
        this.setStateNotify(this.state.list);
    },
    onChange: function(index, key, value) {
        this.state.list[index].key = key;
        this.state.list[index].value = value;
        this.setStateNotify(this.state.list);
    },
    setStateNotify: function(list) {
        this.setState(list);
        if(this.props.onChange) {
            this.props.onChange(list);
        }
    }
});


var KeyValueRow = React.createClass({
    getInitialState: function() {
        return {
            key: this.props.key_ || '',
            value: this.props.value_ || '',
        };
    },
    render: function() {
        return (
            <div>
                <div className="col-xs-5">
                    <input type="text" placeholder={this.props.keyPlaceholder}
                        style={{width: '100%'}} value={this.state.key} onChange={this.onKeyChange}/>
                </div>
                <div className="col-xs-6">
                    <input type="text" placeholder={this.props.valuePlaceholder}
                        style={{width: '100%'}} value={this.state.value} onChange={this.onValueChange}/>
                </div>
                <div className="col-xs-1">
                    <button className="btn btn-danger btn-xs pull-right" onClick={this.props.onDelete}>
                        <Glyphicon glyph="minus" />
                    </button>
                </div>
            </div>
        )
    },

    onKeyChange: function(e) {
        this.state.key = e.target.value;
        this.onUpdate(this.props.index, this.state.key, this.state.value);
    },

    onValueChange: function(e) {
        this.state.value = e.target.value;
        this.onUpdate(this.props.index, this.state.key, this.state.value);
    },

    onUpdate: function(index, key, value) {
        if(this.props.onChange) {
            this.props.onChange(index, key, value);
        }
    }
})
