---
title: Upgrade a Helm Install from R26.3 to R26.4
description: "Manual procedure to upgrade a Kubernetes control plane installed with the R26.3 Helm chart to the R26.4 Simplyblock Operator, including the conversion webhook and CRD steps a plain helm upgrade skips."
weight: 20100
---

This page upgrades a Kubernetes installation made with the R26.3 Helm chart (tested on `v26.3.2-1`) to the R26.4
chart, which serves the `storage.simplyblock.io/v1alpha2` API. It covers the control plane, the operator, and the CSI
driver. It does not cover storage nodes, volumes, or the migration of storage resources.

!!! warning
    This is a manual procedure. The `simplyblock-upgrade` tool that is meant to run it does not yet implement the
    conversion webhook and operator steps, and a plain `helm upgrade` fails on this upgrade. Read
    [Known Limitations](#known-limitations) before starting, and do not run the procedure against a cluster with
    attached volumes until those are resolved for your installation.

## Why a Plain `helm upgrade` Fails

Three things stop it, in this order:

1. The chart refuses the upgrade while the old control plane is not marked to be kept. Helm would otherwise delete the
   FoundationDB database that holds every cluster definition, node registration, and volume record.
2. The R26.4 chart renders `v1alpha2` resources, and Helm applies a chart's CRDs only on install. The CRDs have to be
   applied first.
3. The applied CRDs convert between API versions through a webhook that nothing serves yet. Helm then cannot read the
   existing `ControlPlane`, and the upgrade stops before it reaches the new operator. The conversion webhook has to run
   before the CRDs are applied.

## Before You Start

Take the commands from a checkout of the operator repository at the target tag. The conversion webhook manifests are not
part of the chart.

```bash title="Check out the target release"
git clone --branch <TARGET_TAG> https://github.com/simplyblock/simplyblock-operator
cd simplyblock-operator
export NS=simplyblock
export OPERATOR_IMAGE=<TARGET_OPERATOR_IMAGE>
```

The conversion webhook runs from the operator image, so the image has to contain `/usr/local/bin/conversion-webhook`.

Record the values the release is installed with:

```bash title="Record the current values"
helm get values simplyblock-operator -n "$NS" --all > values-r26-3.yaml
```

The R26.4 chart changes two defaults, `tls.enabled` and `tls.mutual_enabled`, both to `true`. Pass the values your
installation actually has in Step 5. The values schema also rejects keys that the R26.4 chart no longer has. See
[Values That Moved](#values-that-moved).

## Step 1: Record the TLS and Keep the Control Plane

A `v1alpha1` `ControlPlane` has no TLS field, and the `v1alpha2` field `spec.source.local.tls` cannot change once the
control plane exists. Record what the installation uses on the existing object, before the CRDs are applied. Conversion
reads the record, and an object without one converts to plaintext, which is what the R26.3 chart installs by default.

```bash title="Record the installation's TLS"
# TLS off (the R26.3 default):
kubectl -n "$NS" annotate controlplane.v1alpha1.storage.simplyblock.io simplyblock \
  storage.simplyblock.io/v1alpha1-tls='{"enableTLS":false,"enableMutualTLS":false,"provider":"cert-manager"}'
# TLS and mutual TLS on with cert-manager (tls.enabled and tls.mutual_enabled set to true):
kubectl -n "$NS" annotate controlplane.v1alpha1.storage.simplyblock.io simplyblock \
  storage.simplyblock.io/v1alpha1-tls='{"enableTLS":true,"enableMutualTLS":true,"provider":"cert-manager"}'
```

Use the values from `values-r26-3.yaml`: `tls.enabled`, `tls.mutual_enabled`, and the provider, which is `OpenShift`
where `tls.provider` is `openshift`. Then pass the same `tls.enabled` and `tls.mutual_enabled` in Step 5. If they differ
from the record, the API server rejects the upgrade, and nothing is changed.

Without the policy below, Helm deletes these objects on upgrade, FoundationDB included:

Without the policy, Helm deletes these objects on upgrade, FoundationDB included:

```bash title="Annotate what the new chart no longer owns"
for k in deployment/simplyblock-webappapi deployment/simplyblock-tasks \
  deployment/simplyblock-monitoring deployment/simplyblock-admin-control \
  deployment/simplyblock-fdb-controller-manager deployment/simplyblock-fdb-exporter \
  statefulset/simplyblock-minio foundationdbcluster/simplyblock-fdb-cluster; do
  kubectl -n "$NS" annotate "$k" helm.sh/resource-policy=keep --overwrite
done
```

## Step 2: Start the Conversion Webhook

```bash title="Deploy the conversion webhook"
kubectl kustomize operator/config/conversion-webhook \
  | sed -e "s/simplyblock-operator-system/$NS/g" \
        -e "s#quay.io/simplyblock-io/simplyblock-operator:0.1.0#$OPERATOR_IMAGE#" \
  | kubectl apply -f -
kubectl -n "$NS" rollout status deploy/simplyblock-operator-conversion-webhook
```

On a cluster whose DNS domain is not `cluster.local`, add `--cluster-dns-domain=<domain>` to the container arguments
first.

## Step 3: Apply the CRDs

```bash title="Apply the CRDs of the target release"
kubectl apply --server-side --force-conflicts -f helm-charts/charts/simplyblock-operator/crds/
```

`--force-conflicts` is required because Helm owns `.spec.versions` of the CRDs it installed.

The CRDs name a service in the namespace `simplyblock-operator-system` and carry no CA bundle. The conversion webhook
corrects the namespace on a 30-second timer. Wait until the reference points at your namespace, then check that the
existing `ControlPlane` can be read:

```bash title="Check that conversion works"
kubectl get crd controlplanes.storage.simplyblock.io \
  -o jsonpath='{.spec.conversion.webhook.clientConfig.service.namespace}{"\n"}'
kubectl -n "$NS" get controlplanes.v1alpha2.storage.simplyblock.io
```

If the second command fails with `x509: certificate signed by unknown authority`, the CRDs lack the webhook's CA. Images
built before the fix in operator PR #784 do not restore it. Copy it from the webhook's own secret into each of the seven
converted CRDs (`controlplanes`, `storagebackups`, `storageclusterops`, `storageclusters`, `storagenodeops`,
`storagenodes`, `storagepools`):

```bash title="Copy the CA into a converted CRD"
CA=$(kubectl -n "$NS" get secret conversion-webhook-server-cert -o jsonpath='{.data.ca\.crt}')
kubectl patch crd controlplanes.storage.simplyblock.io --type merge \
  -p "{\"spec\":{\"conversion\":{\"webhook\":{\"clientConfig\":{\"caBundle\":\"$CA\"}}}}}"
```

## Step 4: Check for Removed Values

Compare `values-r26-3.yaml` with the R26.4 `values.yaml` and remove or move every key the new chart rejects. See
[Values That Moved](#values-that-moved).

## Step 5: Upgrade the Release

```bash title="Upgrade the chart"
helm upgrade simplyblock-operator helm-charts/charts/simplyblock-operator -n "$NS" \
  --set deployment.profile=standalone \
  --set tls.enabled=<value from the current release> \
  --set tls.mutual_enabled=<value from the current release> \
  --set image.operator.repository=<repository> --set image.operator.tag=<tag>
```

## Step 6: Check the Result

- `helm history simplyblock-operator -n "$NS"` shows the new revision as `deployed`.
- The `ControlPlane` has the same UID and creation time as before the upgrade, and its phase is `Available`.
- The `FoundationDBCluster` has its old creation time, and its pods and volume claims are the old ones.
- The chart no longer installs the CSI driver. The operator creates it from the `SimplyblockDriver`, and the driver
  reaches `Ready` with all nodes. The CSI pods are replaced.
- No pod is crash-looping. The `tasks` pod restarts once while the control-plane image changes.

```bash title="Check the control plane and the driver"
kubectl -n "$NS" get controlplanes.v1alpha2.storage.simplyblock.io,simplyblockdriver
kubectl -n "$NS" get pods
```

On a three-worker K3s cluster with TLS and mutual TLS, this procedure produced revision 2 as `deployed` after 21
seconds, a `ControlPlane` and FoundationDB cluster that were untouched, and a `SimplyblockDriver` that reached `Ready`
with all four nodes. No storage cluster, storage node, or volume existed on that cluster.

## Values That Moved

Keys that the R26.3 chart had and the R26.4 chart rejects or moves include:

- `driverName`, `image.csi*`, `controller.*`, `node.*`, and `snapshotclass.create` move to the `SimplyblockDriver`
  resource.
- `storagenode.*` moves to the cluster and storage node resources. Only `storagenode.multiCluster` stays, as the
  top-level `multiCluster`.
- `controlplane.foundationdb.*`, `controlplane.observability.minio.*`, `csiHostpathDriver`, and `operator.enabled` are
  removed or moved under `controlplane`.

Compare the two `values.yaml` files for the full list.

## Known Limitations

- **The upgrade tool is incomplete.** `simplyblock-upgrade upgrade` plans the conversion webhook and operator steps but
  does not implement them. Steps 2, 3, and 5 above are what it will do.
- **The handover covers eight objects.** Services, ConfigMaps, and the two Certificates `simplyblock-foundationdb` and
  `simplyblock-webappapi` are not marked to be kept. Helm may delete them, and reissuing a Certificate may rotate the
  FoundationDB peer certificates. This was not tested.
- **The TLS record is a manual step.** Without the annotation from Step 1, an object converts to plaintext. A TLS
  installation that skips it is rejected at Step 5, because the chart states TLS and the field is immutable, which
  leaves the cluster unchanged. Check `spec.source.local.tls` on the converted `ControlPlane` before Step 5.
- **A discovery run starts on upgrade.** The chart renders `OperatorOps/initial-discovery` on every upgrade of a
  standalone installation, so an upgraded cluster gets a discovery run and a draft `ClusterDeploymentConfig`. Do not
  approve the draft on a cluster that is already deployed.
- **Attached volumes were not tested.** What replacing the CSI node plugins does to a mounted volume is unverified.
- **Storage resources are not migrated.** The `migrate` stage, the rewrite of stored objects to `v1alpha2`, and the
  removal of `v1alpha1` were not run.
- **Rollback is not covered.** `helm rollback` restores the old operator Deployment but not the CRDs.
