---
title: "CPU Assignment for Storage Nodes"
weight: 30350
---

Simplyblock storage nodes use SPDK for high-performance, user-space storage operations. SPDK requires dedicated CPU
cores to achieve low-latency, predictable I/O processing. Simplyblock provides two methods for assigning CPU cores
to storage nodes: **core isolation** and **CPU topology manager**.

## Core Isolation (Traditional Method)

Core isolation is the original method for dedicating CPU cores to SPDK. It works by reserving a set of cores at the
OS level, preventing the Linux scheduler from placing other workloads on those cores.

Core isolation is configured during storage node setup:

```bash title="Configure storage node with core isolation"
{{ cliname }} storage-node deploy --isolate-cores --ifname=<IFNAME>
```

Or with a specific percentage of cores:

```bash title="Specify core percentage"
{{ cliname }} storage-node deploy --isolate-cores --core-percentage=80
```

Core isolation can also be specified as a hexadecimal CPU mask:

```bash title="Specify explicit core mask"
{{ cliname }} storage-node deploy --core-mask=0xFF00
```

Core isolation is suitable for bare-metal and virtualized Linux deployments where simplyblock has direct control over
the host's CPU configuration.

## CPU Topology Manager (Kubernetes Method)

For Kubernetes deployments, simplyblock supports CPU assignment via the Kubernetes **CPU topology manager**. This
method uses Kubernetes-native CPU management instead of OS-level core isolation, enabling better integration with
the Kubernetes scheduler and other workloads.

When enabled, simplyblock configures the kubelet on each storage node with:

- **`cpuManagerPolicy: static`** -- Kubernetes assigns exclusive CPUs to pods that request integer CPU amounts.
- **`topologyManagerPolicy: single-numa-node`** -- Ensures all resources (CPU, memory, devices) for a pod are
  allocated from the same NUMA node.
- **`topologyManagerScope: pod`** -- Topology alignment is enforced at the pod level.

This ensures that SPDK pods receive dedicated CPU cores on the correct NUMA node, with guaranteed locality to their
NVMe devices and network interfaces.

### Enabling CPU Topology Manager

In the Helm chart:

```bash title="Deploy with CPU topology manager"
helm install simplyblock simplyblock-csi/spdk-csi \
    --set storagenode.create=true \
    --set storagenode.enableCpuTopology=true \
    ...
```

In the Kubernetes operator (`SimplyBlockStorageNode` CRD):

```yaml title="Storage node with CPU topology"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageNode
metadata:
  name: storage-nodes
spec:
  clusterName: prod-cluster
  workerNodes:
    - worker-1
    - worker-2
  coreIsolation: false
```

When `enableCpuTopology` is set (Helm) or the operator detects a Kubernetes environment, the system deploys a
preparation DaemonSet that configures the kubelet on each storage worker node and restarts it. This is a one-time
operation, marked by a flag file to prevent repeated restarts.

### NUMA Resource Plugin

When using CPU topology manager, an optional **NUMA resource plugin** can be deployed alongside:

```bash title="Enable NUMA device plugin"
helm install simplyblock simplyblock-csi/spdk-csi \
    --set storagenode.create=true \
    --set storagenode.enableCpuTopology=true \
    --set storagenode.enableDevicePlugin=true \
    ...
```

The NUMA resource plugin runs as a DaemonSet on storage nodes and exposes NUMA node capacity as a Kubernetes
extended resource. This allows the Kubernetes scheduler to make NUMA-aware placement decisions for storage pods.

### OpenShift Support

On OpenShift clusters, the CPU topology configuration uses `MachineConfig` and `KubeletConfig` custom resources
instead of direct kubelet configuration. Simplyblock automatically detects the OpenShift environment and uses the
appropriate method.

## Choosing Between Methods

| Criterion                  | Core Isolation              | CPU Topology Manager           |
|----------------------------|-----------------------------|--------------------------------|
| **Platform**              | Bare metal, VMs, Kubernetes  | Kubernetes only                |
| **Integration**           | OS-level (cgroups/isolcpus)  | Kubernetes scheduler-native    |
| **NUMA awareness**        | Manual (via core mask)       | Automatic (topology manager)   |
| **Co-location**           | Requires manual planning     | Kubernetes handles scheduling  |
| **OpenShift support**     | Requires manual config       | Automatic via MachineConfig    |
| **Kubelet restart**       | Not required                 | One-time restart on setup      |

For Kubernetes deployments, the CPU topology manager is recommended as it integrates with the Kubernetes scheduler's
resource management and NUMA topology awareness.
