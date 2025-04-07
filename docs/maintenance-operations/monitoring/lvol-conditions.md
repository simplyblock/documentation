---
title: "Logical Volume Conditions"
weight: 30100
---

Logical volumes are the core storage abstraction in simplyblock, representing high-performance, distributed NVMe
block devices backed by the cluster. Maintaining visibility into the health, status, and performance of these volumes is
critical for ensuring workload reliability, troubleshooting issues, and planning resource utilization. Simplyblock
continuously monitors volume-level metrics and exposes them through both CLI and observability tools, giving operators
detailed insight into system behavior.

## Accessing Logical Volume Statistics 

To access a logical volume's performance and I/O statistics, the `sbcli-pre` command line tool can be used:

```bash title="Accessing the statistics of a logical volume"
sbcli-pre volume get-io-stats <VOLUME_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/volume.md#gets-a-logical-volumes-io-statistics).

The information is also available through Grafana in the logical volume's dashboard.

## Accessing Logical Volume Health Information

To access a logical volume's health status, the `sbcli-pre` command line tool can be used:

```bash title="Accessing the health status of a logical volume"
sbcli-pre volume check <VOLUME_ID>
```

All details of the command are available in the
[CLI reference](../../reference/cli/volume.md#checks-a-logical-volumes-health).
