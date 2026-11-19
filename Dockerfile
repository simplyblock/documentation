FROM squidfunk/mkdocs-material:9.6.5
# sbcli's own dependencies (fastapi, boto3, pykmip, ...) used to live here too,
# so that openapi-json-gen.py could import simplyblock_web.app far enough to
# call app.openapi(). That generation step now runs in sbcli's own CI, which
# publishes openapi.json as a build artifact (see doc-builder's gen_sbcli_ref,
# "OpenAPI schema" workflow in simplyblock/sbcli) -- this image no longer
# imports sbcli code at all, so it only needs the documentation site's own
# tooling.
RUN pip install mkdocs-git-revision-date-localized-plugin "mkdocs-material[imaging]" \
    mkdocs-nav-weight mkdocs-redirects mkdocs-glightbox mike mkdocs-video mkdocs-meta-descriptions-plugin \
    markdown-captions jinja2 mkdocs-link-marker mkdocs-markdownextradata-plugin \
    mkdocs-render-swagger-plugin mkdocs-macros-plugin
RUN apk add --no-cache nodejs npm bash
RUN npm install --global webpack webpack-cli mini-css-extract-plugin cssnano css-loader \
    postcss-loader sass-loader sass tachyons-sass postcss-preset-env
