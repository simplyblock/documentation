---
title: "Hub Recovery"
description: "Recover a lost simplyblock DR hub cluster from its signed state bundle with dr-restore, re-join the sites, and fail over when the primary site is lost too."
weight: 10480
---

The hub cluster holds the DR configuration and drives all actions, but it does not hold application data. When the
hub is lost, the applications keep running and replicating on the sites, but no recovery action can be started until
a hub is back. dr-hub therefore writes a signed DR state bundle to the archive bucket, and the `dr-restore` tool
rebuilds a hub from it.

## State Bundle

dr-hub writes a new bundle whenever the DR state changes, at most every `DRConfig.spec.archive.bundle.interval`
(default `5m`). A bundle is a tar file `<prefix>bundle/<generation>.tar` with a detached ed25519 signature
`<generation>.sig`. With `bundle.retainDays` set (default 30), both are written under a compliance-mode object lock.
The latest bundle is shown in `DRConfig.status.lastBundle`.

A bundle contains the following, in restore order:

- **Configuration:** The DRConfig.
- **OCM intent:** Managed cluster sets, managed clusters, cluster set bindings, and the dr-agent addons.
- **Ramen hub configuration:** The Ramen hub ConfigMap with its S3 profiles.
- **Simplyblock DR resources:** ProtectionPlans, DRPaths, ProtectedApplications, RecoveryPlans, and TestSchedules.
- **Ramen resources:** DRClusters, DRPolicies, the Placements and PlacementDecisions of the DRPlacementControls, and
  the DRPlacementControls.
- **Generated Recipes:** For audit only. dr-hub redelivers them after a restore.

A bundle contains no Secrets and no finished runs (these are archived as reports). The following Secrets must be kept
in safekeeping outside the clusters:

- **Archive credential:** The S3 credential dr-hub uses to write the archive.
- **Signing key:** The ed25519 private key that signs the bundles.
- **Ramen S3 secrets:** The credentials of the site S3 stores.
- **Offline restore material:** The public key `bundle-signing.pub` and a read-only S3 credential for the archive.

The signing key pair is created with `dr-restore keygen -out ./keys` during installation. See
[Report and Bundle Archive](../install/archive.md).

## Restoring a Hub

1. **Install a new hub:** Install the hub chart on a new cluster as described in [Install the Hub](../install/hub.md),
   with the same archive configuration.
2. **Restore the Secrets:** Recreate the archive credential and the signing key Secrets in the `dr-simplyblock`
   namespace, and the Ramen S3 secrets in the Ramen namespace, from safekeeping.
3. **Verify the bundle:** List the available generations and verify the one to restore:

    ```bash title="Listing and verifying bundles"
    export AWS_ACCESS_KEY_ID=<read-only key>
    export AWS_SECRET_ACCESS_KEY=<read-only secret>
    dr-restore list -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/
    dr-restore verify -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/ \
      -public-key keys/bundle-signing.pub
    ```

4. **Restore:** Apply the bundle to the new hub. A dry run lists what would be restored without writing anything:

    ```bash title="Restoring the hub"
    dr-restore restore -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/ \
      -public-key keys/bundle-signing.pub -kubeconfig hub.kubeconfig -dry-run
    dr-restore restore -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/ \
      -public-key keys/bundle-signing.pub -kubeconfig hub.kubeconfig
    ```

5. **Re-join the sites:** Join every site cluster again under its old name, with a new bootstrap token from the new
   hub. See [Join Sites](../install/sites.md).
6. **Check readiness:** Ramen adopts the restored DRPlacementControls from the state on the sites instead of
   deploying the applications anew. dr-hub recomputes readiness. Check `kubectl get papp -A` and the readiness of
   each path.

A restore can be rerun after a partial failure: objects that already exist are left alone.

### dr-restore Flags

| Flag                                                         | Meaning                                                                                                                                                    |
|--------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s3-endpoint`, `-bucket`, `-region`, `-prefix`, `-insecure` | The archive location. `-prefix` defaults to `dr/`, `-insecure` uses plain HTTP. Credentials are read from `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. |
| `-dir`                                                       | Reads from a local copy of the archive instead of S3.                                                                                                      |
| `-public-key`                                                | The PEM public key the bundle must verify with. Required. A bundle that does not verify is never applied.                                                  |
| `-generation`                                                | The bundle generation to restore. The newest when empty.                                                                                                   |
| `-kubeconfig`                                                | The kubeconfig of the new hub.                                                                                                                             |
| `-dry-run`                                                   | Lists what would be restored and writes nothing.                                                                                                           |
| `-hold`                                                      | Leaves dr-hub in recovery mode at the end.                                                                                                                 |
| `-fresh-sites`                                               | The sites were rebuilt too. See [Backup and Restore](backup-restore.md#restoring-after-a-total-loss).                                                      |

## Recovery Mode

`dr-restore` first applies the DRConfig with `recoveryMode: true`. In recovery mode, dr-hub neither derives nor binds
objects, and it writes no bundles, so the restored objects cannot trigger changes before Ramen's objects are back. At the end of
the restore, recovery mode is lifted.

With `-hold`, recovery mode stays on, for example, to inspect the restored state before dr-hub resumes. To resume,
set it to `false`:

```bash title="Leaving recovery mode"
kubectl patch drconfig default --type merge -p '{"spec":{"recoveryMode":false}}'
```

The `Recovery` column of `kubectl get drconfig` shows the current mode.

## Hub and Primary Site Lost

When the hub and the primary site are lost together, the hub is restored first, as above, with the surviving sites
re-joined. Then each affected application is recovered on the surviving site with an
[unplanned failover](unplanned-failover.md), usually with an override, because the lost site makes readiness
`NotReady`.

!!! info "Coming soon"
    - **RestoreHub action:** A `RecoveryAction` of kind `RestoreHub` on a running hub. Today, the `dr-restore` tool
      covers the recovery.
    - **Secret sealing:** Sealing the archive credential, signing key, and S3 secrets to a customer-held key, so that
      they can be restored together with the bundle.
