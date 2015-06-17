/* Main entry point */

var React = require("react");
var Router = require('react-router');
var { Route, RouteHandler, Link, DefaultRoute, NotFoundRoute } = Router;

var { IndexPage } = require("./pages/IndexPage.jsx");
var { JobPage } = require("./pages/JobPage.jsx");

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
      return (
          <RouteHandler/>
      );
  }
});

var routes = (
    <Route path="/" handler={App}>
        <DefaultRoute handler={IndexPage} name="index" />
        <Route path="job/:id" handler={JobPage} name="job" />
        <NotFoundRoute handler={NotFound} />
    </Route>
);

Router.run(routes, Router.HashLocation, (Root) => {
    React.render(<Root/>, document.getElementById("arachnado-root"));
});
