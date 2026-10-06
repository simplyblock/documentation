---
title: "Protection Plans"
description: "Declare sites, protected StorageClasses, replication methods, and S3 stores with a ProtectionPlan, and monitor its readiness and conditions."
source: "https://docs.simplyblock.io/latest/disaster-recovery/configuration/protection-plans/"
---

# Protection Plans

A ProtectionPlan is the cluster-scoped resource that defines a disaster recovery topology: which site clusters take
part, which StorageClasses are protected, which replication methods are available, and where each site keeps its
recovery metadata in S3. Together with its [DR paths](paths.md), a plan is all the replication configuration a
topology needs. Protection plans are written by the `dr-admin` role.

The concepts behind plans are explained in [Protection Plans and Paths](../../architecture/concepts/dr-protection-plans.md).

## Specification

| Field                                             | Required         | Description                                                                                                                                                             |
|---------------------------------------------------|------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `metadata.name`                                   | Yes              | Plan name, at most 40 characters.                                                                                                                                       |
| `spec.sites[]`                                    | Yes              | 2 to 16 sites.                                                                                                                                                          |
| `spec.sites[].name`                               | Yes              | Site name within the plan (DNS label, at most 40 characters). DR paths and applications refer to it.                                                                    |
| `spec.sites[].cluster`                            | Yes              | Name of the OCM ManagedCluster, equal to `clusterName` of the spoke chart.                                                                                              |
| `spec.sites[].zone`                               | For `sync`       | Topology zone the site stands for (node label `topology.kubernetes.io/zone`). The sites of a sync plan are the zones of one cluster; optional for async plans.          |
| `spec.sites[].region`                             | No               | Region of the site.                                                                                                                                                     |
| `spec.sites[].veleroNamespace`                    | No               | Velero namespace on this site, overriding `spec.veleroNamespace`.                                                                                                       |
| `spec.storageProfile.storageClassSelector`        | Yes              | Label selector for the protected StorageClasses on every site.                                                                                                          |
| `spec.storageProfile.volumeSnapshotClassSelector` | No               | Label selector for the paired VolumeSnapshotClasses. Defaults to the StorageClass selector.                                                                             |
| `spec.storageProfile.consistencyGroups`           | No               | `Enabled` replicates the volumes of an application together with one consistency point (VolumeGroupReplication). `Disabled` (default) replicates each volume by itself. |
| `spec.storageProfile.groupStorageClassSelector`   | No               | With consistency groups enabled, the StorageClasses whose PVCs form groups. Unset means every selected class.                                                           |
| `spec.methods[]`                                  | Yes              | 1 to 8 replication methods.                                                                                                                                             |
| `spec.methods[].name`                             | Yes              | Method name, at most 20 characters. Applications refer to it.                                                                                                           |
| `spec.methods[].type`                             | Yes              | `sync`, `async`, `s3-backup`, `sync-s3-backup`, or `async-s3-backup`. See [Replication Types](replication-types.md).                                                    |
| `spec.methods[].schedulingInterval`               | For async types  | Replication interval of `async` and `async-s3-backup`, for example, `5m`, `1h`, or `1d`.                                                                                |
| `spec.methods[].s3Backup.interval`                | For backup types | Backup interval of `s3-backup`, `sync-s3-backup`, and `async-s3-backup`, in the same notation.                                                                          |
| `spec.methods[].s3Backup.retention`               | For backup types | Number of backups kept per volume (at least 1).                                                                                                                         |
| `spec.methods[].replicationParameters`            | No               | Up to 16 parameters passed verbatim to the CSI driver.                                                                                                                  |
| `spec.s3Profile.name`                             | One of           | Name of an existing S3 profile, shared by all sites.                                                                                                                    |
| `spec.s3Profiles[]`                               | One of           | One S3 store per site.                                                                                                                                                  |
| `spec.veleroNamespace`                            | No               | Velero namespace on the sites.                                                                                                                                          |
| `spec.autoRestart.enabled`, `.stableFor`          | No               | Restarts the plan's applications in place after their storage cluster recovers from a suspension. See [Restart After a Storage Recovery](../operations/restart.md).     |

The API server rejects a plan that mixes synchronous and asynchronous methods, puts the sites of a sync plan on
different clusters or leaves their zone empty, lists the same combination of cluster and zone twice, or has
`s3Profiles` that do not cover exactly the sites of the plan. A plan written for the earlier `snapshot-s3` method
type is refused.

## Selecting the StorageClasses

The plan selects the protected StorageClasses by label, on every site. Only a selection label is set by the
administrator, for example, `simplyblock.io/replicated: "true"`:

```yaml title="Selecting labeled StorageClasses"
storageProfile:
  storageClassSelector:
    matchLabels:
      simplyblock.io/replicated: "true"
```

A VolumeSnapshotClass is only used if its driver matches the provisioner of a selected StorageClass. Only PVCs of
selected StorageClasses are replicated. PVCs of other classes in a protected namespace are not protected.

