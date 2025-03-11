---
title: Talos Preparations
weight: 30050
---

[Talos Linux](https://www.talos.dev/) is a minimal Linux distribution optimized for Kubernetes. Built as an immutable
distribution image, it provides minimal attack surface but requires some changes to the image to run simplyblock.

Simplyblock requires a set of additional Linux kernel modules, as well as tools being available in the Talos image.
That means that a custom Talos image has to be built to run simplyblock. The following section explains the required
changes to make Talos compliant.

## Required System Extensions (Worker Node)

On Kubernetes worker nodes, simplyblock requires two additional system extension images to be referenced during the
build process or to be installed manually after deployment.

The required system extension image references are:

- ghcr.io/siderolabs/nvme-cli:v2.11
- ghcr.io/siderolabs/util-linux-tools:2.40.4

```bash title="Adding the required system extension image to Talos"
docker run --rm -t -v $PWD/_out:/out ghcr.io/siderolabs/imager:v1.9.2 iso \
    --system-extension-image ghcr.io/siderolabs/nvme-cli:v2.11
    --system-extension-image ghcr.io/siderolabs/util-linux-tools:2.40.4
```

## Required Kernel Modules (Worker Node)


