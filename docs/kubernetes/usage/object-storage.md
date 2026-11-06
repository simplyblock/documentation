---
title: "S3 Object Storage"
description: "Deploy an S3 gateway with the ObjectStore resource, provision buckets, and manage user accounts and bucket permissions on Kubernetes."
weight: 40700
---

S3 object storage is served by a gateway, deployed as an `ObjectStore` resource. The gateway embeds
[VersityGW](https://github.com/versity/versitygw){:target="_blank" rel="noopener"} with a POSIX backend, and every
bucket it serves is backed by its own simplyblock volume: an `S3Bucket` resource, created either directly or by the
gateway in response to an S3 `CreateBucket` request.

## Deploying an ObjectStore

An `ObjectStore` is the desired existence of one S3 gateway: a `Deployment` running the gateway, a `ClusterIP`
`Service` in front of it, and that `Service`'s serving certificate. `spec.buckets` is what every bucket created
through the S3 API is provisioned with, since a `CreateBucket` request carries no size or storage class of its own.
The storage class it names must select the `pnfs` fstype (see [Storage Class](storage-class.md)), the same
requirement `ReadWriteMany` volumes carry, because every gateway pod needs the same bucket volume mounted at once.

```yaml title="Example of an ObjectStore resource"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ObjectStore
metadata:
  name: team-a-store
  namespace: s3-system
spec:
  image: quay.io/simplyblock-io/simplyblock-s3-gateway:main
  port: 9000
  replicas: 3
  tlsProvider: cert-manager
  envFrom:
    - secretRef:
        name: team-a-store-credentials
  buckets:
    storageClassName: simplyblock-pnfs
    capacityBytes: 10737418240
```

The gateway reads its root account, and optionally its Vault configuration, only from `spec.envFrom`, never from a
field the operator sets. A `Secret` carrying `ROOT_ACCESS_KEY_ID` and `ROOT_SECRET_ACCESS_KEY` is required: the
gateway refuses to start without a root account.

```yaml title="Example of the credentials Secret an ObjectStore's envFrom references"
apiVersion: v1
kind: Secret
metadata:
  name: team-a-store-credentials
type: Opaque
stringData:
  ROOT_ACCESS_KEY_ID: simplyblock
  ROOT_SECRET_ACCESS_KEY: simplyblock
```

An `ObjectStore` reaches `Ready` once its `Deployment` reports available and its certificate is issued.

```bash title="Checking an ObjectStore's provisioning phase"
kubectl get objectstore team-a-store -n s3-system
```

```plain title="Example output of an ObjectStore that has converged"
NAME            PHASE   REPLICAS   READY   AGE
team-a-store    Ready   3          3       4m12s
```

Reaching the gateway's `Service` from outside the cluster is not something `ObjectStore` configures. An Ingress, a
Gateway API route, or a cloud load balancer is placed in front of it the same way as for any other cluster-internal
`Service`.

## Creating buckets

A bucket is an `S3Bucket` resource: its own backing volume, a pNFS export, and the mount delivered to every pod of
the `ObjectStore` named in `spec.objectStoreRef`. It can be created directly, or implicitly by an S3 client's
`CreateBucket` call against the gateway.

```yaml title="Example of an S3Bucket resource created directly"
apiVersion: storage.simplyblock.io/v1alpha2
kind: S3Bucket
metadata:
  name: team-a-reports
  namespace: s3-system
spec:
  objectStoreRef: team-a-store
  bucketName: reports
  capacityBytes: 5368709120
  storageClassName: simplyblock-pnfs
```

```bash title="Creating a bucket through the S3 API instead"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api create-bucket --bucket reports
```

`spec.objectStoreRef`, `spec.bucketName`, and `spec.storageClassName` are immutable: a bucket does not move between
gateways, and its S3 name and storage class are fixed at creation. `spec.capacityBytes` can be raised, which
reconciles to a `PersistentVolumeClaim` expansion, but not lowered.

## Managing user accounts

A gateway's accounts are not stored by this project. They live in the Vault-backed IAM backend built into
VersityGW, configured by setting `VGW_IAM_VAULT_ENDPOINT_URL` and the matching `VGW_IAM_VAULT_*` variables in the
`Secret` referenced by `spec.envFrom`. Without a Vault endpoint, the gateway serves only its root account.

Each account is one entry in Vault, keyed by its S3 access key, carrying its secret key and a role: `user`,
`admin`, or `userplus`. An access key has the same shape AWS itself uses, `AKIA` followed by 17 characters, and the
access key is also the identity used everywhere else: as the owner and grantee of a bucket ACL, and as the
principal matched by a bucket policy.

Accounts are managed through the gateway's admin API, served on the same port as the S3 API, authenticated the
same way an S3 request is (a SigV4-signed request from the root account or from any `admin`-role account). The
[VersityGW admin CLI](https://github.com/versity/versitygw){:target="_blank" rel="noopener"} is a client for that
API:

```bash title="Creating an account with access to the gateway's S3 API"
versitygw admin --endpoint-url https://team-a-store.s3-system.svc:9000 \
    --access simplyblock --secret simplyblock \
    create-user --access AKIAEXAMPLEUSERBKEY --secret '<secret>' --role user
```

```bash title="Listing the accounts a gateway currently holds"
versitygw admin --endpoint-url https://team-a-store.s3-system.svc:9000 \
    --access simplyblock --secret simplyblock \
    list-users
```

A changed or deleted account takes effect on a gateway replica only after its IAM cache expires
(`VGW_IAM_CACHE_TTL`, 120 seconds by default): a revoked key keeps working on another replica for up to that long.

## Granting access to another user's bucket

Bucket ownership and ACLs are not stored in Vault either. They are kept as extended attributes on the bucket's own
volume, so they travel with the bucket rather than with a central permissions table. A bucket's owner is the access
key of the account whose `CreateBucket` request created it. Granting another account access means adding that
account's access key as a grantee on the bucket's ACL.

```bash title="Granting another account read access to a bucket, by its access key"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api put-bucket-acl --bucket reports \
    --grant-read 'id=AKIAEXAMPLEUSERBKEY'
```

```bash title="Reading back a bucket's current owner and grantees"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api get-bucket-acl --bucket reports
```

A bucket policy, scoped to a `Principal` naming one or more access keys, is the alternative to an ACL grant when
the permission needs to be conditional or needs to cover more than the canned ACL permissions (`READ`, `WRITE`,
`READ_ACP`, `WRITE_ACP`, `FULL_CONTROL`).
