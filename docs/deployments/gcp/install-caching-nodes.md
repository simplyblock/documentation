---
title: "Install Caching Nodes (Kubernetes)"
weight: 30300
---

Caching nodes are simplyblock storage containers co-located with the workloads on Kubernetes workers. They utilize
directly attached NVMe disks on the worker nodes to provide an ultra-low-latency write-through cache for disaggregated
or hybrid simplyblock clusters.

## Prerequisites

| Service                     | Direction | Source / Target Network | Port(s) | Protocol(s) |
|-----------------------------|-----------|-------------------------|---------|-------------|
| ICMP                        | ingress   | control                 | -       | ICMP        |
| Cluster Control             | ingress   | control                 | 5000    | TCP         |
| spdk-http-proxy             | ingress   | storage, control        | 8080    | TCP         |
| SSH                         | ingress   | storage, control, admin | 22      | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375    | TCP         |
|                             |           |                         |         |             |
| FoundationDB                | egress    | storage                 | 4500    | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375    | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377    | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789    | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946    | TCP / UDP   |
| Graylog                     | egress    | control                 | 12202   | TCP         |

Caching nodes, like storage nodes, require huge page memory to hold the internal state. Huge pages should be 2MiB in
size, and a minimum of 4096 huge pages should be allocated at boot time of the operating system.

```bash
demo@worker-1 ~> sudo sysctl -w vm.nr_hugepages=4096
```

!!! info
To see how huge pages can be pre-reserved at boot time, see the node sizing documentation section on  
[Huge Pages](../deployment-planning/node-sizing.md#memory-requirements).

```bash
demo@worker-1 ~> sudo systemctl restart kubelet
```

```bash
demo@worker-1 ~> kubectl describe node worker-1.kubernetes-cluster.local | grep hugepages-2Mi
```

```plain
demo@demo ~> kubectl describe node worker-1.kubernetes-cluster.local | grep hugepages-2Mi
  hugepages-2Mi:      9440Mi
  hugepages-2Mi:      9440Mi
  hugepages-2Mi      0 (0%)    0 (0%)
```

```bash
demo@worker-1 ~> sudo yum install -y nvme-cli
demo@worker-1 ~> sudo modprobe nvme-tcp
demo@worker-1 ~> sudo modprobe nbd
```

```bash
demo@demo ~> kubectl label nodes worker-1.kubernetes-cluster.local type=simplyblock-cache
```

Afterward, the worker node can be described to check that the node-selector type is successfully set.

```plain title="Example output of a successfully configured worker node"
demo@demo ~> kubectl describe node worker-1.kubernetes-cluster.local | grep simplyblock-cache
                    type=simplyblock-cache
```

```yaml title="Example Caching Node-enabled StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  type: cache
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
```
