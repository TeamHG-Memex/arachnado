/* Main entry point */

var React = require("react");
var ReactDOM = require("react-dom");
var { Router, Route, IndexRoute, hashHistory } = require('react-router');

var { IndexPage } = require("./pages/IndexPage.jsx");
var { JobPage } = require("./pages/JobPage.jsx");
var { SitesPage, SitePage } = require("./pages/SitesPage.jsx");

var NotFound = React.createClass({
    render: function () {
        return (
            <div>
                <h2>Page Not Found</h2>
                <p>The page you were trying to access doesn't exist.</p>
            </div>
        );
    }
});


var App = React.createClass({
  render () {
      // TODO: move most stuff from base.html here
      return this.props.children;
  }
});

ReactDOM.render((
    <Router history={hashHistory}>
        <Route path="/" component={App}>
            <IndexRoute component={IndexPage} />
            <Route path="job/:id" component={JobPage} />
            <Route path="sites" component={SitesPage} />
            <Route path="*" component={NotFound} />
        </Route>
    </Router>
), document.getElementById("arachnado-root"));
