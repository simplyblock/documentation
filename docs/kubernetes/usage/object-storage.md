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
`capacityBytes` there is the size given to each such bucket, not a total pool shared between them. The storage class
it names must select the `pnfs` fstype (see [Creating a pNFS StorageClass](pnfs.md#creating-a-pnfs-storageclass)),
the same requirement `ReadWriteMany` volumes carry, because every gateway pod needs the same bucket volume mounted
at once. It also needs `volumeBindingMode: Immediate`, since no pod ever mounts a bucket's claim directly: under the
default `WaitForFirstConsumer` the claim never binds and the bucket stays `Pending`. pNFS itself carries its own
cluster requirements, in particular a metadata-server-capable node and `/dev/kvm` (see
[Requirements](pnfs.md#requirements)).

`spec.region` defaults to `us-east-1` and is the only region the gateway's S3 API accepts: a request signed for any
other region is rejected with `AuthorizationHeaderMalformed`, including from an AWS CLI profile whose own default
region differs.

`spec.tlsProvider` defaults to `OpenShift`, which relies on the cluster's `service-ca-operator` and issues nothing on
a plain Kubernetes cluster. The example below selects `cert-manager` instead, which makes the operator request a
`Certificate` against the `ClusterIssuer` named `simplyblock-certificate-authority-issuer`. That `ClusterIssuer` has
to already exist, or the `ObjectStore` goes `Degraded`.

```yaml title="Example of an ObjectStore resource"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ObjectStore
metadata:
  name: team-a-store
  namespace: s3-system
spec:
  # Pin an actual released tag rather than tracking a moving one.
  image: docker.io/simplyblock/gateway:<tag>
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
  namespace: s3-system
type: Opaque
stringData:
  ROOT_ACCESS_KEY_ID: <access-key>
  ROOT_SECRET_ACCESS_KEY: <secret-key>
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
`CreateBucket` call against the gateway. The two examples below are alternatives for the same bucket, not steps to
run one after the other: a `CreateBucket` call against `invoices` would collide with the `S3Bucket` already created
for it.

```yaml title="Example of an S3Bucket resource created directly"
apiVersion: storage.simplyblock.io/v1alpha2
kind: S3Bucket
metadata:
  name: team-a-invoices
  namespace: s3-system
spec:
  objectStoreRef: team-a-store
  bucketName: invoices
  capacityBytes: 5368709120
  storageClassName: simplyblock-pnfs
```

```bash title="Creating a different bucket through the S3 API instead"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api create-bucket --bucket reports
```

A bucket created through the S3 API gets an `S3Bucket` resource named after the bucket itself. Most S3-legal bucket
names are also valid Kubernetes object names, but not all are (one with a period next to a hyphen, for example, is
not), and such a name is refused.

`spec.objectStoreRef`, `spec.bucketName`, and `spec.storageClassName` are immutable: a bucket does not move between
gateways, and its S3 name and storage class are fixed at creation. `spec.capacityBytes` can be raised, which
reconciles to a `PersistentVolumeClaim` expansion, but not lowered.

An `S3Bucket` created directly, unlike one created through `CreateBucket`, has no owner: nothing sets its ACL, so
only the gateway's root account can manage it, until the root account grants another account access the same way
described [below](#granting-access-to-another-users-bucket).

Deleting a bucket, through either `DeleteBucket` or by deleting its `S3Bucket` resource directly, deletes the
`S3Bucket`. What happens to the underlying volume and its data from there follows the storage class's
`reclaimPolicy`, the same as for any other simplyblock volume.

## Managing user accounts

A gateway's accounts are not stored by simplyblock. They live in the Vault-backed IAM backend built into
VersityGW, configured by setting `VGW_IAM_VAULT_ENDPOINT_URL` and the matching `VGW_IAM_VAULT_*` variables in the
`Secret` referenced by `spec.envFrom`. Without a Vault endpoint, the gateway serves only its root account.

Each account is one entry in Vault, keyed by its S3 access key, carrying its secret key and a role: `user`, `admin`,
or `userplus`. The gateway enforces no particular shape on an access key: it is a free-form string. The access key
is also the identity used everywhere else, as the owner and grantee of a bucket ACL and as the principal matched by
a bucket policy.

The role decides what the account may do beyond its own data. An `admin` account can manage other accounts and
bypasses bucket ACLs and policies entirely. A `userplus` account additionally may call `CreateBucket`, which a plain
`user` account cannot: that call gets `AccessDenied` instead. The root account behaves like `admin` without being a
Vault entry at all.

Accounts are managed through the gateway's admin API, served on the same port as the S3 API, authenticated the
same way an S3 request is (a SigV4-signed request from the root account or from any `admin`-role account). The
[VersityGW admin CLI](https://github.com/versity/versitygw/wiki/Admin-APIs){:target="_blank" rel="noopener"} is a
client for that API. The API is served over the gateway's cluster-issued certificate, so a client that does not
already trust it has to be told how: `aws` takes `--ca-bundle`. `versitygw admin` has no equivalent
certificate-pinning flag and takes `--allow-insecure`, which skips verification instead.

```bash title="Creating an account with access to the gateway's S3 API, as root"
versitygw admin --endpoint-url https://team-a-store.s3-system.svc:9000 \
    --access <root-access-key> --secret <root-secret-key> \
    create-user --access <access-key> --secret <secret-key> --role user
```

```bash title="Listing the accounts a gateway currently holds, as root"
versitygw admin --endpoint-url https://team-a-store.s3-system.svc:9000 \
    --access <root-access-key> --secret <root-secret-key> \
    list-users
```

A changed or deleted account takes effect on a gateway replica only after its IAM cache expires
(`VGW_IAM_CACHE_TTL`, 120 seconds by default): a revoked key keeps working on another replica for up to that long.

## Granting access to another user's bucket

Bucket ownership and ACLs are not stored in Vault either. They are kept as extended attributes on the bucket's own
volume, so they travel with the bucket rather than with a central permissions table. A bucket's owner is the access
key of the account whose `CreateBucket` request created it. Granting another account access means adding that
account's access key as a grantee on the bucket's ACL, a request the bucket's owner or root has to issue.

`CreateBucket` with no `--object-ownership` defaults a bucket to `BucketOwnerEnforced`, under which `put-bucket-acl`
is rejected outright (`AccessControlListNotSupported`), ACLs being meaningless once every object is unconditionally
owned by the bucket owner. Granting through an ACL needs ownership controls that still allow one, set either at
creation or before the grant:

```bash title="Allowing ACLs on a bucket already created with the default ownership"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api put-bucket-ownership-controls --bucket reports \
    --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerPreferred}]'
```

```bash title="Granting another account read access to a bucket, by its access key"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api put-bucket-acl --bucket reports \
    --grant-read 'id=<access-key>'
```

```bash title="Reading back a bucket's current owner and grantees"
aws --endpoint-url https://team-a-store.s3-system.svc:9000 \
    s3api get-bucket-acl --bucket reports
```

A bucket policy, scoped to a `Principal` naming one or more access keys, is the alternative to an ACL grant when the
permission needs to be conditional, needs to cover more than the canned ACL permissions (`READ`, `WRITE`,
`READ_ACP`, `WRITE_ACP`, `FULL_CONTROL`), or when the bucket keeps the default `BucketOwnerEnforced` ownership:
unlike an ACL grant, a bucket policy works under it unchanged.
