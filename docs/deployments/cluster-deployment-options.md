---
title: Cluster Deployment Options
description: "Cluster Deployment Options: The following options can be set when creating a cluster. This applies to both plain linux and kubernetes deployments."
---

The following options can be set when creating a cluster. This applies to both plain Linux and Kubernetes deployments.
Most cannot be changed later on, so careful planning is recommended.

### ```--enable-node-affinity```

As long as a node is not full (out of capacity), the first chunk
of data is always stored on the local node (the node to which the volume is attached).
This reduces network traffic and latency, particularly for reads, but may lead to an
uneven distribution of capacity within the cluster. Generally, using node affinity accelerates
reads, but leads to higher variability in performance across nodes in the cluster.
It is recommended particularly for 1+1 EC schemas.

### ```--data-chunks-per-stripe, --parity-chunks-per-stripe```

Those two parameters together make up the erasure coding schema of the cluster (e.g. 1+1, 2+2, 4+2). The schema is set
once at cluster creation and applies to all volumes in the cluster. It cannot be configured per volume.

### ```--cap-warn, --cap-crit```

Warning and critical limits for overall cluster utilization. If the warning
limit is exceeded, warnings will be issued in the event log. If the "critical" limit is exceeded,
the cluster will be placed into read-only mode. For large clusters, a 99% "critical" limit is OK. For small
clusters (less than 50 TB), 97% is better.

### ```--prov-cap-warn, --prov-cap-crit```

Warning and critical limits for over-provisioning. Exceeding
these limits will cause entries in the cluster log. If the critical limit is exceeded,
new volumes cannot be provisioned and volumes cannot be enlarged. A limit of 500% is typical.

### ```--log-del-interval```

Number of days for which logs are retained. Log storage can grow significantly, and it is recommended not to keep logs
for longer than one week. This is only relevant if the observability stack is deployed.

### ```--metrics-retention-period```

Number of days for which the I/O statistics and other metrics are retained. The amount of data per day is significant,
so retention should typically be limited to a few days or a week.

### ```--contact-point```

This is a webhook endpoint for alerting on critical events such as storage nodes becoming unreachable.
This is only relevant if the observability stack is deployed.

### ```--fabric```

Choose `tcp`, `rdma`, or both. If both fabrics are chosen, volumes can connect to the cluster
using either option (defined per volume or storage class), but the cluster internally uses `rdma`.

### ```--qpair-count```

The default number of queue pairs (sockets) per volume for an initiator (host) to connect to the
target (server). More queue pairs per volume increase concurrency and volume performance, but require more
server resources (RAM, CPU) and thus limit the total number of volumes per storage node. The default is 3.
If you need a few very performant volumes, increase the amount. If you need a large number of less performant
volumes, decrease it. More than 12 parallel connections have limited impact on overall performance. Also, the
host requires at least one core per queue pair.

### ```--use-backup```

Path to a JSON file with S3 or S3-compatible (MinIO) backup configuration. This enables snapshot-based backup and
recovery for the cluster.

```json title="Example: backup-config.json (AWS S3)"
{
  "access_key_id": "<AWS_ACCESS_KEY>",
  "secret_access_key": "<AWS_SECRET_KEY>",
  "bucket_name": "simplyblock-backups"
}
```

```json title="Example: backup-config.json (MinIO / S3-compatible)"
{
  "access_key_id": "<MINIO_ACCESS_KEY>",
  "secret_access_key": "<MINIO_SECRET_KEY>",
  "bucket_name": "simplyblock-backups",
  "local_endpoint": "http://minio.example.com:9000"
}
```

| Key                  | Description                                                                | Required |
|----------------------|----------------------------------------------------------------------------|----------|
| `access_key_id`      | S3 access key ID.                                                         | Yes      |
| `secret_access_key`  | S3 secret access key.                                                     | Yes      |
| `bucket_name`        | S3 bucket name. Defaults to `simplyblock-backup-<CLUSTER_ID>` if omitted. | No       |
| `local_endpoint`     | Custom S3 endpoint URL for MinIO or other S3-compatible storage.          | No       |
| `with_compression`   | Enable compression for backup data. Default: `false`.                     | No       |
| `snapshot_backups`   | Enable snapshot-based incremental backups. Default: `true`.               | No       |

For more information on backup operations, see [Backup and Recovery](../usage/backup-recovery.md).

### ```--name```

A human-readable name for the cluster.
