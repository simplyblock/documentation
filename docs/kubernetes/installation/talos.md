---
title: "Talos"
description: "Run simplyblock on Talos Linux: required kernel modules, huge pages, CPU topology, privileged namespace, and the Talos environment setting."
weight: 40200
---

[Talos Linux](https://www.talos.dev/){:target="_blank" rel="noopener"} is a minimal Linux distribution optimized for Kubernetes. Built as an immutable
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

## Huge Pages and the Kubelet: Two Modes

Simplyblock requires huge pages memory to operate (2 MiB pages) and, for the highest performance, a kubelet that runs
the static CPU manager with a single-NUMA-node topology manager. On other distributions the storage node prepares its
worker itself. The Talos host is immutable and has no shell, so both settings live in the **machine config**, and
there are two ways to get them there. The deployment document picks one with `spec.cluster.talosMachineConfig`:

| Mode | `talosMachineConfig` | Who writes the machine config | Talos API access from the cluster |
|------|----------------------|-------------------------------|-----------------------------------|
| Pre-provisioned (**default**) | `Preprovisioned` or unset | You, before the storage nodes are added | Not needed |
| Managed | `Managed` | The storage node, through the Talos API, while it is added | Required (see below) |

```yaml title="Choosing the mode in the ClusterDeploymentConfig"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
spec:
  environment: Talos
  cluster:
    name: mycluster
    talosMachineConfig: Preprovisioned   # Preprovisioned (default) | Managed
    enableCpuTopology: true              # default true on Talos
    enableKubeletConfiguration: true     # default true on Talos
```

The field is accepted only when `spec.environment` is `Talos`. A document written by the operator's discovery run
states none of the three fields, which gives a pre-provisioned cluster with the kubelet included. The mode can be
changed on a running cluster by patching the StorageCluster (`spec.storageNodes.talosMachineConfig`); the storage
nodes pick the new value up on their next add or restart.

In both modes a storage node first reads what its worker already has: the host's huge-page pool, the capacity the
kubelet advertises, and the kubelet's live configuration. A worker that already carries everything is left alone.
The modes differ only in what happens when something is missing. The huge pages are always part of this; the
kubelet's CPU topology is part of it only when `enableCpuTopology` and `enableKubeletConfiguration` are both on, which
a Talos document turns on by default.

### Pre-provisioned (default)

The storage node applies nothing. If the pool or the kubelet settings are short, adding the node fails and the storage
node's log carries the exact machine-config patch to apply, sized for that worker. The operator retries the add on its
own once the patch is in.

```plain title="A refusal in the storage node's log"
Talos node 'worker-3': host provides 4000 MiB of huge pages but the SPDK pod requests 6088 MiB (hugepages-2Mi),
i.e. at least 3044 2 MiB pages, and the machine config is pre-provisioned (TALOS_MACHINE_CONFIG=preprovisioned).
Save the YAML below as patch.yaml and apply it to the worker with 'talosctl -n <node ip> patch mc -p @patch.yaml',
then restart its kubelet with 'talosctl -n <node ip> service kubelet restart' so it advertises the pool, or set
storageNodes.talosMachineConfig: Managed on the StorageCluster to let the node apply it through the Talos API:
machine:
  sysfs:
    devices.system.node.node0.hugepages.hugepages-2048kB.nr_hugepages: '3423'
```

The file is the lines from `machine:` to the end, nothing else:

```yaml title="Content of patch.yaml"
machine:
  sysfs:
    devices.system.node.node0.hugepages.hugepages-2048kB.nr_hugepages: '3423'
```

```bash title="Apply the patch and restart the kubelet"
[demo@demo ~]# talosctl patch mc --nodes <WORKER_NODE_IP> --mode=no-reboot --patch @patch.yaml
[demo@demo ~]# talosctl service kubelet restart --nodes <WORKER_NODE_IP>
```

No reboot is needed: the pool is applied live, and the kubelet restart makes it advertise the new capacity. The
count is simplyblock's own sizing for that worker and replaces the key's value; a pool the worker keeps for another
consumer has to be added to it by hand, since the node only verifies that the total covers its request.

To put the whole fleet in place before adding any node, use the same `machine.sysfs` key with one entry per NUMA
node that will host a storage node, and the kubelet settings below, in each worker's machine config at install
time. One way to size a fleet of identical workers is to add the first worker without the patch and read the numbers
off the refusal. A pool reserved through `machine.sysctls` `vm.nr_hugepages` is honoured as well, as long as it
covers the request; do not set both.

```yaml title="Content of enable-cpu-topology.yaml"
machine:
  kubelet:
    extraConfig:
      cpuManagerPolicy: static
      reservedSystemCPUs: "0,1"
      topologyManagerPolicy: single-numa-node
      topologyManagerScope: pod
```

`reservedSystemCPUs` must match the cluster's `reservedSystemCPU` (default `0,1`): the storage node compares the
kubelet's live configuration against it. Talos restarts the kubelet itself when `extraConfig` changes. A kubelet that
previously ran under another CPU-manager policy refuses to start over its checkpoint; put the `extraConfig` block in
the machine config before the worker's first boot, or remove `/var/lib/kubelet/cpu_manager_state` on the worker first
(a privileged pod with that path mounted, since the host has no shell).

### Managed

With `talosMachineConfig: Managed` the storage node writes the same two settings itself, through the Talos API, and
only when they are missing: it reserves the huge pages, restarts the kubelet so it advertises them, and patches the
kubelet's CPU topology. It adds its own pages on top of whatever pool the worker already carries, records that
baseline on the worker, and never shrinks the pool. A worker whose pool was set by hand and is then switched to
Managed should have that pool set to `"0"` first, or the node sizes a second allocation on top of the first.

Managed mode needs the Talos API to be reachable from the simplyblock namespace with the `os:admin` role. This is a
control-plane machine-config change only the cluster's administrator can make:

```yaml title="Talos 1.14 and later: KubeTalosAPIAccessConfig on the control plane nodes"
apiVersion: v1alpha1
kind: KubeTalosAPIAccessConfig
allowedRoles:
  - os:admin
allowedKubernetesNamespaces:
  - simplyblock
```

```yaml title="Earlier Talos: machine.features on the control plane nodes"
machine:
  features:
    kubernetesTalosAPIAccess:
      enabled: true
      allowedRoles:
        - os:admin
      allowedKubernetesNamespaces:
        - simplyblock
```

Then create the ServiceAccount that Talos issues the credentials for, in the simplyblock namespace, before the
storage nodes are added. Talos writes a Secret of the same name next to it:

```yaml title="Content of talos-api-access.yaml"
apiVersion: talos.dev/v1alpha1
kind: ServiceAccount
metadata:
  name: talos-api-access-talos-secrets
  namespace: simplyblock
spec:
  roles:
    - os:admin
```

```bash title="Grant the storage nodes Talos API access"
[demo@demo ~]# kubectl apply -f talos-api-access.yaml
```

Without it, adding a node in Managed mode fails with a message naming the missing Secret.

## Required Talos Permissions

Simplyblock's CSI driver requires connecting NVMe over Fabrics devices, as well as mounting and formatting them.
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
[demo@demo ~]# kubectl apply -f simplyblock-namespace.yaml
```

The namespace is created before the operator is installed. Otherwise, the Helm chart creates an unlabeled namespace of
its own, and the exemptions never take effect.

## Talos Environment

The `ClusterDeploymentConfig` that describes the storage cluster must name the environment `Talos`. Discovery writes
the detected distribution into the draft, but it should be checked during the review:

```yaml title="ClusterDeploymentConfig for Talos (excerpt)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  environment: Talos
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
    talosMachineConfig: Preprovisioned   # or Managed, see above
  nodeSets:
    - name: storage
      groups:
        - name: default
          workers: [worker-1, worker-2, worker-3]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

With `environment: Talos`, the expansion turns `enableCpuTopology` and `enableKubeletConfiguration` on in
`StorageCluster.spec.storageNodes` unless the document states them off, and copies `talosMachineConfig` there
(`Preprovisioned` when unset). The storage nodes then verify or apply the huge pages and the kubelet settings as
described above.

## Installation of Simplyblock

To install the simplyblock components on Talos, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and to [create a storage cluster](k8s-storage-plane.md).
