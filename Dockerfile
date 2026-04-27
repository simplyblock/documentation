FROM squidfunk/mkdocs-material:9.6.5
RUN pip install mkdocs-git-revision-date-localized-plugin "mkdocs-material[imaging]" \
    mkdocs-nav-weight mkdocs-glightbox mike mkdocs-video mkdocs-meta-descriptions-plugin \
    markdown-captions jinja2 mkdocs-link-marker mkdocs-markdownextradata-plugin \
    mkdocs-render-swagger-plugin mkdocs-macros-plugin fastapi uvicorn flask fdb \
    docker kubernetes prettytable boto3 jsonschema psutil prometheus_api_client \
    jc flask_swagger_ui prometheus_client pydantic_settings starlette
RUN apk add --no-cache nodejs npm bash
RUN npm install --global webpack webpack-cli mini-css-extract-plugin cssnano css-loader \
    postcss-loader sass-loader sass tachyons-sass postcss-preset-env
