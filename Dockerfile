FROM squidfunk/mkdocs-material:9.6.5
RUN pip install mkdocs-git-revision-date-localized-plugin "mkdocs-material[imaging]" \
    mkdocs-nav-weight mkdocs-glightbox mike mkdocs-video mkdocs-meta-descriptions-plugin \
    markdown-captions jinja2 mkdocs-link-marker mkdocs-markdownextradata-plugin
