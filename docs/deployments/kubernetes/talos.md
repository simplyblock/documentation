---
title: Talos Prerequisites
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
demo@demo ~> docker run --rm -t \
    -v $PWD/_out:/out ghcr.io/siderolabs/imager:v1.9.2 iso \
    --system-extension-image ghcr.io/siderolabs/nvme-cli:v2.11
    --system-extension-image ghcr.io/siderolabs/util-linux-tools:2.40.4
```

## Required Kernel Modules (Worker Node)


## Huge Pages Reservations

Simplyblock requires huge pages memory to operate. The storage engine expects to find huge pages of 2 MiB page size. The
required amount of huge pages depends on a number of factors. To calculate the number of required huge pages,
simplyblock provides a [Huge Pages Calculator](../../reference/huge-pages-calculator.md).

!!! info
    The number of huge pages calculated by the huge pages calculator is the minimum required number. A higher number of
    huge pages can always be allocated. The storage engine, however, will refuse to start up without the required number
    of huge pages.

To apply the change to Talos' worker nodes, a YAML configuration file with the following content is required. The number
of pages is to be replaced with the number calculated above.

```yaml title="Content of huge-pages-config.yaml"
sysctls:
   vm.nr_hugepages: "<number-of-pages>"
```

To activate the huge pages, the `talosctl` command should be used.

```bash title="Enable Huge Pages in Talos"
demo@demo ~> talosctl apply-config --nodes <worker_node_ip> \
    --file huge-pages-config.yaml -m reboot
demo@demo ~> talosctl service kubelet restart --nodes <worker_node_ip>
```

## Required Talos Permissions

Simyplyblock's CSI Driver requires to connect NVMe over Fabrics devices, as well as mount and format them. Therefore,
the CSI Driver has to run as a privileged container. Hence, Talos needs to be configured to start the Simplyblock CSI
Driver in privileged mode. 

To enable privileged mode and grant the required access, the following YAML configuration has to be applied to all Talos
worker nodes which will have the Simplyblock CSI Driver installed:

```yaml title="Content of required-permissions.yaml"
admissionControl:
  - name: PodSecurity # Name is the name of the admission controller.
    # Configuration is an embedded configuration object to be used as the plugin's
    configuration:
      apiVersion: pod-security.admission.config.k8s.io/v1alpha1
      defaults:
        audit: privileged
        audit-version: latest
        enforce: privileged
        enforce-version: latest
        warn: privileged
        warn-version: latest
      exemptions:
        namespaces:
          - kube-system
        runtimeClasses: []
        usernames: []
```

To enable the required permisions, the `talosctl` command should be used.

```bash title="Enabled Simplyblock Required Permissions in Talos"
demo@demo ~> talosctl apply-config --nodes <worker_node_ip> \
    --file required-permissions.yaml.yaml -m reboot
demo@demo ~> talosctl service kubelet restart --nodes <worker_node_ip>
```

