---
title: Kubernetes CSI
description: "Kubernetes CSI: Controller Plugin: Runs as a Deployment and manages volume provisioning and deletion Node Plugin: Runs as a DaemonSet and handles volume."
weight: 30300
---

Simplyblock CSI integrates Kubernetes volume lifecycle operations (provision, attach, mount, unmount, delete) with the
simplyblock storage backend.

Most CSI issues appear in one of three layers:

- Kubernetes object lifecycle (PVC/PV/Pod events),
- CSI controller/node plugin behavior,
- node-level transport and NVMe subsystem state.

## High-Level CSI Driver Architecture

- **Controller Plugin:** Runs as a Deployment and manages volume provisioning and deletion.
- **Node Plugin:** Runs as a DaemonSet and handles volume attachment, mounting, and unmounting.
- **Sidecars:** Handle external provisioning (`csi-provisioner`), attaching (`csi-attacher`), and driver registration
  (`csi-node-driver-registrar`).

## Quick Component Health Checks

Start by validating CSI control-plane and node-plane pods:

```bash title="List CSI pods"
kubectl get pods -n <CSI_NAMESPACE> -o wide
```

```bash title="Inspect CSI pod status and restart counts"
kubectl get pods -n <CSI_NAMESPACE> \
  -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,RESTARTS:.status.containerStatuses[*].restartCount,NODE:.spec.nodeName
```

## Check Kubernetes Events First

Before deep host diagnostics, inspect object events for clear failure reasons:

```bash title="Describe PVC"
kubectl describe pvc <PVC_NAME> -n <WORKLOAD_NAMESPACE>
```

```bash title="Describe pod using the PVC"
kubectl describe pod <POD_NAME> -n <WORKLOAD_NAMESPACE>
```

```bash title="View recent warning events"
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp
```

## Trace a PVC End-to-End

Use this sequence to identify the right logs and host:

1. Find pod(s) using the PVC.
2. Resolve the node where the pod is scheduled.
3. Locate the CSI node plugin pod on that node.
4. Pull logs from the node plugin (and controller plugin if needed).

```bash title="Find pods using the PVC"
kubectl get pods -A -o \
jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}' | \
grep <PVC_NAME>
```

```bash title="Find node for the PVC-consuming pod"
kubectl get pods -A -o \
jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{"\t"}{.spec.nodeName}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}' | \
grep <PVC_NAME>
```

```bash title="Find CSI node plugin pod on target node"
kubectl get pods -n <CSI_NAMESPACE> -o wide | grep <NODE_NAME>
```

```bash title="Get CSI node plugin logs"
kubectl logs -n <CSI_NAMESPACE> <CSI_NODE_POD> -c <DRIVER_CONTAINER>
```

```bash title="Get CSI controller plugin logs"
kubectl logs -n <CSI_NAMESPACE> <CSI_CONTROLLER_POD> -c <DRIVER_CONTAINER>
```

## Troubleshooting NVMe-Related Errors

If errors indicate NVMe path issues (volume attachment failure, device not found, path loss), run the following checks
on the affected worker node.

### 1) Ensure `nvme-cli` is installed

=== "RHEL / Alma / Rocky"

    ```bash title="Install nvme-cli on RHEL-based systems"
    sudo dnf install -y nvme-cli
    ```

=== "Debian / Ubuntu"

    ```bash title="Install nvme-cli on Debian-based systems"
    sudo apt install -y nvme-cli
    ```

### 2) Verify `nvme_tcp` kernel module

```bash title="Check NVMe/TCP kernel module"
lsmod | grep nvme_tcp
```

If missing, load it:

```bash title="Load NVMe/TCP kernel module"
sudo modprobe nvme-tcp
```

Persist module loading across reboots:

=== "Red Hat / Alma / Rocky"

    ```bash title="Persist nvme-tcp module (RHEL-based)"
    echo "nvme-tcp" | sudo tee -a /etc/modules-load.d/nvme-tcp.conf
    ```

=== "Debian / Ubuntu"

    ```bash title="Persist nvme-tcp module (Debian-based)"
    echo "nvme-tcp" | sudo tee -a /etc/modules
    ```

### 3) Check NVMe subsystem state

```bash title="List NVMe subsystems"
sudo nvme list-subsys
```

If expected subsystem is missing, reconnect manually:

```bash title="Reconnect NVMe-oF subsystem"
sudo nvme connect -t tcp \
    -n <NVME_SUBSYS_NAME> \
    -a <TARGET_IP> \
    -s <TARGET_PORT> \
    -l <CTRL_LOSS_TIMEOUT> \
    -c <RECONNECT_DELAY> \
    -i <NR_IO_QUEUES>
```

### 4) Collect node diagnostics

```bash title="Collect NVMe-related kernel logs"
sudo dmesg | grep -i nvme
```

## Common Failure Patterns

- `timed out waiting for condition` during mount: usually node-path or transport connectivity.
- `device not found` after attach: often missing kernel module or failed subsystem connect.
- repeated reconnect loops in logs: verify target IP/port, transport, and backend health.

## Symptom-to-Action Quick Index

- PVC stuck in `Pending`: check provisioning flow and CSI controller logs.
- Pod stuck in `ContainerCreating` or mount timeout: trace PVC to node plugin logs.
- Volume attach/mount failure with NVMe errors: run node-level NVMe diagnostics.
- Intermittent I/O errors after attach: inspect kernel/NVMe subsystem state and reconnect path.

## Escalation Checklist

When escalating to support, collect:

- CSI controller and node plugin logs around failure timestamp.
- `kubectl describe` output for affected PVC and pod.
- Node-level `nvme list-subsys` and `dmesg` output.
- Affected resource identifiers: namespace, pod, PVC, PV, node, and approximate timestamps.

## Related References

- [Install CSI Driver](../../deployments/kubernetes/install-csi.md)
- [Provisioning](../../usage/simplyblock-csi/provisioning.md)
- [Storage Plane Troubleshooting](storage-plane.md)
- [Cluster Health Monitoring](../../maintenance-operations/monitoring/cluster-health.md)
