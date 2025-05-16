/**
 * @prettier
 */

// NOTE: this config *does not* inherit from `_config-builder`.
// It is also used in the dev config.

const path = require("path")
const MiniCssExtractPlugin = require("mini-css-extract-plugin")

module.exports = {
  mode: "production",

  resolveLoader: {
    modules: [process.env.NODE_PATH]
  },

  entry: {
    "swagger-ui": "./scripts/style/main.scss",
  },

  module: {
    rules: [
      {
        test: [/\.(scss)(\?.*)?$/],
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
          },
          {
            loader: "css-loader",
            options: { sourceMap: true },
          },
          {
            loader: "postcss-loader",
            options: {
              postcssOptions: {
                sourceMap: true,
                plugins: [
                  require("cssnano")(),
                  "postcss-preset-env", // applies autoprefixer
                ],
              },
            },
          },
          {
            loader: "sass-loader",
            options: {
              api: "modern-compiler",
              sourceMap: true,
              sassOptions: {
                quietDeps: true,
              },
            },
          },
        ],
      },
    ],
  },

  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].css",
    }),
  ],

  devtool: "source-map",

  output: {
    path: path.join(__dirname, "../docs/assets", "stylesheets"),
    publicPath: "/assets/stylesheets",
  },

  optimization: {
    splitChunks: {
      cacheGroups: {
        styles: {
          name: "styles",
          test: /\.css$/,
          chunks: "all",
          enforce: true,
        },
      },
    },
  },
}