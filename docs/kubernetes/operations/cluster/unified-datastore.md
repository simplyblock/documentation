---
title: "Operating a Unified DataStore"
description: "Operate a simplyblock Unified DataStore: the array registration, login rotation, capacity growth, LUN takeover after node failures, and teardown."
weight: 10166
---

{{experimental}}

A [Unified DataStore](../../../architecture/concepts/unified-datastore.md) is operated like any other simplyblock cluster.
This page covers what is different: the registration of the storage array, the LUNs simplyblock manages on it, and
the takeover of a failed node's LUN. Everything below is done on the `StorageCluster`: the operator carries every
change to the control plane and the array.

## Array Registration

The array's registration is reported in `status.array` of the `StorageCluster`:

| Field                | Meaning                                                                                |
|----------------------|----------------------------------------------------------------------------------------|
| `id`                 | The control plane's id of the registered array                                         |
| `lunSize`            | The size all LUNs of the cluster have been grown to                                    |
| `registered`         | `true` once the control plane connected with the current spec and login and saved them |
| `protocols`          | The protocols the array plug-in reported it can serve                                  |
| `observedGeneration` | The `StorageCluster` generation last registered                                        |
| `credentialsVersion` | The resource version of the login Secret last registered                               |
| `message`            | The reason the last registration or LUN growth failed, empty otherwise                 |

The registration is repeated automatically whenever `spec.multiAttach.array` changes or the login Secret is updated.
The control plane connects to the array with the new settings before it saves them, so a refused change leaves the
previous registration in force.

```bash title="Showing the registered array"
kubectl -n simplyblock get storagecluster <CLUSTER_NAME> -o jsonpath='{.status.array}'
```

The array's settings are the ones in `spec.multiAttach.array`. The login is never shown: the control plane only
reports whether it holds one.

| Event                      | Object           | Meaning                                                                     |
|----------------------------|------------------|-----------------------------------------------------------------------------|
| `ArrayRegistered`          | `StorageCluster` | The array was registered with the current spec and login                    |
| `ArrayRegistrationRefused` | `StorageCluster` | The login could not be read, or the control plane could not connect with it |
| `AwaitingArray`            | `StorageNode`    | The node's addition waits for the array registration                        |
| `ArrayLUNsGrown`           | `StorageCluster` | Every LUN was grown to `lunSize`, and the cluster's devices with them       |
| `ArrayLUNGrowthFailed`     | `StorageCluster` | Not every LUN could be grown to `lunSize`. The growth is repeated.          |

## Rotating the Array Login

How a login is rotated depends on where it is kept:

- **Secret:** The new login is written to the Secret. The cluster registers the array again with it, and the old login
  can be revoked on the array once `status.array.credentialsVersion` has changed and `registered` is `true`. The
  Secret itself can be deleted after a successful registration. It is only read again when the array block or the
  Secret changes.
- **Vault KV:** A new version of the secret is written in Vault. Without a pinned `version`, the newest version is read
  each time the control plane connects to the array. The connection kept for fencing is renewed within ten minutes,
  so the old login is revoked no earlier than ten minutes after the new version was written.
- **KMIP secret:** A new object is created and the reference's `uid` is changed in the `StorageCluster`, which
  registers the array again.

Other settings of the array, such as its endpoint, options, CA bundle, or journal placement, are changed in
`spec.multiAttach.array` the same way. The cluster registers the array again with them, and the control plane connects
to the array before it saves anything. A changed journal placement applies to storage nodes added afterward.

## Growing Capacity

The capacity of all LUNs is grown together, by raising `lunSize`. A single LUN is never grown alone, because the data
is placed evenly across all of them, and a LUN is never shrunk.

```bash title="Growing every LUN of the cluster to 6 TiB"
kubectl -n simplyblock patch storagecluster <CLUSTER_NAME> --type merge \
    -p '{"spec":{"multiAttach":{"array":{"lunSize":"6Ti"}}}}'
```

Every LUN is grown on the array to the new size first, and every host it is presented to is rescanned until it sees
it. The cluster's devices are then grown onto it online. Storage nodes added later get LUNs of the new size.
`status.array.lunSize` follows once all of it succeeded, and the event `ArrayLUNsGrown` is raised.

All storage nodes and their devices must be online, and the array's pool must hold the grown capacity. When a LUN
cannot be grown, no device of the cluster is grown, `status.array.message` names the cause, and the growth is
repeated until it succeeds. A LUN that already has the new size is left alone, so no LUN is grown twice. A lower
`lunSize` is refused in `status.array.message`.

```bash title="Following the growth"
kubectl -n simplyblock get storagecluster <CLUSTER_NAME> \
    -o jsonpath='{.status.array.lunSize} {.status.array.message}'
```

Journal LUNs are not grown with the data LUNs: a journal's size does not depend on the data it protects.

