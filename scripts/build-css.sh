#!/usr/bin/env bash

export NODE_PATH=$(npm root -g)
export NODE_ENV=production
export BABEL_ENV=production
echo "Building stylesheet..."
webpack --config ./scripts/stylesheets.js
rm ./docs/assets/stylesheets/swagger-ui.js
