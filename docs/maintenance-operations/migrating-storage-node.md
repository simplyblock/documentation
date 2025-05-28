---
title: "Migrating a Storage Node"
weight: 20000
---

Simplyblock storage clusters are designed as always-on. That means that a storage node migration is an online operation
that doesn't require explicit maintenance windows or storage downtime.

## Storage Node Migration

Migrating a storage node is a three-step process. First, the new storage node will be pre-deployed, then the old node
will be restarted with the new node address, and finally, the new storage node will become the primary storage node.

!!! warning
    Between each process step, it is required to wait for storage node migration tasks to complete. Otherwise, there
    may have an impact on the system's performance or, worse, may lead to data loss.

As part of the process, the existing storage node id will be moved to the new host machine. All logical volumes
allocated on the old storage node will be moved to the new storage node and will automatically be reconnected.

### First-Stage Storage Node Deployment

To install the first stage of a storage node, the installation guide for the selected environment should be followed.

The process will diverge after executing the initial deployment command `{{ cliname }} storage-node deploy`.
If the command finishes successfully, resume from the next section of this page.

- [Kubernetes](../deployments/kubernetes/install-simplyblock/index.md)
- [Bare Metal or Virtualized Linux](../deployments/baremetal/index.md)
- [AWS EC2](../deployments/aws-ec2/index.md)

### Restart Old Storage Node

To start the migration process of logical volumes, the old storage node needs to be restarted with the new storage
node's API address.

In this example, it is assumed that the new storage node's IP address is _192.168.10.100_. The IP address must be
changed according to the real-world setup.

!!! danger
    Providing the wrong IP address can lead to service interruption and data loss.

To restart the node, the following command must be run:

```bash title="Restarting a storage node to initiate the migration"
{{ cliname }} storage-node restart <NODE_ID> --node-addr=<NEW_NODE_IP>:5000
```

!!! warning
    The parameter `--node-addr` expects the API endpoint of the new storage node. This API is reachable on port _5000_.
    It must be ensured that the given parameter is the new IP address and the port, separated by a colon.

```plain title="Example output of the node restart"
demo@cp-1 ~> {{ cliname }} storage-node restart 788c3686-9d75-4392-b0ab-47798fd4a3c1 --node-addr 192.168.10.64:5000
2025-04-02 13:24:26,785: INFO: Restarting storage node
2025-04-02 13:24:26,796: INFO: Setting node state to restarting
2025-04-02 13:24:26,807: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "STATUS_CHANGE", "object_name": "StorageNode", "message": "Storage node status changed from: unreachable to: in_restart", "caused_by": "monitor"}
2025-04-02 13:24:26,812: INFO: Sending event updates, node: 788c3686-9d75-4392-b0ab-47798fd4a3c1, status: in_restart
2025-04-02 13:24:26,843: INFO: Sending to: f4b37b6c-6e36-490f-adca-999859747eb4
2025-04-02 13:24:26,859: INFO: Sending to: 71c31962-7313-4317-8330-9f09a3e77a72
2025-04-02 13:24:26,870: INFO: Sending to: 93a812f9-2981-4048-a8fa-9f39f562f1aa
2025-04-02 13:24:26,893: INFO: Restarting on new node with ip: 192.168.10.64:5000
2025-04-02 13:24:27,037: INFO: Restarting Storage node: 192.168.10.64
2025-04-02 13:24:27,097: INFO: Restarting SPDK
...
2025-04-02 13:24:40,012: INFO: creating subsystem nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:13945596-4fbc-46a5-bbb1-ebe4d3e2af26
2025-04-02 13:24:40,025: INFO: creating subsystem nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:2c593f82-d96c-4eb7-8d1c-30c534f6592d
2025-04-02 13:24:40,037: INFO: creating subsystem nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:e3d2d790-4d14-4875-a677-0776335e4588
2025-04-02 13:24:40,048: INFO: creating subsystem nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:1086d1bf-e77f-4ddf-b374-3575cfd68d30
2025-04-02 13:24:40,414: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "StorageNode", "message": "Port blocked: 9091", "caused_by": "cli"}
2025-04-02 13:24:40,494: INFO: Add BDev to subsystem
2025-04-02 13:24:40,495: INFO: 1
2025-04-02 13:24:40,495: INFO: adding listener for nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:13945596-4fbc-46a5-bbb1-ebe4d3e2af26 on IP 10.10.10.64
2025-04-02 13:24:40,499: INFO: Add BDev to subsystem
2025-04-02 13:24:40,499: INFO: 1
2025-04-02 13:24:40,500: INFO: adding listener for nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:e3d2d790-4d14-4875-a677-0776335e4588 on IP 10.10.10.64
2025-04-02 13:24:40,503: INFO: Add BDev to subsystem
2025-04-02 13:24:40,504: INFO: 1
2025-04-02 13:24:40,504: INFO: adding listener for nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:2c593f82-d96c-4eb7-8d1c-30c534f6592d on IP 10.10.10.64
2025-04-02 13:24:40,507: INFO: Add BDev to subsystem
2025-04-02 13:24:40,508: INFO: 1
2025-04-02 13:24:40,509: INFO: adding listener for nqn.2023-02.io.simplyblock:a84537e2-62d8-4ef0-b2e4-8462b9e8ea96:lvol:1086d1bf-e77f-4ddf-b374-3575cfd68d30 on IP 10.10.10.64
2025-04-02 13:24:41,861: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "StorageNode", "message": "Port allowed: 9091", "caused_by": "cli"}
2025-04-02 13:24:41,894: INFO: Done
Success
```

