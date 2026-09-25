---
title: "Cluster Health"
description: "Check the health of a simplyblock cluster on Kubernetes through the ControlPlane, StorageCluster, StorageNode, and StorageDevice status, and with the CLI."
weight: 10610
---

A simplyblock cluster consists of the control plane and the storage nodes of the storage plane, working together to
deliver a resilient, distributed storage platform. On Kubernetes, the Simplyblock Operator mirrors the state of both
into the status of its custom resources, so the health of a deployment can be read with `kubectl`. The `{{ cliname }}`
command line interface provides additional statistics and checks for deeper diagnosis.

## Control Plane Status

The `ControlPlane` resource (short name `cp`) is created by the Helm chart as `simplyblock`. Its phase is `Available`
when every component is ready, `Degraded` when a non-essential component is short of replicas, and `Unavailable` when
an essential component has none ready. `Installing` is reported during the first installation.

```bash title="Reading the control plane status"
kubectl -n simplyblock get controlplane simplyblock
```

`status.components` lists every workload of the control plane with its `desired` and `ready` replica counts, and
whether it is `essential`. The FoundationDB cluster (`simplyblock-fdb-cluster`) and the management API
(`simplyblock-webappapi`) are essential.

```bash title="Listing the control plane components and their readiness"
kubectl -n simplyblock get cp simplyblock \
  -o jsonpath='{range .status.components[*]}{.name}{"\t"}{.ready}/{.desired}{"\t"}{.essential}{"\n"}{end}'
```

`status.version` reports the version the control plane serves, and `status.lastChecked` the time of the last probe.

## Storage Cluster Status

The `StorageCluster` resource (short name `stc`) reports the phase of the cluster (`Pending`, `Creating`,
`Provisioning`, `Activating`, `Online`, `Degraded`, `Unavailable`, or `Suspended`) together with the backend status
string, the erasure coding scheme, and the maximum fault tolerance.

```bash title="Reading the storage cluster status"
kubectl -n simplyblock get storagecluster -o wide
```

Further status fields worth checking:

- **`status.rebalancing`:** whether the backend is rebalancing data.
- **`status.maxFaultTolerance`:** the number of failures the cluster currently tolerates.
- **`status.maxConcurrentWorkerRestarts`:** the effective number of workers that may restart at once.
- **`status.message`:** the latest finding of the operator.

### Running Tasks

`status.tasks` lists the control plane's running and pending jobs (at most 20), each with its `id`, `type`, `status`
(`new`, `running`, or `suspended`), and `retry` count. A finished task leaves the list and is reported as an event. A
task whose `retry` count keeps growing is failing rather than slow.

```bash title="Listing the running tasks of a cluster"
kubectl -n simplyblock get stc production \
  -o jsonpath='{range .status.tasks[*]}{.id}{"\t"}{.type}{"\t"}{.status}{"\t"}{.retry}{"\n"}{end}'
```

A task is canceled with a `StorageClusterOps` operation with `action: CancelTask` and the task's `id`, see
[Cluster Actions](../cluster/cluster-actions.md).

## Storage Node and Device Status

Each storage node is a `StorageNode` resource (short name `sn`) in the namespace of its cluster. The listing shows the
worker, the socket, the phase, the backend status (for example, `online`, `offline`, `suspended`, or `unreachable`),
and the health check result.

```bash title="Listing the storage nodes of a cluster"
kubectl -n simplyblock get storagenodes -o wide
```

`status.resources` of a node reports its CPU and memory, the number of volumes, the online and total devices, and its
capacity. The devices of a node are mirrored as `StorageDevice` resources (short name `sd`), labeled with the node:

```bash title="Listing the devices of one storage node"
kubectl -n simplyblock get storagedevices -l storage.simplyblock.io/node=production-7f3a9c
```

A device reports its `status.phase`, the backend `status.deviceStatus`, its `status.role` (`Storage` or `Journal`),
and its hardware details.

## Capacity

The capacity of the cluster, its nodes, pools, and devices is served by the metrics API, see
[Capacity Metrics API](index.md#capacity-metrics-api).

```bash title="Reading the capacity of a cluster"
kubectl -n simplyblock get storageclustermetrics production -o yaml
```

The warning and critical capacity thresholds that feed the capacity alerts are set in
`StorageCluster.spec.warningThreshold` and `spec.criticalThreshold`, each with `capacity` and `provisionedCapacity`.

## Events

The operator reports state changes and the progress of every operation as Kubernetes events on the affected resource.

```bash title="Listing the recent events of the simplyblock namespace"
kubectl -n simplyblock get events --sort-by=.lastTimestamp
```

## Using the CLI

The `{{ cliname }}` command line interface is available in the `simplyblock-admin-control` pod of a local control plane.

```bash title="Running the CLI in the admin control pod"
kubectl -n simplyblock exec -it deploy/simplyblock-admin-control -- {{ cliname }} cluster list
```

The commands below are run the same way. The cluster UUID is held in `StorageCluster.status.uuid`.

```bash title="Accessing the status of a cluster"
{{ cliname }} cluster status <CLUSTER_ID>
```

```bash title="Accessing the statistics of a cluster"
{{ cliname }} cluster show <CLUSTER_ID>
```

```bash title="Accessing the I/O statistics of a cluster"
{{ cliname }} cluster get-io-stats <CLUSTER_ID>
```

```bash title="Accessing the capacity information of a cluster"
{{ cliname }} cluster get-capacity <CLUSTER_ID>
```

```bash title="Accessing the health status of a cluster"
{{ cliname }} cluster check <CLUSTER_ID>
```

All details of the commands are available in the [CLI reference](../../../reference/cli/index.md). The statistics are
also available through Grafana in the cluster's dashboard, see [Accessing Grafana](accessing-grafana.md).
