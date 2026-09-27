---
title: "Deployment Topologies"
description: "How simplyblock places its control plane, operator, and storage nodes: local or hub-based management combined with HCI, disaggregated, or hybrid storage."
weight: 20250
---

A simplyblock deployment is described by two independent decisions. The first decides where the control plane and
the Simplyblock Operator run, which defines the management scope and the blast radius of a management failure. The
second decides where the storage nodes run relative to the application workloads, which defines data locality,
scaling, and the lifecycle coupling between storage and compute.

## Two Independent Dimensions

The placement of the control plane and operator is orthogonal to the placement of the storage nodes. Any storage
topology can be combined with either management topology.

| Dimension                  | Options                                                           | Decides                                                                              |
|----------------------------|-------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Control plane and operator | Local on each Kubernetes cluster, or centralized on a hub cluster | Management scope, isolation, upgrade independence, footprint on the managed clusters |
| Storage placement          | Hyper-converged (HCI), disaggregated, or hybrid                   | Data locality, independent scaling of compute and storage, maintenance coupling      |

For example, a set of small edge clusters can run hyper-converged storage while being managed from a central hub,
and a large datacenter cluster can run disaggregated storage with its own local control plane.

## Control Plane and Operator Placement

- **Local:** Every Kubernetes cluster runs its own control plane and Simplyblock Operator. This is the model that is
  available today.
- **Hub:** A hub (management) cluster runs the operator and the control plane centrally, and the managed clusters
  only run lightweight agents, the CSI driver, and the storage nodes. The hub model is coming soon.

The details and a comparison are in [Control Plane and Operator](control-plane-and-operator.md).

## Storage Placement

- **Hyper-converged (HCI):** Storage nodes run on the same Kubernetes workers as the applications. See
  [HCI (Hyper-Converged)](hci.md).
- **Disaggregated:** Storage nodes run on dedicated workers or in a dedicated storage cluster, and applications
  access them over NVMe-oF. See [Disaggregated](disaggregated.md).
- **Hybrid:** Some workers host both storage and applications, while others are storage-only or compute-only. The
  hybrid model is a matter of node selection and does not require a different installation.

## Relation to Disaster Recovery

Disaster recovery adds a hub cluster that coordinates several site clusters. The DR hub is independent of the
management topology described here, but the same hub cluster can also host the centralized simplyblock control plane
once that is available. The supported combinations are shown in
[Deployment Architectures](../../deployment-preparation/deployment-architectures.md).

## Pages in This Section

- [Control Plane and Operator](control-plane-and-operator.md)
- [HCI (Hyper-Converged)](hci.md)
- [Disaggregated](disaggregated.md)
