---
title: "Cluster Health"
description: "Cluster Health: A simplyblock cluster consists of interconnected management nodes (control plane) and storage nodes (storage plane) working together to deliver."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/monitoring/cluster-health/"
---

# Cluster Health

A simplyblock cluster consists of interconnected management nodes (control plane) and storage nodes (storage plane)
working together to deliver a resilient, distributed storage platform. Monitoring the overall health, availability, and
performance of the cluster is essential for ensuring data integrity, fault tolerance, and optimal operation under
varying workloads. Simplyblock provides detailed metrics and status indicators at both the node and cluster levels to
help administrators proactively detect issues and maintain system stability.

## Accessing Cluster Status

To access a cluster's status, the `sbctl` command line tool can be used:

```bash title="Accessing the status of a cluster"
sbctl cluster status <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../../reference/cli/index.md).

## Accessing Cluster Statistics

To access a cluster's performance and I/O statistics, the `sbctl` command line tool can be used:

```bash title="Accessing the statistics of a cluster"
sbctl cluster show <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../../reference/cli/index.md).

The information is also available through Grafana in the cluster's dashboard.

## Accessing Cluster I/O Statistics

To access a cluster's performance and I/O statistics, the `sbctl` command line tool can be used:

```bash title="Accessing the I/O statistics of a cluster"
sbctl cluster get-io-stats <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../../reference/cli/index.md).

The information is also available through Grafana in the cluster's dashboard.

## Accessing Cluster Capacity Information

To access a cluster's capacity information, the `sbctl` command line tool can be used:

```bash title="Accessing the capacity information of a cluster"
sbctl cluster get-capacity <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../../reference/cli/index.md).

## Accessing Cluster Health Information

To access a cluster's health status, the `sbctl` command line tool can be used:

```bash title="Accessing the health status of a cluster"
sbctl cluster check <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../../reference/cli/index.md).
