---
title: "Kubernetes"
weight: 20100
---

Installing simplyblock into and using it with Kubernetes requires two or more components to be installed. The number
of components depends on your deployment strategy and requirements.

For Kubernetes-related installations, simplyblock provides three deployment models: [hyper-converged (also known as
co-located)](../../architecture/concepts/hyper-converged.md),
[disaggregated](../../architecture/concepts/disaggregated.md), and a hybrid model which combines the best of the former
two.

## Prerequisites

Before starting with the installation of simplyblock, make yourself familiar with the requirements and prerequisites
of simplyblock. You can find all necessary information under the [Prerequisites](prerequisites.md) section specific to
Kubernetes deployments.

## Installation

After making sure that all requirements are fulfilled, you can start with the installation. Follow the necessary
section depending on your chosen deployment model:

- [Hyper-Converged Setup](install-simplyblock/hyper-converged.md)
- [Disaggregated Setup](install-simplyblock/disaggregated.md)
- [Hybrid Setup](install-simplyblock/hybrid.md)

In either case, you start with installing the control plane, before going over to the actual storage cluster and
the Kubernetes CSI driver.

As a last step, you may want to install caching nodes on your Kubernetes workers to improve access latency. See the
installation steps in the [Install Caching Nodes](install-caching-nodes.md) section.
