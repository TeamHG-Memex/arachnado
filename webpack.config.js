var path = require('path');
var webpack = require('webpack');

function _static(name){
    return path.resolve(__dirname, 'arachnado/static/', name);
}

module.exports = {
    entry: {
        'main': _static("js/main.jsx"),
        'common': _static("js/common.js"),

        'vendor': [
            'react',
            'react-bootstrap',
            'react-router',
            'reflux',
            'eventemitter3'
        ]
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
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    plugins: [
        new webpack.optimize.CommonsChunkPlugin("vendor", "vendor.js"),
    ]
    //devtool: "#inline-source-map",
};
