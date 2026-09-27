---
title: "Protection Plans"
description: "Declare sites, protected StorageClasses, replication methods, and S3 stores with a ProtectionPlan, and review what dr-hub derives from it."
weight: 10220
---

A ProtectionPlan is the cluster-scoped resource that defines a disaster recovery topology: which site clusters take
part, which StorageClasses are protected, which replication methods are available, and where each site keeps its
Ramen metadata in S3. From a plan and its [DR paths](paths.md), `dr-hub` derives all Ramen and csi-addons objects that
Ramen needs. Protection plans are written by the `dr-admin` role.

The concepts behind plans are explained in [Protection Plans and Paths](../../architecture/concepts/dr-protection-plans.md).

## Specification

| Field                                             | Required          | Description                                                                                                                                                             |
|---------------------------------------------------|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `metadata.name`                                   | Yes               | Plan name, at most 40 characters. It is part of derived object names and label keys.                                                                                    |
| `spec.sites[]`                                    | Yes               | 2 to 16 sites.                                                                                                                                                          |
| `spec.sites[].name`                               | Yes               | Site name within the plan (DNS label, at most 40 characters). DR paths and applications refer to it.                                                                    |
| `spec.sites[].cluster`                            | Yes               | Name of the OCM ManagedCluster, equal to `clusterName` of the spoke chart.                                                                                              |
| `spec.sites[].zone`                               | No                | Topology zone the site stands for, if the cluster spans several zones.                                                                                                  |
| `spec.sites[].region`                             | No                | Region, copied into the derived DRCluster.                                                                                                                              |
| `spec.sites[].veleroNamespace`                    | No                | Velero namespace on this site, overriding `spec.veleroNamespace`.                                                                                                       |
| `spec.storageProfile.storageClassSelector`        | Yes               | Label selector for the protected StorageClasses on every site.                                                                                                          |
| `spec.storageProfile.volumeSnapshotClassSelector` | No                | Label selector for the paired VolumeSnapshotClasses. Defaults to the StorageClass selector.                                                                             |
| `spec.storageProfile.consistencyGroups`           | No                | `Enabled` (default) replicates the volumes of an application together with one consistency point (VolumeGroupReplication). `Disabled` replicates each volume by itself. |
| `spec.methods[]`                                  | Yes               | 1 to 8 replication methods.                                                                                                                                             |
| `spec.methods[].name`                             | Yes               | Method name, at most 20 characters. Applications refer to it.                                                                                                           |
| `spec.methods[].type`                             | Yes               | `sync`, `async`, or `snapshot-s3`. See [Replication Types](replication-types.md).                                                                                       |
| `spec.methods[].schedulingInterval`               | For `async`       | Replication interval, for example, `5m`, `1h`, or `1d`. Forbidden for other types.                                                                                      |
| `spec.methods[].snapshotS3.schedule`              | For `snapshot-s3` | Cron expression of the backup schedule.                                                                                                                                 |
| `spec.methods[].snapshotS3.retention`             | For `snapshot-s3` | Number of complete backup sets kept (at least 1).                                                                                                                       |
| `spec.methods[].snapshotS3.s3ProfileName`         | No                | Ramen S3 profile for the backups, overriding the plan's profile.                                                                                                        |
| `spec.methods[].replicationParameters`            | No                | Up to 16 parameters passed verbatim into the derived replication classes.                                                                                               |
| `spec.s3Profile.name`                             | One of            | Name of an existing S3 profile in the Ramen configuration, shared by all sites.                                                                                         |
| `spec.s3Profiles[]`                               | One of            | One S3 store per site, written into the Ramen configuration by `dr-hub`.                                                                                                |
| `spec.veleroNamespace`                            | No                | Velero namespace on the sites.                                                                                                                                          |

The API server rejects a plan that mixes `sync` and `async` methods, lists the same combination of cluster and zone
twice, or has `s3Profiles` that do not cover exactly the sites of the plan.

## Selecting the StorageClasses

The plan selects the protected StorageClasses by label, on every site. Only a selection label is set by the
administrator, for example, `simplyblock.io/replicated: "true"`:

```yaml title="Selecting labeled StorageClasses"
storageProfile:
  storageClassSelector:
    matchLabels:
      simplyblock.io/replicated: "true"
```

`dr-hub` then adds the labels Ramen needs to every selected class on every site, through an OCM ManifestWork
`dr-classes-<plan>` per site:

