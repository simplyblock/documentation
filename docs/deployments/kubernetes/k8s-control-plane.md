---
title: "Install Simplyblock Control Plane on Kubernetes"
description: "Install Simplyblock Control Plane on Kubernetes: Before running the helm install, you can edit the values.yaml file to match your specific configuration."
weight: 30000
---

```bash title="Install CLI"
pip install {{ cliname }} --upgrade
```

After installing the CLI, navigate to the Helm chart directory within the installed package:

```bash
cd /usr/local/lib/python3.9/site-packages/simplyblock_core/scripts/charts/
```

Then build the Helm dependencies and deploy the simplyblock control plane:

```bash
helm dependency build ./
helm upgrade --install sbcli --namespace simplyblock --create-namespace ./
```

Before running the `helm install`, you can edit the `values.yaml` file to match your specific configuration.
For example, to set cluster parameters, storage options, monitoring secret or node selectors according to your environment.

{% include 'control-plane-network-port-table-k8s.md' %}

Find and exec into the admin control pod (replace the pod name if different):

```bash
kubectl -n simplyblock exec -it simplyblock-admin-control-<uuid> -- bash
```

```bash title="Install Control Plane"
{{ cliname }} cluster create --mgmt-ip <WORKER_IP> --ha-type ha --mode kubernetes
```

!!! info
    You need to add additional parameter when using a Loadbalancer `--ingress-host-source loadbalancer` and `--dns-name <LB_INGRESS_DNS>`

To enable NVMe-oF transport security (DH-HMAC-CHAP authentication and TLS/PSK), provide a JSON configuration file
with the `--host-sec` flag:

```bash title="Install Control Plane with NVMe-oF Security"
{{ cliname }} cluster create --mgmt-ip <WORKER_IP> --ha-type ha --mode kubernetes --host-sec=host-security-config.json
```

```json title="Example: host-security-config.json"
{
  "params": {
    "dhchap_digests": ["sha256", "sha384"],
    "dhchap_dhgroups": ["ffdhe4096", "ffdhe2048"]
  }
}
```

For more information, see [NVMe-oF Security](../../architecture/concepts/nvmf-security.md).

To enable S3 backup and recovery, provide a JSON configuration file with the `--use-backup` flag:

```bash title="Install Control Plane with Backup"
{{ cliname }} cluster create --mgmt-ip <WORKER_IP> --ha-type ha --mode kubernetes --use-backup=backup-config.json
```

```json title="Example: backup-config.json"
{
  "access_key_id": "<AWS_ACCESS_KEY>",
  "secret_access_key": "<AWS_SECRET_KEY>",
  "bucket_name": "simplyblock-backups"
}
```

For MinIO or S3-compatible storage, add the `local_endpoint` field:

```json title="Example: MinIO backup config"
{
  "access_key_id": "<MINIO_ACCESS_KEY>",
  "secret_access_key": "<MINIO_SECRET_KEY>",
  "bucket_name": "simplyblock-backups",
  "local_endpoint": "http://minio.example.com:9000"
}
```

For more information on backup operations, see [Backup and Recovery](../../usage/backup-recovery.md).

Additional parameters for the cluster create command can be found at [Cluster Deployment Options](../cluster-deployment-options.md).