Capacity is also added with new storage nodes. A growth document (see
[Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md)) names no local device per new node with the
journal placement `LUN`, and one per new node, its journal, with `Local`. Each node's LUNs are created when it is added.

## Node Failures and LUN Takeover

A lost storage node is detected within seconds, its LUN is fenced on the array and taken over by a standby node, and
the I/O of the cluster's volumes resumes (see
[Node Failure and LUN Takeover](../../../architecture/concepts/unified-datastore.md#node-failure-and-lun-takeover)). No
data is rebuilt, and no operator action is needed.

While a takeover runs, every volume of the cluster pauses its I/O, because every volume has data on every LUN. The
pause lasts seconds. When no standby can read the LUN, for example, because the array did not present it to the
standby, the I/O stays paused for up to 150 seconds and then fails, and the LUN's device is marked unavailable.

A node that returns after its LUN was taken over is not given the LUN back. It becomes a standby of the LUN, and the
node that took it over keeps serving it.

!!! warning
    A host whose node was fenced keeps the fence on the array until the node is back online in the cluster. Mapping
    the LUN to the host by hand, or releasing the reservation, can let late writes of that host overwrite newer data.

## Removing a Storage Node

When a storage node is removed, its LUN and its journal LUN are unmapped from every host, and the LUNs of other nodes
are unmapped from the removed node's host unless it serves them. The LUNs themselves are kept on the array. They are
deleted together with the cluster.

## Deleting the Cluster

Deleting the `StorageCluster` deletes every LUN created for it on the array, data and journal LUNs alike, after
unmapping each from all hosts, and then the array registration with its stored login. LUNs that were not created by
the cluster are never touched. A LUN that cannot be deleted does not stop the deletion. It is named in the control
plane's log and removed on the array by hand.

The array registration cannot be removed from a running cluster: without it, a failed node could no longer be fenced
and its LUN not taken over. `spec.multiAttach.array` is therefore kept for the lifetime of the cluster.

## Array Maintenance

Non-disruptive array maintenance, such as a controller failover of the array, needs no action in simplyblock. Array
maintenance that interrupts the I/O of all LUNs, such as a disruptive firmware update, requires the storage cluster to
be shut down first (see [Shutting Down a Storage Cluster](shutting-down-a-cluster.md)). The array's management API
must be reachable whenever a node is added or removed, the capacity is grown, or a node fails, since all of them change
the array's configuration.

## Monitoring

| What                       | Where                                                                                                           |
|----------------------------|-----------------------------------------------------------------------------------------------------------------|
| Array registration         | `status.array` and the events of the `StorageCluster`                                                           |
| LUN takeovers and fences   | The cluster events (see [Cluster Health](../monitoring/cluster-health.md))                                      |
| Capacity of the cluster    | [Cluster Health](../monitoring/cluster-health.md) and [Prometheus Metrics](../monitoring/prometheus-metrics.md) |
| Capacity of the array pool | The monitoring of the array                                                                                     |
| Drive health               | The monitoring of the array. SMART data is not available for LUNs.                                              |

Simplyblock does not return freed capacity to the array, so the array's allocation of the LUNs only grows. An alert on
the array's pool must fire well before it is full: a full pool fails the writes of all LUNs at once.

## Troubleshooting

| Symptom                                                   | Cause and remedy                                                                                                                                                                    |
|-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `registered` stays unset, `message` names a TLS error     | The array's certificate is not trusted. `spec.multiAttach.array.caBundle` is set to the array's CA.                                                                                 |
| `registered` stays unset, `message` names a login failure | The login is wrong or lacks permissions. The Secret, Vault secret, or KMIP object is corrected.                                                                                     |
| `message` names a failed LUN growth                       | A node or device is offline, or the array's pool is full. The cause is removed; the growth is repeated automatically.                                                               |
| `message` says the local key store refuses credentials    | The cluster has no external key management service. One is configured, the login is kept in Vault or KMIP, or, in a test environment only, `credentials.allowLocalKeyStore` is set. |
| Storage nodes wait with `AwaitingArray`                   | The array is not registered yet. `status.array.message` names the reason.                                                                                                           |
| A node addition fails: the LUN did not appear             | The host has no working connection to the array (iSCSI session, zoning, or NVMe connection).                                                                                        |
| A SCSI LUN with several paths is not found                | `multipathd` built no map for it: it is not running, or the array's LUNs are blacklisted (see [Multipathing](../../../deployment-preparation/unified-datastore.md#multipathing)).   |
| A node addition fails: no initiator for the protocol      | The host has no iSCSI initiator name, FC port, or NVMe host NQN. It is configured on the host.                                                                                      |
| An array operation fails with a name collision            | A volume or host object of the same name exists on the array and was not created by this cluster. It is renamed or removed on the array.                                            |
