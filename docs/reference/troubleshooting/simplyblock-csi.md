---
title: Kubernetes CSI
weight: 30300
---

## High-Level CSI Driver Architecture

** Controller Plugin:** Runs as a Deployment and manages volume provisioning and deletion.

**Node Plugin:** Runs as a DaemonSet and handles volume attachment, mounting, and unmounting.

**Sidecars:** Handle tasks like external provisioning (`csi-provisioner`), attaching (`csi-attacher`), and monitoring
(`csi-node-driver-registrar`).

## Finding CSI Driver Logs for a Specific PVC

1. Identify the Node Where the PVC is Mounted
   ```bash title="Get the pod name using the persistent volume claim"
   kubectl get pods -A -o \
   jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}' | \
   grep <PVC_NAME>
   ```
   ```bash title="Find the node the pod is bound to"
   kubectl get pods -A -o \
   jsonpath='{range .items[*]}{.spec.nodeName}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}' | \
   grep <PVC_NAME>
   ```
2. Find the CSI driver pod on that node
   ```bash title="Find the CSI driver pod"
   kubectl get pods -n <CSI_NAMESPACE> -o wide | grep <NODE_NAME>
   ```
3. Get Logs from the node plugin
   ```bash title="Get the CSI driver pod logs"
   kubectl logs -n <CSI_NAMESPACE> <CSI_NODE_POD> -c <DRIVER_CONTAINER>
   ```
   
## Troubleshooting NVMe-Related Errors

If the error is NVMe-related (e.g., volume attachment failure, device not found), follow these steps.

1. Ensure that `nvme-cli` is installed

    === "RHEL / Alma / Rocky"
    
        ```bash
        sudo dnf install -y nvme-cli
        ```
    
    === "Debian / Ubuntu"
    
        ```bash
        sudo apt install -y nvme-cli
        ```

2. Verify if the _nvme-tcp_ kernel module is loaded
   ```bash title="Check NVMe/TCP kernel module is loaded"
   lsmod | grep nvme_tcp
   ```

    If not available, the driver can be loaded temporarily using the following command:

    ```bash title="Load NVMe/TCP kernel module"
    sudo modprobe nvme-tcp
    ```

    However, to ensure it is automatically loaded at system startup, it should be persisted as following:

    === "Red Hat / Alma / Rocky"
    
        ```bash
        echo "nvme-tcp" | sudo tee -a /etc/modules-load.d/nvme-tcp.conf
        ```
    
    === "Debian / Ubuntu"
    
        ```bash
        echo "nvme-tcp" | sudo tee -a /etc/modules
        ```

3. Check NVMe Connection Status
   ```bash title="Check NVMe-oF connection"
   sudo nvme list-subsys
   ```
   
    If the expected NVMe subsystem is missing, reconnect manually:

    ```bash title="Manually reconnect the NVMe-oF device"
    sudo nvme connect -t tcp \
        -n <NVME_SUBSYS_NAME> \
        -a <TARGET_IP> \
        -s <TARGET_PORT> \
        -l <CTRL_LOSS_TIMEOUT> \
        -c <RECONNECT_DELAY> \
        -i <NR_IO_QUEUES>
    ```

4. If the issue persists, gather kernel logs and provide them to the simplyblock support team:
   ```bash title="Collect logs for support"
   sudo dmesg | grep -i nvme
   ```
