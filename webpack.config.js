var path = require('path');
var webpack = require('webpack');

module.exports = {
    entry: {
        'app': './arachnado/static/js/entry.js',
        'vendor': ['react-bootstrap'],
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
        new webpack.optimize.CommonsChunkPlugin(/* chunkName= */"vendor", /* filename= */"vendor.js")
    ],
    externals: {
        react: 'React'
    }
};
