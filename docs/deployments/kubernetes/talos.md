---
title: "Talos"
weight: 40200
---
[Talos Linux](https://www.talos.dev/) is a minimal Linux distribution optimized for Kubernetes. Built as an immutable
distribution image, it provides a minimal attack surface but requires some changes to the image to run simplyblock.

Simplyblock requires a set of additional Linux kernel modules, as well as tools being available in the Talos image.
That means that a custom Talos image has to be built to run simplyblock. The following section explains the required
changes to make Talos compliant.


## Required Kernel Modules (Worker Node)
On Kubernetes worker nodes, simplyblock requires a few kernel modules to be loaded.

```yaml title="Content of kernel-module-config.yaml"
machine:
  kernel:
    modules:
      - name: nbd 
      - name: uio_pci_generic
      - name: vfio_pci
      - name: vfio_iommu_type1
```

## Huge Pages Reservations

Simplyblock requires huge pages memory to operate. The storage engine expects to find huge pages of 2 MiB page size. The
required amount of huge pages depends on a number of factors.

After installing the Kubernetes control plane, you can calculate the required huge pages from the admin control pod (see the [Kubernetes Control Plane installation guide](./k8s-control-plane.md) for how to find and exec into the pod).

Run the following command on the admin control pod to calculate the huge pages required on the host:

```bash title="Run the huge memory calculator"
sbctl storage-node configure --calculate-hp-only --max-lvol <MAX_LVOL> --number-of-devices <NUMBER_OF_DEVICES>
```
The following flags also affect the huge page calculation:

- `--nodes-per-socket (default: 1)`
- `--sockets-to-use (default: 0)`
- `--cores-percentage (default: 0 / unset)`

```bash title="Example output of huge pages calculator
demo@demo ~> sbctl storage-node configure --calculate-hp-only --max-lvol 10 --number-of-devices 4
2026-02-22 22:27:47,017: 140705369632256: INFO: The minimum required huge pages on this host is: 11552 MB
True
```

To apply the change to Talos' worker nodes, a YAML configuration file with the following content is required. The number
of pages is to be replaced with the number calculated above.

```yaml title="Content of huge-pages-config.yaml"
machine:
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

Simyplyblock's CSI driver requires connecting NVMe over Fabrics devices, as well as mounting and formatting them.
Therefore, the CSI driver has to run as a privileged container. Hence, Talos must be configured to start the
simplyblock's CSI driver in privileged mode. 

Talos allows overriding the pod security admission settings at a Kubernetes namespace level. To enable privileged mode
and grant the required access to the simplyblock CSI driver, a specific simplyblock namespace with the appropriate
security exemptions must be created:

```yaml title="Content of simplyblock-namespace.yaml"
apiVersion: v1
kind: Namespace
metadata:
  name: simplyblock
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/audit-version: latest
    pod-security.kubernetes.io/warn: privileged
    pod-security.kubernetes.io/warn-version: latest
```

To enable the required permissions, apply the namespace configuration using `kubectl`.

```bash title="Enabled privileged mode for simplyblock"
demo@demo ~> kubectl apply -f simplyblock-namespace.yaml
```
