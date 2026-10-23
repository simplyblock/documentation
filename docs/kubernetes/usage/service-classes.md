---
title: "Service Classes"
description: "Define the I/O service classes of a storage cluster, place volumes in a class through a storage pool or StorageClass, and set the share of replication traffic."
weight: 40650
---

Service classes divide the I/O capacity of a storage cluster between groups of volumes in relative terms. Each class
has a weight, and when the classes compete for the same storage, each class receives a share of the cluster's I/O in
proportion to its weight. A class that does not use its share leaves it to the others, so no capacity is held back.

Service classes complement the per-volume and per-pool caps described in
[Defining Quality of Service](quality-of-service.md). A cap is an absolute ceiling for a volume or a pool. A service
class is a relative share that guarantees a group of volumes its part of the cluster under load, whatever the other
volumes do. See [Performance and QoS](../../architecture/storage-performance-and-qos.md) for the background.

## How Service Classes Work

Every volume runs in exactly one service class. A storage cluster has the following classes:

| Class                    | Purpose                                           | Configured by           |
|--------------------------|---------------------------------------------------|-------------------------|
| `Default`                | Every volume that names no other class            | `defaultWeight`         |
| Up to five named classes | Volumes that are placed in the class by name      | `classes`               |
| Metadata and migration   | Internal metadata I/O and volume migration        | Fixed at 25% of the I/O |
| Replication              | Snapshot replication between two storage clusters | `replicationShare`      |

The metadata and replication classes are internal. Volumes cannot be placed in them.

The weights of `Default` and the named classes are relative to each other. Together, they divide the share that
remains after the metadata class (25%) and the replication class (`replicationShare`). For example, with
`defaultWeight: 100`, one class `gold` with weight `300`, and `replicationShare: 10`, the remaining 65% are divided
1:3:

| Class                  | Share of the I/O under full contention |
|------------------------|----------------------------------------|
| Metadata and migration | 25%                                    |
| Replication            | 10%                                    |
| `gold`                 | 48%                                    |
| `Default`              | 17%                                    |

Shares only take effect while classes compete. A class that is idle does not count, so the active classes divide the
whole capacity among themselves in proportion to their weights.

## Configuring the Classes of a Cluster

The classes of a storage cluster are declared in `StorageCluster.spec.serviceClasses`. The Simplyblock Operator
applies them to the control plane and keeps them in line with the specification.

```yaml title="Example of a storage cluster with two service classes"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: production
  namespace: simplyblock
spec:
  # ...
  serviceClasses:
    defaultWeight: 100
    classes:
      - name: gold
        weight: 300
      - name: bronze
        weight: 20
    replicationShare: 10
```

| Field              | Description                                                                                                   | Default |
|--------------------|---------------------------------------------------------------------------------------------------------------|---------|
| `defaultWeight`    | Relative weight of the `Default` class, from 1 to 1000.                                                       | `100`   |
| `classes`          | Up to five named classes. Each has a `name` and a `weight` from 1 to 1000.                                    | None    |
| `classes[].name`   | Name a storage pool or StorageClass uses to select the class. It starts with a letter. `Default` is reserved. | None    |
| `replicationShare` | Percentage of the I/O given to snapshot replication, from 0 to 74.                                            | `10`    |

The classes can be changed on a running cluster. A class can be added, reweighted, or removed, and the new weights
take effect on the storage nodes immediately. A class keeps the number the control plane assigned to it for as long
as it exists. A class that a volume still uses cannot be removed: the change is refused and retried until the
specification or the volumes change.

If `serviceClasses` is omitted, the operator leaves the classes of the cluster as they are.

### Status and Events

`StorageCluster.status.serviceClasses` lists the named classes as the control plane holds them, with their `name`,
their control-plane `id`, and their `weight`. The operator reports the outcome of every change as an event on the
`StorageCluster`:

| Event                       | Meaning                                                                                      |
|-----------------------------|----------------------------------------------------------------------------------------------|
| `ServiceClassesApplied`     | The specification differed from the control plane and was applied.                           |
| `ServiceClassesRefused`     | The control plane refused the change, for example, because a removed class is still in use.  |
| `ServiceClassesUnsupported` | The control plane is too old to configure service classes; the specification is not applied. |

## Placing Volumes in a Class

A volume's class is selected by name through the StorageClass it is provisioned with. For the StorageClass of a
storage pool, the class is stated in the pool's volume defaults, and the operator writes it into the StorageClass as
the `priority_class` parameter (see [Storage Class](storage-class.md)):

```yaml title="Example of a storage pool whose volumes run in the gold class"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: databases
  namespace: simplyblock
spec:
  # ...
  volumeDefaults:
    priorityClass: gold
```

An authored StorageClass names the class in its parameters:

```yaml title="Example of a StorageClass for the gold class"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: databases-gold
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: databases
  priority_class: gold
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

The class is chosen when a volume is created. A volume whose class the cluster does not define is not created. A
StorageClass without `priority_class` places its volumes in `Default`.

## Replication Traffic

Asynchronous replication between two storage clusters runs in the replication class: the reads of the snapshots that
are sent, and the writes of the copies that receive them. `replicationShare` sets the weight of that class.

`replicationShare` is a weight, not a cap. Replication uses more than its share when no other class needs the
capacity, and a share of `0` leaves replication only the scheduler's minimum while other classes are busy.

A copy that carries client I/O again, after a failover or a migration cutover, runs in the class of the source volume,
provided the target cluster defines a class with the same number. Otherwise, it runs in `Default`. To keep classes
across a failover, define the same classes, in the same order, on both storage clusters.

## Limitations

- The class of a volume is fixed when the volume is created. Volumes created before a class existed stay in their
  class.
- There is no per-claim annotation for the class. The class comes from the StorageClass.
- A storage cluster that was created with six named classes by an earlier version keeps its sixth class. Its
  replication runs in `Default`.
