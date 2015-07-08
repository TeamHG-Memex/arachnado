var React = require("react");
var Reflux = require("reflux");
var { Alert, Badge, Button } = require("react-bootstrap");
var { Navigation } = require('react-router');
var JobStore = require("../stores/JobStore");


var NewJobStarting = React.createClass({
    render: function() {
        return (
            <Alert bsStyle="warning">
                New job is starting
            </Alert>
        );
    }
});

var NewJobStarted = React.createClass({
    mixins: [Navigation],
    render: function() {
        return (
            <Alert bsStyle="success">
                New job with login credentials has started
                &nbsp;&nbsp;&nbsp;
                <Button bsSize="xsmall" bsStyle="default" onClick={this.transitionToNewJob}>Go to job ({this.props.newJobId})</Button>
            </Alert>
        );
    },
    transitionToNewJob: function() {
        this.transitionTo("job", {id: this.props.newJobId})
    },
});


var LoginFailed = React.createClass({
    render: function() {
        return (
            <Alert bsStyle="danger">
                Login failed. Please check credentials and check again.
            </Alert>
        );
    }
});


var LoginSuccess = React.createClass({
    render: function() {
        return (
            <Alert bsStyle="info">
                Login successfull.
                &nbsp;&nbsp;&nbsp;
                <Button bsSize="xsmall" bsStyle="default" onClick={this.startNewJob}>
                    Start new job with those credentials
                </Button>
            </Alert>
        );
    },
    startNewJob: function() {
        this.props.startNewJob(this.props.username, this.props.password)
    }
});

var LoginInProgress = React.createClass({
    render: function() {
        return <Alert bsStyle="info">
            Login in progres...
        </Alert>;
    }
})


var LoginCredentialsWidget = React.createClass({
    getInitialState: function() {
        return {username: '', password: ''};
    },
    usernameChanged: function(event) {
        this.setState({username: event.target.value});
    },
    passwordChanged: function(event) {
        this.setState({password: event.target.value});
    },
    render: function() {
        var loginMessage = null;
        if(this.props.newJobStarting) {
            if(this.props.newJobId) {
                loginMessage = <NewJobStarted newJobId={this.props.newJobId}/>;
            } else {
                loginMessage = <NewJobStarting/>;
            }
        }
        else if(this.props.loginRequested) {
            if(this.props.job.flags.find(f => f == 'test_login_failed')) {
                loginMessage = <LoginFailed/>;
            }
            else if(this.props.job.flags.find(f => f == 'test_login_success')) {
                loginMessage = <LoginSuccess startNewJob={this.props.startNewJob} username={this.state.username} password={this.state.password}/>;
            }
            else {
                loginMessage = <LoginInProgress/>;
            }
        }

        return (
            <div key={this.props.job.id}>
                <form onSubmit={this.onSubmit} method="GET">
                    <input type="text" placeholder="Username" className="form-control"
                        onChange={this.usernameChanged}/>
                    <input type="password" placeholder="Password" className="form-control"
                        onChange={this.passwordChanged}/>

                    <input type="submit" className="btn btn-primary btn-xs form-control"
                        value="Login"/>
                </form>
                {loginMessage}
            </div>
        );
    },
    onSubmit: function(e) {
        e.preventDefault();
        this.props.startLogin(this.state.username, this.state.password);
    }
});


export var LoginCredentials = React.createClass({
    mixins: [Reflux.connect(JobStore.store, 'jobs')],
    getInitialState: function() {
        return {loginRequested: false, newJobStarting: false};
    },
    render: function() {
        var newJobId = this.findChildJobId();
        return <LoginCredentialsWidget job={this.props.job} newJobId={newJobId}
            loginRequested={this.state.loginRequested} startLogin={this.startLogin}
            startNewJob={this.startNewJob} newJobStarting={this.state.newJobStarting}
            key={this.props.job.id}/>
    },


    startLogin: function(username, password) {
        JobStore.Actions.login(this.props.job.id, username, password);
        this.setState({loginRequested: true});
    },

    //TODO: move to the store?
    startNewJob: function(username, password) {
        JobStore.Actions.startCrawl(this.props.job.seed, {
            args: {
                login_username: username,
                login_password: password,
                login_url: this.props.job.login_url,
                parent_job_id: this.props.job.id
            }
        });
        this.setState({newJobStarting: true});
    },

    findChildJobId: function() {
        var childJob = this.state.jobs.find(job => job.args.parent_job_id == this.props.job.id);
        if(childJob) {
            return childJob.id;
        }
    },
});
