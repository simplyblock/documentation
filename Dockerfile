FROM squidfunk/mkdocs-material:9.6.5
# boto3 is pinned to a current release. kubernetes 37.0.2 requires
# python-dateutil>=3 while every botocore since 2015 requires <3; without the
# pin, pip resolves the conflict by backtracking to boto3 1.2.0, whose botocore
# does not import on Python 3.11. With the pin, pip backtracks kubernetes instead.
RUN pip install mkdocs-git-revision-date-localized-plugin "mkdocs-material[imaging]" \
    mkdocs-nav-weight mkdocs-redirects mkdocs-glightbox mike mkdocs-video mkdocs-meta-descriptions-plugin \
    markdown-captions jinja2 mkdocs-link-marker mkdocs-markdownextradata-plugin \
    mkdocs-render-swagger-plugin mkdocs-macros-plugin fastapi uvicorn flask fdb \
    docker kubernetes prettytable "boto3>=1.40" jsonschema psutil prometheus_api_client \
    jc flask_swagger_ui prometheus_client pydantic_settings starlette hvac tenacity \
    prometheus_fastapi_instrumentator py-cpuinfo ec2-metadata flask-openapi3 graypy \
    sse-starlette "sentry-sdk[flask]" paramiko
RUN apk add --no-cache nodejs npm bash
RUN npm install --global webpack webpack-cli mini-css-extract-plugin cssnano css-loader \
    postcss-loader sass-loader sass tachyons-sass postcss-preset-env
