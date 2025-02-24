---
title: "Kubernetes"
weight: 20100
---

Installing simplyblock into and using it with Kubernetes requires two or more components to be installed. The number
of components depends on your deployment strategy and requirements.

For Kubernetes-related installations, simplyblock provides three deployment models: [hyper-converged (also known as
co-located)](../../architecture/concepts/hyper-converged/), [disaggregated](../../architecture/concepts/disaggregated/),
and a hybrid model which combines the best of the former two.

## Prerequisites

Before starting with the installation of simplyblock, make yourself familiar with the requirements and prerequisites
of simplyblock. You can find all necessary information under the [Prerequisites](prerequisites) section specific to Kubernetes
deployments.

## Installation

After making sure that all requirements are fulfilled, you can start with the installation. Follow the necessary
section depending on your chosen deployment model:

- [Hyper-Converged Setup](install-simplyblock/hyper-converged/)
- [Disaggregated Setup](install-simplyblock/disaggregated/)
- [Hybrid Setup](install-simplyblock/hybrid/)

In either case, you start with installing the management plane, before going over to the actual storage cluster and
the Kubernetes CSI driver.

As a last step, you may want to install caching nodes on your Kubernetes workers to improve access latency. See the
installation steps in the [Install Caching Nodes](install-caching-nodes/) section.