### Make new Storage Node Primary

After the migration has successfully finished, the new storage node must be made the primary storage node for the owned
set of logical volumes.

This can be initiated using the following command:

```bash title="Make the new storage node the primary"
{{ cliname }} storage-node make-primary <NODE_ID>
```

The following is the example output.

```plain title="Example output of primary change"
demo@cp-1 ~> {{ cliname }} storage-node make-primary 788c3686-9d75-4392-b0ab-47798fd4a3c1
2025-04-02 13:25:02,220: INFO: Adding device 65965029-4ab3-44b9-a9d4-29550e6c14ae
2025-04-02 13:25:02,251: INFO: bdev already exists alceml_65965029-4ab3-44b9-a9d4-29550e6c14ae
2025-04-02 13:25:02,252: INFO: bdev already exists alceml_65965029-4ab3-44b9-a9d4-29550e6c14ae_PT
2025-04-02 13:25:02,266: INFO: subsystem already exists True
2025-04-02 13:25:02,267: INFO: bdev already added to subsys alceml_65965029-4ab3-44b9-a9d4-29550e6c14ae_PT
2025-04-02 13:25:02,285: INFO: Setting device online
2025-04-02 13:25:02,301: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "NVMeDevice", "message": "Device created: 65965029-4ab3-44b9-a9d4-29550e6c14ae", "caused_by": "cli"}
2025-04-02 13:25:02,305: INFO: Make other nodes connect to the node devices
2025-04-02 13:25:02,383: INFO: Connecting to node 71c31962-7313-4317-8330-9f09a3e77a72
2025-04-02 13:25:02,384: INFO: bdev found remote_alceml_197c2d40-d39a-4a10-84eb-41c68a6834c7_qosn1
2025-04-02 13:25:02,385: INFO: bdev found remote_alceml_5202854e-e3b3-4063-b6b9-9a83c1bbefe9_qosn1
2025-04-02 13:25:02,386: INFO: bdev found remote_alceml_15c5f6de-63b6-424c-b4c0-49c3169c0135_qosn1
2025-04-02 13:25:02,386: INFO: Connecting to node 93a812f9-2981-4048-a8fa-9f39f562f1aa
2025-04-02 13:25:02,439: INFO: Connecting to node f4b37b6c-6e36-490f-adca-999859747eb4
2025-04-02 13:25:02,440: INFO: bdev found remote_alceml_0544ef17-6130-4a79-8350-536c51a30303_qosn1
2025-04-02 13:25:02,441: INFO: bdev found remote_alceml_e9d69493-1ce8-4386-af1a-8bd4feec82c6_qosn1
2025-04-02 13:25:02,442: INFO: bdev found remote_alceml_5cc0aed8-f579-4a4c-9c31-04fb8d781af8_qosn1
2025-04-02 13:25:02,443: INFO: Connecting to node 93a812f9-2981-4048-a8fa-9f39f562f1aa
2025-04-02 13:25:02,493: INFO: Connecting to node f4b37b6c-6e36-490f-adca-999859747eb4
2025-04-02 13:25:02,494: INFO: bdev found remote_alceml_0544ef17-6130-4a79-8350-536c51a30303_qosn1
2025-04-02 13:25:02,494: INFO: bdev found remote_alceml_e9d69493-1ce8-4386-af1a-8bd4feec82c6_qosn1
2025-04-02 13:25:02,495: INFO: bdev found remote_alceml_5cc0aed8-f579-4a4c-9c31-04fb8d781af8_qosn1
2025-04-02 13:25:02,495: INFO: Connecting to node 71c31962-7313-4317-8330-9f09a3e77a72
2025-04-02 13:25:02,496: INFO: bdev found remote_alceml_197c2d40-d39a-4a10-84eb-41c68a6834c7_qosn1
2025-04-02 13:25:02,496: INFO: bdev found remote_alceml_5202854e-e3b3-4063-b6b9-9a83c1bbefe9_qosn1
2025-04-02 13:25:02,497: INFO: bdev found remote_alceml_15c5f6de-63b6-424c-b4c0-49c3169c0135_qosn1
2025-04-02 13:25:02,667: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 773ae420-3491-4ea6-aaf4-b7b1103132f6", "caused_by": "cli"}
2025-04-02 13:25:02,675: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 95eaf69f-6926-454e-a023-8d9341f7c4c6", "caused_by": "cli"}
2025-04-02 13:25:02,682: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 0a0f7942-46d7-46b2-9dc6-c5787bc3691e", "caused_by": "cli"}
2025-04-02 13:25:02,690: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 0f10c95e-937b-4e9b-99ca-e13815ae3578", "caused_by": "cli"}
2025-04-02 13:25:02,698: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: fb36c4c7-d128-4a43-894f-50fb406bab30", "caused_by": "cli"}
2025-04-02 13:25:02,707: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: d5480f1f-e113-49ab-8c9d-3663e7ba512b", "caused_by": "cli"}
2025-04-02 13:25:02,717: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 8e910437-7957-4701-b626-5dffce0284dc", "caused_by": "cli"}
2025-04-02 13:25:02,727: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 919fceb4-ee48-4c72-96b0-a4367b8d0f67", "caused_by": "cli"}
2025-04-02 13:25:02,737: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: da076017-c0ba-4e5b-8bcd-7748fa56305e", "caused_by": "cli"}
2025-04-02 13:25:02,748: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: fa43687f-33ff-486d-8460-2b07bbc18cff", "caused_by": "cli"}
2025-04-02 13:25:02,757: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: e53431ce-c7c9-40a9-8e11-4dafefce79d8", "caused_by": "cli"}
2025-04-02 13:25:02,768: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: 38e320ca-1fd1-4f8e-9ef1-2defa50f1d22", "caused_by": "cli"}
2025-04-02 13:25:02,813: INFO: Adding device 7e5145e7-d8fc-4d60-8af1-3f5015cb3021
2025-04-02 13:25:02,837: INFO: bdev already exists alceml_7e5145e7-d8fc-4d60-8af1-3f5015cb3021
2025-04-02 13:25:02,837: INFO: bdev already exists alceml_7e5145e7-d8fc-4d60-8af1-3f5015cb3021_PT
2025-04-02 13:25:02,851: INFO: subsystem already exists True
2025-04-02 13:25:02,852: INFO: bdev already added to subsys alceml_7e5145e7-d8fc-4d60-8af1-3f5015cb3021_PT
2025-04-02 13:25:02,879: INFO: Setting device online
2025-04-02 13:25:02,893: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "NVMeDevice", "message": "Device created: 7e5145e7-d8fc-4d60-8af1-3f5015cb3021", "caused_by": "cli"}
2025-04-02 13:25:02,897: INFO: Make other nodes connect to the node devices
2025-04-02 13:25:02,968: INFO: Connecting to node 71c31962-7313-4317-8330-9f09a3e77a72
2025-04-02 13:25:02,969: INFO: bdev found remote_alceml_197c2d40-d39a-4a10-84eb-41c68a6834c7_qosn1
2025-04-02 13:25:02,970: INFO: bdev found remote_alceml_5202854e-e3b3-4063-b6b9-9a83c1bbefe9_qosn1
2025-04-02 13:25:02,971: INFO: bdev found remote_alceml_15c5f6de-63b6-424c-b4c0-49c3169c0135_qosn1
2025-04-02 13:25:02,971: INFO: Connecting to node 93a812f9-2981-4048-a8fa-9f39f562f1aa
...
2025-04-02 13:25:10,255: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: a4692e1d-a527-44f7-8a86-28060eb466cf", "caused_by": "cli"}
2025-04-02 13:25:10,277: INFO: {"cluster_id": "a84537e2-62d8-4ef0-b2e4-8462b9e8ea96", "event": "OBJ_CREATED", "object_name": "JobSchedule", "message": "task created: bab06208-bd27-4002-bc7b-dd92cf7b9b66", "caused_by": "cli"}
True
```

At this point, the old storage node is automatically removed from the cluster, and the storage node id is taken over by
the new storage node. Any operation on the old storage node, such as an OS reinstall, can be safely executed.
