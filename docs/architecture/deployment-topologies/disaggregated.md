---
title: "Disaggregated"
description: "Disaggregated simplyblock deployments run storage nodes on dedicated workers or in a dedicated storage cluster, decoupling storage from the compute lifecycle."
weight: 20253
---

In a disaggregated deployment, dedicated storage nodes operate separately from the compute nodes that run the
applications. The storage nodes run either on a dedicated node pool of the same Kubernetes cluster or in a separate
Kubernetes cluster that only provides storage. Applications access their volumes over NVMe-oF (NVMe/TCP or
NVMe/RoCE). Both variants use the same Kubernetes-native operations model through the Simplyblock Operator.

![Disaggregated deployment with a dedicated storage cluster](../../assets/images/architecture/topology-disaggregated.svg)

## How It Works

The storage nodes run on workers that are selected for storage only. The CSI driver runs on the compute workers and
connects each volume to the storage nodes over the network. The main difference from the
[hyper-converged model](hci.md) is the separation of storage and compute resources: no application pods share a
worker with a storage node.

## Benefits

- **Independent scalability:** Compute and storage scale separately, which avoids unnecessary hardware expansion.
  For example, a small compute cluster with I/O-intensive workloads may still require a lot of storage capacity and
  IOPS.
- **Independent lifecycle:** Storage and compute are maintained, upgraded, and replaced independently of each other.
  Worker node upgrades, maintenance, and reboots on the compute side do not affect the storage nodes.
- **Controlled storage performance:** Latency, throughput, and IOPS are easier to control, since storage nodes do not
  compete with application workloads for CPU, memory, or network.
- **Hardware independence:** As with hyper-converged storage, components and nodes can be replaced independently of
  the software, with hardware from different vendors, and in gradual, rolling replacements.

## Considerations

- **No data locality:** Every I/O crosses the network between compute and storage workers.
- **Minimum scale:** The storage cluster has a minimum size of its own, independent of the size of the compute
  cluster.
- **Scaling alignment:** Storage and compute are sized separately, so a change in the compute demand can require a
  separate adjustment of the storage cluster.

## When to Choose Disaggregated

A disaggregated deployment is the preferred choice when:

- Storage capacity or performance needs differ strongly from compute needs.
- Compute workers are upgraded, rebooted, or replaced frequently, and storage should not be affected.
- Storage has to be served to several Kubernetes clusters or to workloads outside the storage cluster.
- Predictable storage performance matters more than data locality.

## Hybrid Deployments

Hyper-converged and disaggregated placement can be combined in one cluster. Some workers run both storage nodes and
applications, while others are storage-only or compute-only. From a deployment perspective, there is no essential
difference between the models: the placement of storage nodes is a question of node selection (which workers are
listed for the storage nodes) only.