- **Storage ID:** `ramendr.openshift.io/storageid`, shared by both sites for sync (`sb-sync-<hash>`) and different per
  site for async (`sb-<hash>`).
- **Replication IDs:** `ramendr.openshift.io/replicationid` and `ramendr.openshift.io/groupreplicationid`.
- **Plan label:** `plan.dr.simplyblock.io/<plan>: "true"`.

A VolumeSnapshotClass is only labeled if its driver matches the provisioner of a selected StorageClass. Only PVCs of
selected StorageClasses are replicated. PVCs of other classes in a protected namespace are not protected.

## What dr-hub Derives

From a plan and its paths, `dr-hub` derives:

- **DRCluster:** One Ramen DRCluster per site, named after the site's cluster.
- **DRPolicy:** One Ramen DRPolicy per pair of sites that is connected by at least one DR path, and per `sync` or
  `async` method. The policy is named `<plan>-<siteA>-<siteB>-<method>`, for example, `fra-fra-a-fra-b-async-5m`, and
  carries the labels `dr.simplyblock.io/plan`, `dr.simplyblock.io/pair`, and `dr.simplyblock.io/method`. A
  `snapshot-s3` method derives no DRPolicy.
- **Replication classes:** A VolumeReplicationClass `sb-<plan>-<method>-<hash>` per `async` method on every site,
  with the scheduling interval and the `replicationParameters`. A matching VolumeGroupReplicationClass with the suffix
  `-group` is created next to it. Sync methods need no replication classes.

The derived objects are owned by `dr-hub` and must not be edited. Changes are made in the plan.

### Recreating a DRPolicy

The spec of a Ramen DRPolicy is immutable. If a plan change requires a different DRPolicy (for example, a changed
scheduling interval), the plan reports `DRPolicyDrift`, and the policy is only replaced after confirmation. The
annotation `dr.simplyblock.io/recreate-drpolicies` lists the policies that may be recreated, comma-separated:

```bash title="Confirming the recreation of a DRPolicy"
kubectl annotate protectionplan fra \
  dr.simplyblock.io/recreate-drpolicies=fra-fra-a-fra-b-async-5m
```

A policy is only recreated while no DRPlacementControl uses it. Otherwise, the plan reports `DRPolicyInUse`.
Applications on the old policy have to be protected again under a new ProtectedApplication first.

## S3 Profiles

Ramen keeps the PV and PVC metadata and the Kubernetes object captures of protected applications in an S3 store on
each site. A plan declares the stores in one of two ways:

- **`s3Profiles`:** One store per site, with bucket, endpoint, region, and a credential Secret in the Ramen
  namespace (created by the hub chart, see [Installing the Hub](../install/hub.md)). `dr-hub` writes each store into
  the Ramen configuration as a profile `sb-<hash>`. Plans that name the same store share the profile. This is the
  default for hubs where `dr-hub` manages Ramen.
- **`s3Profile`:** The name of a profile that already exists in the Ramen configuration, shared by all sites. This is
  required on a hub where Ramen is configured by other means, for example, an ACM or ODF hub with
  `bootstrap.enabled=false`.

| Field            | Description                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------|
| `site`           | Site of the plan the store belongs to.                                                        |
| `bucket`         | Bucket name.                                                                                  |
| `endpoint`       | S3 endpoint URL. Any S3-compatible object store is supported.                                 |
| `region`         | Bucket region.                                                                                |
| `secretRef`      | Name of a Secret in the Ramen namespace with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. |
| `caCertificates` | Base64-encoded CA certificates for an endpoint with a private CA.                             |

## Status

```bash title="Listing the protection plans"
kubectl get protectionplans
```

The plan status reports, per site, the derived DRCluster, whether the class labels are applied, and whether the site
agent is available. Per site pair, it lists the paths, the derived DRPolicies, and whether Ramen has resolved the
peer classes. The plan conditions are:

| Condition           | Meaning                                                                                       |
|---------------------|-----------------------------------------------------------------------------------------------|
| `Derived`           | The DRClusters, DRPolicies, and class works are derived without problems.                     |
| `InventoryReady`    | Every site agent has reported its StorageClasses and VolumeSnapshotClasses.                   |
| `S3ProfileResolved` | The S3 profile or the per-site stores are present in the Ramen configuration.                 |
| `Ready`             | All of the above, the class works are applied, and Ramen reports peer classes for every pair. |

A plan that is not `Ready` names the missing part in the condition message, for example, a site without a matching
StorageClass.

