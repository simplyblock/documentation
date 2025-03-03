# Simplyblock Documentation

This repository contains the simplyblock documentation. It is built using [mkdocs](https://www.mkdocs.org/) and
uses a provided shell script `doc-builder.sh` to ease the process of working with it.

## Docs Builder

The `doc-builder.sh` tool uses Docker and a customized mkdocs Docker image to serve and build the documentation. The
image contains all required plugins.

When using `doc-builder.sh` for the first time (and ideally after an update of the Git repository), the Docker image
needs to be built using:

```bash
./doc-builder.sh build-image
```

### Serving Content Locally

When building or updating the documentation, it is useful to have a local builder with live updating. Mkdocs supports
this, as does the `doc-builder.sh`. To simplify the process of working with mkdocs, there is a command to start the
local builder:

```bash
./doc-builder.sh serve
```

### Building a Static Version of the Documentation

To test a fully built, static version of the current documentation, the docs can be built into the `./site` directory.
This version can be used independently and deployed by dropping it into any webserver that is able to serve static
content.

To build the static version, use the following command:

```bash
./doc-builder.sh build
```

### Preparing the Deployment of a New Version

Since the documentation system supports the deployment and management of multiple versions, previous and current
versions are collected in the `./deployment/` folder. The symlinks are automatically updated according to the newest
version, as is the `versions.json` file.

To simplify the process of a new version deployment of the documentation, the `doc-builder.sh` provides the necessary
command.

```bash
./doc-builder.sh deploy {version-name}
```

The given _version-name_ will be used as a directory name and name of the version in the dropdown selector. Hence, it
is recommended that it only contains lowercase letters, numbers, and underscores or dashes.
