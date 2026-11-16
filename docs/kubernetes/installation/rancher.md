---
title: "SUSE Rancher and RKE2"
description: "Installing simplyblock into RKE2 or K3s clusters managed by SUSE Rancher, including the permissions required on CIS-hardened clusters."
weight: 40150
---

[SUSE Rancher](https://www.rancher.com/){:target="_blank" rel="noopener"} (Rancher Manager, Rancher Prime) is a
management plane for Kubernetes clusters and not a Kubernetes distribution of its own. Simplyblock is installed into a
downstream cluster managed by Rancher, never into the Rancher management cluster.

A Rancher-based deployment is made up of three layers, and the simplyblock requirements differ per layer:

| Layer                   | Examples                                                                                                                | Simplyblock requirements                    |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| Management plane        | Rancher Manager, Rancher Prime                                                                                          | None                                        |
| Kubernetes distribution | [RKE2](https://docs.rke2.io/){:target="_blank" rel="noopener"}, [K3s](https://k3s.io/){:target="_blank" rel="noopener"} | Privileged permissions on hardened clusters |
| Worker node OS          | SUSE Linux Enterprise, SUSE Linux Micro, RHEL, Ubuntu                                                                   | Supported Linux distribution                |

!!! info
    Not all worker nodes of a downstream cluster have to host storage components.
    The `ClusterDeploymentConfig` lists the workers that participate in the storage cluster.
    Storage workloads can be isolated on dedicated worker nodes or node pools.

## Prerequisites

The downstream cluster has to be operational, and cluster administrator privileges are required. `kubectl` is
configured against the downstream cluster with the kubeconfig provided by the Rancher UI, not with the kubeconfig of
the management cluster.

The cluster and its worker nodes have to meet the general simplyblock requirements:

- [Software Requirements](../../deployment-preparation/software-requirements.md)
- [Hardware Requirements](../../deployment-preparation/hardware-requirements.md)
- [Supported Linux Distributions](../../reference/supported-linux-distributions.md#kubernetes-hyper-converged-control-plane-and-storage-plane)

## Required Permissions

The Simplyblock CSI driver connects NVMe over Fabrics devices, formats them, and mounts them. Therefore, it runs as a
privileged container.

By default, RKE2 ships a Pod Security Admission configuration that enforces the `privileged` standard cluster-wide, and
nothing else has to be granted. On a cluster provisioned with the CIS hardening profile, the `restricted` standard is
enforced instead, and only the RKE2 system namespaces are exempted from it. The simplyblock namespace therefore has to
be labeled with the exemptions itself.

```yaml title="Example of the simplyblock namespace with privileged exemptions (simplyblock-namespace.yaml)"
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

```bash title="Creating the simplyblock namespace with the privileged exemptions"
kubectl apply -f simplyblock-namespace.yaml
```

The namespace is created before the operator is installed. Otherwise, the Helm chart creates an unlabeled namespace of
its own, and the exemptions never take effect.

## Dedicated CPUs for Storage Nodes

By default, a storage node on RKE2 or K3s runs without the kubelet CPU topology configuration. The storage engine
pins its threads to CPUs, but those CPUs stay available to other pods. With `enableCpuTopology`, the kubelet of each
storage worker is configured for static CPU management, and the storage node pod receives CPUs of its own.

The kubelet configuration is applied by simplyblock itself when a storage node is added. The cluster definition of
RKE2 or K3s stays untouched.

| Kubelet Setting             | Value              | Purpose                                                                          |
|-----------------------------|--------------------|----------------------------------------------------------------------------------|
| `cpuManagerPolicy`          | `static`           | Assigns exclusive CPUs to the storage node pod                                   |
| `cpuManagerReconcilePeriod` | `5s`               | Interval at which the kubelet reapplies the CPU assignment                       |
| `topologyManagerPolicy`     | `single-numa-node` | Keeps the CPUs of the pod on one NUMA node                                       |
| `topologyManagerScope`      | `pod`              | Aligns the containers of the pod together                                        |
| `reservedSystemCPUs`        | `0,1` by default   | CPUs kept for the host and the kubelet, and never assigned to the storage engine |

### How the Kubelet Is Configured

RKE2 and K3s write the kubelet configuration themselves, as a drop-in file in a directory below their data directory,
and write it again at every start. The settings of simplyblock are therefore stored in a second drop-in file,
`99-simplyblock-cpu-topology.conf`, which is left in place by RKE2 and K3s.

| Distribution | Drop-In Directory                                | Restarted Service                          |
|--------------|--------------------------------------------------|--------------------------------------------|
| RKE2         | `/var/lib/rancher/rke2/agent/etc/kubelet.conf.d` | `rke2-agent`, or `rke2-server` on a server |
| K3s          | `/var/lib/rancher/k3s/agent/etc/kubelet.conf.d`  | `k3s-agent`, or `k3s` on a server          |

A data directory that was moved with `--data-dir` is followed. After the file is written, the service that runs the
kubelet is restarted once, by which the kubelet is restarted as well. Running pods are not stopped by that restart. On
a server node, the same service also runs the API server, so storage nodes are best placed on agent nodes.

If the kubelet does not come back with the new settings, the drop-in file is removed, the service is restarted again,
and the storage node is not added.

!!! warning
    A K3s release that keeps no drop-in directory takes kubelet settings only as `kubelet-arg` entries of its own
    configuration. The storage node is then refused with a message that names the arguments to set. They are set in
    the K3s configuration, and the storage cluster is deployed with `enableKubeletConfiguration: false`.

### Enabling the CPU Topology

The discovery writes a draft whose environment leaves the CPU topology off. Only a `Vanilla` draft states the two
settings itself, so the environment is changed before the draft is approved.

```bash title="Enabling the CPU topology in the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge -p '{
  "spec": {
    "environment": "Vanilla",
    "cluster": {"enableCpuTopology": true, "enableKubeletConfiguration": true}
  }
}'
```

| Field on `spec.cluster`      | Purpose                                                                                                         |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `enableCpuTopology`          | Enables topology-aware CPU assignment on storage nodes                                                          |
| `enableKubeletConfiguration` | Lets the storage nodes apply the kubelet CPU topology configuration. Set to `false` if it is already configured |

`reservedSystemCPU` is set per group of a node set, as described under
[Create a Storage Cluster](k8s-storage-plane.md). It names both hardware threads of each reserved core. Otherwise, the
storage engine receives the sibling thread and shares a physical core with the host. The siblings of a CPU are read on
the host:

```bash title="Reading the sibling threads of CPU 0"
cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list
```

After the storage cluster is active, the storage node pods belong to the `Guaranteed` class, which is what the kubelet
assigns exclusive CPUs to.

```bash title="Checking the class of the storage node pods"
kubectl -n simplyblock get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass | grep snode-spdk-pod
```

The Helm values `storagenode.enableCpuTopology`, `storagenode.isolateCores`, `storagenode.skipKubeletConfiguration`,
and `storagenode.reservedSystemCpu` of earlier releases no longer exist. For the full list of `storageNodes` fields,
see [Simplyblock Operator](../../reference/operator/index.md).

## SUSE Linux Micro Nodes

[SUSE Linux Micro](https://www.suse.com/products/micro/){:target="_blank" rel="noopener"} (SL Micro, formerly SLE Micro)
is supported as a worker node operating system and needs no image customization. Huge pages are allocated by
simplyblock automatically, and `/etc` is writable, so configuration drop-ins are applied directly.

Additional packages cannot be installed in place, because the root filesystem is read-only. Such a change is applied
with `transactional-update` and takes effect after a reboot.

## Installation of Simplyblock

To install the simplyblock components on a Rancher-managed cluster, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and to [create a storage cluster](k8s-storage-plane.md).
