var path = require('path');
var webpack = require('webpack');

module.exports = {
    entry: {
        'app': './arachnado/static/js/main.js',
        'vendor': ['react-bootstrap', 'eventemitter3'],
    },
    output: {
        path: path.resolve(__dirname, 'arachnado/static/build'),
        filename: 'app.js',
    },
    module: {
        loaders: [
            { test: /\.jsx?$/, exclude: /node_modules/, loader: "babel-loader"},
        ]
    },
    plugins: [
        new webpack.optimize.CommonsChunkPlugin("vendor", "vendor.js")
    ],
    externals: {
        react: 'React'
    }
};
