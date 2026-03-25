---
title: Cluster Deployment Options
description: "Cluster Deployment Options: The following options can be set when creating a cluster. This applies to both plain linux and kubernetes deployments."
---

The following options can be set when creating a cluster. This applies to both plain linux and kubernetes deployments.
Most cannot be changed later on, so careful planning is recommended.

### ```--enable-node-affinity```

As long as a node is not full (out of capacity), the first chunk 
of data is always stored on the local node (the node to which the volume is attached). 
This reduces network traffic and latency - accelerating particularly the read - but may lead to an
inequal distribution of capacity within the cluster. Generally, using node affinity accelerates
reads, but leads to higher variability in performance across nodes in the cluster.
It is recommended on shared networks and networks below 100gb/s. 

### ```--data-chunks-per-stripe, --parity-chunks-per-stripe```

Those two parameters together make up the default erasure coding schema of the node (e.g. 1+1, 2+2, 4+2). Starting from R25.10, it is also
possible to set individual schemas per volume, but this feature is still in alpha-stage.

### ```--cap-warn, --cap-crit```

Warning and critical limits for overall cluster utilization. The warning 
limit will just cause issuance of warnings in the event log if exceeded, the "critical" limit will 
place the cluster into read-only mode. For large clusters, 99% of "critical" limit is ok, for small
clusters (less than 50TB) better use 97%. 

### ```--prov-cap-warn, --prov-cap-crit```

Warning and critical limits for over-provisioning. Exceeding
these limits will cause entries in the cluster log. If the critical limit is exceeded, 
new volumes cannot be provisioned and volumes cannot be enlarged. A limit of 500% is typical.

### ```--log-del-interval```

Number of days by which logs are retained. Log storage can grow significantly and it is recommended to keep logs for not longer than one week.

### ```--metrics-retention-period```

Number of days by which the io statistics and other metrics are retained. The amount of data per day is significant, typically limit to a few days or a week.

### ```--contact-point```

This is a webhook endpoint for alerting (critical events such as storage nodes becoming unreachable)

### ```--fabric```

Choose tcp, rdma or both. If both fabrics are chosen, volumes can connect to the cluster
using both options (defined per volume or storage class), but the cluster internally uses rdma.

### ```--qpair-count```

The default amount of queue pairs (sockets) per volume for an initiator (host) to connect to the 
target (server). More queue pairs per volume increase concurrency and volume performance, but require more
server resources (ram, cpu) and thus limit the total amount of volumes per storage node. The default is 3. 
If you need few, very performant volumes, increase the amount, if you need a large amount of less performant 
volumes decrease it. More than 12 parallel connections have limited impact on overall performance. Also, the 
host requires at least one core per queue pair.

### ```--host-sec```

Path to a JSON file with NVMe-oF host security configuration. This enables DH-HMAC-CHAP authentication for NVMe-oF
connections cluster-wide. The JSON file specifies the allowed digest algorithms and Diffie-Hellman groups.

```json title="Example: host-security-config.json"
{
  "params": {
    "dhchap_digests": ["sha256", "sha384"],
    "dhchap_dhgroups": ["ffdhe4096", "ffdhe2048"]
  }
}
```

Supported digests: `sha256`, `sha384`, `sha512`

Supported DH groups: `null`, `ffdhe2048`, `ffdhe3072`, `ffdhe4096`, `ffdhe6144`, `ffdhe8192`

For more information, see [NVMe-oF Security](../architecture/concepts/nvmf-security.md).

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

A human-readable name for the cluster