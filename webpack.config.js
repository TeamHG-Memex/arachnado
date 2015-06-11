var path = require('path');
var webpack = require('webpack');

function _static(name){
    return path.resolve(__dirname, 'arachnado/static/', name);
}

module.exports = {
    entry: {
        'common': _static("js/common.js"),
        'index': _static("js/index.jsx"),

        'vendor': ['react-bootstrap', 'eventemitter3', 'reflux'],
    },
    output: {
        path: _static("build"),
        filename: '[name].js',
    },
    module: {
        loaders: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                loader: "babel-loader"
            },
        ]
    },
    plugins: [
        new webpack.optimize.CommonsChunkPlugin("vendor", "vendor.js")
    ],
    externals: {
        react: 'React'
    }
    //devtool: "#inline-source-map",
};