## Deleting a Plan

A plan that is still used by protected applications cannot be deleted without confirmation. The annotation
`dr.simplyblock.io/confirm-delete: "true"` confirms the deletion:

```bash title="Confirming the deletion of a plan in use"
kubectl annotate protectionplan fra dr.simplyblock.io/confirm-delete=true
kubectl delete protectionplan fra
```

## Examples

### Asynchronous Replication Between Two Sites

```yaml title="Two sites with asynchronous replication every five minutes (plan-async.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: aws-fra
spec:
  sites:
    - name: site-a
      cluster: site-a
      zone: eu-central-1-a
    - name: site-b
      cluster: site-b
      zone: eu-central-1-b
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/replicated: "true"
  methods:
    - name: async-5m
      type: async
      schedulingInterval: 5m
  s3Profiles:
    - site: site-a
      bucket: dr-site-a
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret-site-a
    - site: site-b
      bucket: dr-site-b
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret-site-b
  veleroNamespace: velero
```

### Synchronous Replication Between Two Datacenters

```yaml title="Metro plan with synchronous replication (plan-metro.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: metro
spec:
  sites:
    - name: dc1
      cluster: ocp-dc1
    - name: dc2
      cluster: ocp-dc2
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/metro: "true"
  methods:
    - name: sync
      type: sync
  s3Profile:
    name: ramen-metro
```

With a DR path from `dc1` to `dc2`, the derived DRPolicy is `metro-dc1-dc2-sync`.

### Three Sites With a Fallback Site

A third site can serve as a one-way fallback, for example, a remote datacenter that only receives failovers. The DR
paths decide which pairs are connected (see [DR Paths](paths.md#three-sites-with-a-one-way-fallback)):

```yaml title="Three sites with two asynchronous methods (plan-eu.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: eu
spec:
  sites:
    - name: fra-a
      cluster: ocp-fra-a
    - name: fra-b
      cluster: ocp-fra-b
    - name: muc-c
      cluster: ocp-muc-c
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/replicated: "true"
  methods:
    - name: async-5m
      type: async
      schedulingInterval: 5m
    - name: async-1h
      type: async
      schedulingInterval: 1h
  s3Profile:
    name: ramen-eu
```

Because the plan has more than one method, every application must set `spec.method`.

### Synchronous Replication With Backups to S3

```yaml title="Metro plan with an additional backup method (plan-metro-backup.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: metro-backup
spec:
  sites:
    - name: dc1
      cluster: ocp-dc1
    - name: dc2
      cluster: ocp-dc2
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/metro: "true"
    consistencyGroups: Disabled
  methods:
    - name: sync
      type: sync
    - name: backup-5m
      type: snapshot-s3
      snapshotS3:
        schedule: "*/5 * * * *"
        retention: 3
  s3Profile:
    name: ramen-metro
```

### Passing Parameters to the CSI Driver

`replicationParameters` are copied verbatim into the derived VolumeReplicationClass and VolumeGroupReplicationClass.
They are the contract with the CSI driver, for example, a reference to the replication secret:

```yaml title="Asynchronous plan with replication parameters (plan-fra.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: fra
spec:
  sites:
    - name: fra-a
      cluster: ocp-fra-a
      zone: fra-a
      region: eu-central
    - name: fra-b
      cluster: ocp-fra-b
      zone: fra-b
      region: eu-central
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/replicated: "true"
  methods:
    - name: async-5m
      type: async
      schedulingInterval: 5m
      replicationParameters:
        replication.storage.openshift.io/replication-secret-name: sb-replication
        replication.storage.openshift.io/replication-secret-namespace: simplyblock
  s3Profile:
    name: ramen-fra
```

The resulting VolumeReplicationClass on each site looks as follows:

```yaml title="VolumeReplicationClass derived by dr-hub"
apiVersion: replication.storage.openshift.io/v1alpha1
kind: VolumeReplicationClass
metadata:
  name: sb-fra-async-5m-eeb847e1cb66
  labels:
    dr.simplyblock.io/method: async-5m
    dr.simplyblock.io/plan: fra
    ramendr.openshift.io/replicationid: sb-async
    ramendr.openshift.io/storageid: sb-11526c617486
spec:
  provisioner: csi.simplyblock.io
  parameters:
    replication.storage.openshift.io/replication-secret-name: sb-replication
    replication.storage.openshift.io/replication-secret-namespace: simplyblock
    schedulingInterval: 5m
```
