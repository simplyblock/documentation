---
title: "Cluster Health"
weight: 30200
---

A simplyblock cluster consists of interconnected management nodes (control plane) and storage nodes (storage plane)
working together to deliver a resilient, distributed storage platform. Monitoring the overall health, availability, and
performance of the cluster is essential for ensuring data integrity, fault tolerance, and optimal operation under
varying workloads. Simplyblock provides detailed metrics and status indicators at both the node and cluster level to
help administrators proactively detect issues and maintain system stability.

## Accessing Cluster Status

To access a cluster's status, the `sbcli-pre` command line tool can be used:

```bash title="Accessing the status of a cluster"
sbcli cluster status <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/cluster.md#shows-a-clusters-status).

## Accessing Cluster Statistics 

To access a cluster's performance and I/O statistics, the `sbcli` command line tool can be used:

```bash title="Accessing the statistics of a cluster"
sbcli cluster show <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/cluster.md#shows-a-clusters-statistics).

The information is also available through Grafana in the cluster's dashboard.

## Accessing Cluster I/O Statistics 

To access a cluster's performance and I/O statistics, the `sbcli` command line tool can be used:

```bash title="Accessing the I/O statistics of a cluster"
sbcli cluster get-io-stats <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/cluster.md#gets-a-clusters-io-statistics).

The information is also available through Grafana in the cluster's dashboard.

## Accessing Cluster Capacity Information

To access a cluster's capacity information, the `sbcli` command line tool can be used:

```bash title="Accessing the capcity information of a cluster"
sbcli cluster get-capacity <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/cluster.md#gets-a-clusters-capacity).

## Accessing Cluster Health Information

To access a cluster's health status, the `sbcli` command line tool can be used:

```bash title="Accessing the health status of a cluster"
sbcli cluster check <CLUSTER_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/cluster.md#checks-a-clusters-health).
