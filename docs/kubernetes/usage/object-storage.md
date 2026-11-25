---
title: "S3 Object Storage"
description: "Run the simplyblock S3-compatible gateway (beta) on Kubernetes: the ObjectStore and S3Bucket resources, credentials, TLS, and bucket capacity."
weight: 40085
---

Object storage is in beta. An S3-compatible gateway is run by the `ObjectStore` resource as a Deployment behind a
ClusterIP Service. Each bucket is an `S3Bucket` resource, backed by a pNFS volume of its own, which is mounted into
every gateway pod. The capacity of a bucket is the size of its volume.

## Requirements

- **pNFS:** The metadata server is enabled, and a pNFS StorageClass exists, as described in
  [ReadWriteMany Volumes](pnfs.md). The StorageClass must set `allowVolumeExpansion: true` for buckets to grow. The
  nodes running gateway pods mount the bucket volumes as pNFS clients, so the
  [client requirements](pnfs.md#requirements) apply to them.
- **Gateway image:** `spec.image` has no default, because the gateway is not released together with the operator.
- **TLS:** The gateway serves TLS only. Its certificate is issued either by the OpenShift service CA or by
  cert-manager, through the ClusterIssuer `simplyblock-certificate-authority-issuer`, which must exist.

## Credentials

The gateway reads its credentials from its environment, which is filled from the Secrets and ConfigMaps listed in
`spec.envFrom`. The operator injects no credentials. Without `ROOT_ACCESS_KEY_ID` and `ROOT_SECRET_ACCESS_KEY`, the
gateway does not start.

```yaml title="Example of the gateway credentials Secret (objectstore-credentials.yaml)"
apiVersion: v1
kind: Secret
metadata:
  name: objectstore-credentials
  namespace: team-a
type: Opaque
stringData:
  ROOT_ACCESS_KEY_ID: <ACCESS_KEY>
  ROOT_SECRET_ACCESS_KEY: <SECRET_KEY>
```

Without further settings, the gateway serves the root account only. Additional accounts are kept in HashiCorp Vault
or OpenBao, enabled by `VGW_IAM_VAULT_ENDPOINT_URL` and the other `VGW_IAM_VAULT_*` variables in the same Secret.

## Creating an ObjectStore

```yaml title="Example of an ObjectStore (objectstore.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ObjectStore
metadata:
  name: s3
  namespace: team-a
spec:
  image: <GATEWAY_IMAGE>
  port: 9000
  replicas: 2
  tlsProvider: cert-manager
  envFrom:
    - secretRef:
        name: objectstore-credentials
  buckets:
    storageClassName: simplyblock-shared
    capacityBytes: 107374182400
```

| Field                      | Description                                                                                                                                   | Default     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| `image`                    | Gateway image. Required.                                                                                                                      | -           |
| `imagePullPolicy`          | `Always`, `IfNotPresent`, or `Never`.                                                                                                         | `Always`    |
| `port`                     | Container port and Service port. Required. See below.                                                                                         | -           |
| `region`                   | Region the S3 API answers to. Clients must sign their requests for exactly this region.                                                       | `us-east-1` |
| `replicas`                 | Number of gateway pods. No two of them run on the same node, so a pod without a free node stays `Pending`.                                    | `1`         |
| `nodeSelector`             | Node labels the gateway pods are scheduled by.                                                                                                | -           |
| `tolerations`              | Tolerations for tainted nodes.                                                                                                                | -           |
| `resources`                | Requests and limits of the gateway container.                                                                                                 | No limits   |
| `envFrom`                  | Secrets and ConfigMaps injected into the gateway's environment unchanged.                                                                     | -           |
| `tlsProvider`              | Issuer of the Service's serving certificate: `OpenShift` (the service CA) or `cert-manager`. Outside OpenShift, `cert-manager` has to be set. | `OpenShift` |
| `buckets.storageClassName` | pNFS StorageClass of every bucket created through the S3 API. Required.                                                                       | -           |
| `buckets.capacityBytes`    | Capacity of every bucket created through the S3 API, per bucket. Required.                                                                    | -           |

`spec.port` sets the container port and the Service port, but it is not passed to the gateway. The gateway listens on
`VGW_PORT`, `:9000` by default. A port other than 9000 therefore requires `VGW_PORT` with the same port in the Secret,
for example, `VGW_PORT: ":9443"` for `port: 9443`.

The Deployment, the Service, and the gateway's ServiceAccount are named after the ObjectStore. The gateway is reached
in the cluster at `https://<NAME>.<NAMESPACE>.svc:<PORT>`. A renewed certificate is served without a restart.

The ObjectStore turns `Ready` once the Deployment is available and the certificate is issued. When either does not
happen within five minutes, it turns `Degraded`, with the cause in its `DeploymentAvailable` or `CertificateReady`
condition. A Degraded ObjectStore is provisioned again when a Secret or ConfigMap from `spec.envFrom` is created or
changed, or when the certificate turns ready.

```bash title="Listing the object stores and buckets of a namespace"
kubectl get objectstores,s3buckets -n team-a
```

An ObjectStore is deleted only after every S3Bucket referencing it is gone. Until then, its `BucketsRemaining`
condition names the remaining buckets.

## Creating Buckets

A bucket is created in one of two ways:

- **Through the S3 API:** A `CreateBucket` request to the gateway creates an S3Bucket in the ObjectStore's namespace,
  named after the bucket, with the StorageClass and capacity from `spec.buckets`. The request waits for the bucket to
  turn `Ready`, for at most five minutes (`GATEWAY_BUCKET_TIMEOUT`), and the S3Bucket is deleted again when it does
  not. A bucket name that is not a valid Kubernetes object name, such as one with a period next to a hyphen, is
  refused.
- **As an S3Bucket resource:** An S3Bucket created directly sets its own capacity and StorageClass.

```yaml title="Example of an S3Bucket (s3bucket.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: S3Bucket
metadata:
  name: reports
  namespace: team-a
spec:
  objectStoreRef: s3
  bucketName: reports
  capacityBytes: 53687091200
  storageClassName: simplyblock-shared
```

| Field              | Description                                                                                                    |
|--------------------|----------------------------------------------------------------------------------------------------------------|
| `objectStoreRef`   | ObjectStore in the same namespace whose gateway serves the bucket. Immutable.                                  |
| `bucketName`       | S3 bucket name, following the S3 naming rules. Immutable.                                                      |
| `capacityBytes`    | Capacity of the bucket's volume. It can be raised, but not lowered.                                            |
| `storageClassName` | StorageClass of the bucket's volume. It must be a pNFS StorageClass, or the bucket stays `Pending`. Immutable. |

For every bucket, a `ReadWriteMany` PersistentVolumeClaim is created in the bucket's namespace, normally named
`s3bucket-<BUCKET_NAME>`. Once it is bound and exported, the volume is mounted on every node that runs a gateway pod,
and the bucket turns `Ready`. A bucket that does not get there within five minutes turns `Degraded` and stays so. It has to be
deleted and created again.

## Growing a Bucket

A bucket grows when `spec.capacityBytes` of its S3Bucket is raised. The PersistentVolumeClaim is expanded, and the
bucket stays `Ready` meanwhile. When the StorageClass does not allow expansion, the S3Bucket receives a
`CapacityExpansionRefused` event. A write to a full bucket is answered with `507 InsufficientStorage`.

`spec.buckets.capacityBytes` of the ObjectStore only applies to buckets created afterward. It does not grow existing
buckets.

## Deleting a Bucket

A bucket is deleted through the S3 `DeleteBucket` request or by deleting its S3Bucket. The volume is unmounted from
the gateway nodes, and the PersistentVolumeClaim is deleted. What happens to the data follows the reclaim policy of
the StorageClass.

## Limitations

- Object versioning is not supported. A `PutBucketVersioning` request is answered with `VersioningNotConfigured`.
- The gateway is exposed inside the cluster only, through its ClusterIP Service. An Ingress, a Route, or a
  LoadBalancer in front of it is not created by the operator.
- A changed Secret or ConfigMap in `spec.envFrom` is not rolled out to running gateway pods. New credentials, such as
  rotated root keys, take effect once the pods are restarted.
