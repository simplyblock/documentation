---
title: "Archive and State Bundle"
description: "Configure the S3 archive for DR reports, the signing key, and the signed DR state bundle that is used to rebuild a lost hub cluster."
weight: 10120
---

The hub cluster holds the complete DR configuration: protection plans, paths, applications, and the Ramen objects
derived from them. To survive the loss of the hub itself, `dr-hub` writes this state as a signed DR state bundle to an
S3 archive. The same archive stores the report of every finished recovery action and test.

The archive is configured in `DRConfig.spec.archive`. Without an archive, no bundles and no reports are written, and
finished runs are never pruned from the hub.

## What the Archive Contains

All keys are written below the configured prefix (default `dr/`):

| Key                                                                            | Content                                                          |
|--------------------------------------------------------------------------------|------------------------------------------------------------------|
| `<prefix>bundle/<generation>.tar`                                              | One DR state bundle per state generation.                        |
| `<prefix>bundle/<generation>.sig`                                              | The ed25519 signature of the bundle.                             |
| `<prefix>reports/<namespace>/<kind>/<yyyy>/<mm>/<completed>-<name>-<uid>.pdf`  | The report of a finished recovery action or test, as PDF.        |
| `<prefix>reports/<namespace>/<kind>/<yyyy>/<mm>/<completed>-<name>-<uid>.json` | The same report as JSON (`schema: dr.simplyblock.io/report/v1`). |

A DR state bundle contains:

- **DR configuration:** The `DRConfig` and all DR objects (protection plans, DR paths, protected applications,
  recovery plans, and test schedules).
- **OCM intent:** The managed clusters and cluster sets the hub expects.
- **Ramen state:** The Ramen hub configuration, DRCluster, DRPolicy, and DRPlacementControl objects, and the
  Placements with their decisions.
- **Generated Recipes:** The Ramen Recipes that `dr-hub` generated for discovered applications.

A bundle never contains Secrets and no finished runs. The S3 credentials, the archive credential, and the signing key
must be kept in a separate, safe location and restored manually after a hub loss (see
[Recovering the Hub](../operations/hub-recovery.md)).

The hub checks every 5 minutes (`bundle.interval`) whether its DR state has changed and writes a new bundle only when
it has.

## Preparing the Signing Key

Every bundle is signed with an ed25519 key. When the hub is rebuilt, `dr-restore` refuses any bundle that does not
verify against the public key. The key pair is generated with `dr-restore keygen`. The `dr-restore` binary is part of
the `dr-hub` image:

```bash title="Generating the bundle signing key pair"
mkdir -p keys
docker run --rm --entrypoint dr-restore -v "$PWD/keys:/keys" \
  quay.io/simplyblock-io/dr-hub:<version> keygen -out /keys
```

The command writes `bundle-signing.key` (the private key, PKCS#8 PEM) and `bundle-signing.pub` (the public key) and
prints the key fingerprint.

## Creating the Secrets

The archive needs two Secrets in the `dr-simplyblock` namespace: the S3 credential the hub writes with, and the
private signing key.

```bash title="Creating the archive credential and the signing key Secrets"
kubectl -n dr-simplyblock create secret generic dr-archive \
  --from-literal=AWS_ACCESS_KEY_ID=<access key id> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<secret access key>

kubectl -n dr-simplyblock create secret generic dr-bundle-key \
  --from-file=ed25519.key=keys/bundle-signing.key
```

The signing key must be stored under the key `ed25519.key`.

## Configuring the Archive

The archive is set in the hub chart values (`drConfig.spec.archive`) or directly in the `DRConfig`:

```yaml title="Archive configuration in the DRConfig (drconfig-archive.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRConfig
metadata:
  name: default
spec:
  archive:
    endpoint: s3.eu-central-1.amazonaws.com
    bucket: dr-archive
    region: eu-central-1
    prefix: dr/
    credentialsSecretRef:
      name: dr-archive
    reportRetainDays: 0
    bundle:
      interval: 5m
      retainDays: 30
      signingKeySecretRef:
        name: dr-bundle-key
  retention:
    days: 90
    keepPerApplication: 10
```

| Field                                     | Default  | Description                                                                                    |
|-------------------------------------------|----------|------------------------------------------------------------------------------------------------|
| `archive.endpoint`                        | Required | S3 endpoint as `host[:port]`, without a scheme. Any S3-compatible object store is supported.   |
| `archive.bucket`                          | Required | Archive bucket.                                                                                |
| `archive.region`                          | Empty    | Bucket region.                                                                                 |
| `archive.prefix`                          | `dr/`    | Prefix of every key.                                                                           |
| `archive.insecure`                        | `false`  | Uses plain HTTP instead of HTTPS.                                                              |
| `archive.credentialsSecretRef.name`       | Required | Secret in the `dr-simplyblock` namespace with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. |
| `archive.reportRetainDays`                | `0`      | Object lock retention of each report in days. `0` writes reports without an object lock.       |
| `archive.bundle.disabled`                 | `false`  | Stops writing bundles. Reports are still written.                                              |
| `archive.bundle.interval`                 | `5m`     | How often the hub checks its DR state for changes.                                             |
| `archive.bundle.retainDays`               | `30`     | Object lock retention of each bundle in days. Requires a bucket with object lock enabled.      |
| `archive.bundle.signingKeySecretRef.name` | Required | Secret in the `dr-simplyblock` namespace with the private key under `ed25519.key`.             |

The `DRConfig` status shows the last bundle written:

```bash title="Checking the last written bundle"
kubectl get drconfig default -o jsonpath='{.status.lastBundle}'
```

## Object Lock

Object lock makes bundles and reports immutable for their retention period, so that neither an operator error nor
an attacker with the hub's credentials can delete them. Bundles are written with compliance-mode object lock for
`bundle.retainDays` days, reports with `reportRetainDays` days.

- **Bucket setting:** Object lock must be enabled when the bucket is created. It cannot be added to most existing
  buckets. Versioning is required for object lock.
- **Without object lock:** Disaster recovery works without object lock, but recovering the hub after a ransomware
  attack relies on bundles the attacker could not delete.
- **Compliance mode:** Objects under compliance-mode lock cannot be deleted before their retention expires, not even
  by the bucket owner. The retention periods should be chosen accordingly.

!!! note
    `dr-hub` does not check the bucket settings. A bucket without object lock accepts the bundles, but the retention
    is not enforced.

## Retention of Finished Runs

Finished recovery actions and tests stay on the hub as Kubernetes objects so that their status and reports remain
visible. `DRConfig.spec.retention` bounds how many are kept:

- **Keep per application:** The newest `keepPerApplication` runs (default 10) of each application or recovery plan
  are always kept, whatever their age.
- **Age:** Older runs are deleted after `days` days (default 90), but only after their report is in the archive.
- **Without archive:** Without an archive, finished runs are never pruned.

## Safekeeping the Restore Material

The hub writes to the archive with its own credential. A hub rebuild reads from the archive with a separate
credential. The following material must be kept offline, outside the hub and outside the sites:

- **Public key:** `bundle-signing.pub`, used by `dr-restore` to verify a bundle.
- **Read credential:** An S3 credential that can read the archive bucket. Ideally, the hub's own credential is
  write-only and cannot read or delete bundles.
- **Secrets:** The archive credential, the signing key, and the Ramen S3 credentials, which are not part of the
  bundle.

The private signing key `bundle-signing.key` is only needed again when the hub is rebuilt. It should be stored with
the same care as the other Secrets.

## Next Steps

- [Joining Site Clusters](sites.md)
- [Recovering the Hub](../operations/hub-recovery.md)