## Changing the Replication Settings

Some plan changes, for example, a changed scheduling interval, cannot be applied in place. The plan then reports
`DRPolicyDrift`, and the change is only applied after confirmation. The condition message names the annotation
`dr.simplyblock.io/recreate-drpolicies` and the value that confirms the change:

```bash title="Confirming a replication settings change"
kubectl annotate protectionplan fra \
  dr.simplyblock.io/recreate-drpolicies=fra-fra-a-fra-b-async-5m
```

The change is only applied while no protected application uses the affected replication settings. Otherwise, the plan
reports `DRPolicyInUse`. Applications on the old settings have to be protected again under a new ProtectedApplication
first.

## S3 Profiles

The PV and PVC metadata and the Kubernetes object captures of protected applications are kept in a DR metadata bucket
on each site. These S3 profiles configure only those buckets. The archive bucket of the hub is configured with the hub
installation, and the simplyblock backup buckets with the storage clusters (see
[S3 Buckets](../../deployment-preparation/dr-requirements.md#s3-buckets)). A plan declares the stores in one of two ways:

- **`s3Profiles`:** One store per site, with bucket, endpoint, region, and a credential Secret in the Ramen
  namespace (created by the hub chart, see [Installing the Hub](../install/hub.md)). Plans that name the same store
  share it. This is the default for hubs installed with the hub chart, and the only option for the backup method
  types, whose backups the storage writes into the site's store.
- **`s3Profile`:** The name of an S3 profile that already exists on the hub, shared by all sites. This is required on
  a hub where the S3 profiles are configured by other means, for example, an ACM or ODF hub with
  `bootstrap.enabled=false`.

| Field            | Description                                                                                                                                 |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `site`           | Site of the plan the store belongs to.                                                                                                      |
| `bucket`         | Bucket name.                                                                                                                                |
| `endpoint`       | S3 endpoint URL. Any S3-compatible object store is supported.                                                                               |
| `region`         | Bucket region.                                                                                                                              |
| `secretRef`      | Name of a Secret in the Ramen namespace with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, usually `ramen-s3-secret` from the hub chart. |
| `caCertificates` | Base64-encoded CA certificates for an endpoint with a private CA.                                                                           |

## Status

```bash title="Listing the protection plans"
kubectl get protectionplans
```

The plan status reports, per site, whether the StorageClasses are prepared and whether the site agent is available.
Per site pair, it lists the paths and whether replication between the pair is ready. The plan conditions are:

| Condition           | Meaning                                                                     |
|---------------------|-----------------------------------------------------------------------------|
| `Derived`           | The replication configuration of the plan is complete and without problems. |
| `InventoryReady`    | Every site agent has reported its StorageClasses and VolumeSnapshotClasses. |
| `S3ProfileResolved` | The S3 profile or the stores of all sites are configured.                   |
| `Ready`             | All of the above, and replication is ready for every connected site pair.   |

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
      bucket: dr-metadata
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret
    - site: site-b
      bucket: dr-metadata
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret
  veleroNamespace: velero
```

### Synchronous Replication Between the Zones of a Stretch Cluster

The sites of a sync plan are the zones of one cluster with a stretched simplyblock storage cluster underneath:

```yaml title="Stretch cluster plan with synchronous replication (plan-metro.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: metro
spec:
  sites:
    - name: dc1
      cluster: ocp-stretch
      zone: dc1
    - name: dc2
      cluster: ocp-stretch
      zone: dc2
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

### Asynchronous Replication With Backups to S3

A combined method is one method. The storage replicates every five minutes and backs every primary volume up to the
site's store every hour, keeping 24 backups:

```yaml title="Asynchronous plan with backups (plan-fra-backup.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: fra-backup
spec:
  sites:
    - name: fra-a
      cluster: ocp-fra-a
    - name: fra-b
      cluster: ocp-fra-b
  storageProfile:
    storageClassSelector:
      matchLabels:
        simplyblock.io/replicated: "true"
  methods:
    - name: async-5m-backup
      type: async-s3-backup
      schedulingInterval: 5m
      s3Backup:
        interval: 1h
        retention: 24
  s3Profiles:
    - site: fra-a
      bucket: dr-metadata-fra-a
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret
    - site: fra-b
      bucket: dr-metadata-fra-b
      endpoint: https://s3.eu-central-1.amazonaws.com
      region: eu-central-1
      secretRef: ramen-s3-secret
  autoRestart:
    enabled: true
```

### Passing Parameters to the CSI Driver

`replicationParameters` are passed verbatim to the CSI driver. On simplyblock storage, nothing has to be passed:
dr-hub derives the backend pairing, the replication policy, the per-direction class parameters, and the replication
Secret itself (see [Replication Types](replication-types.md#asynchronous-replication)). The parameters are the
contract with another CSI driver, for example, a reference to its replication secret:

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
