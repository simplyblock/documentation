FROM squidfunk/mkdocs-material
RUN pip install mkdocs-git-revision-date-localized-plugin
RUN pip install "mkdocs-material[imaging]"
RUN pip install mkdocs-nav-weight
RUN pip install mkdocs-glightbox
RUN pip install mike
RUN pip install mkdocs-video