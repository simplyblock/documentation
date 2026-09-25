---
title: "Test Failover"
description: "Run a test failover with a TestBubble: clone replicated volumes on the target site, restore in isolation, validate, report, and tear down."
weight: 10310
---

A `TestBubble` recovers one protected application, or every application of a recovery plan, along a DR path that
declares `Test`. It recovers onto the path's target site into renamed, isolated namespaces, then validates the
application, writes a report, and removes everything it created. A test never writes production objects, the
DRPlacementControls, or replication.

## Prerequisites

A test failover requires the following:

- **Path declares Test:** The DR path lists `Test` in `spec.actions` and carries a `spec.test` block. See
  [DR Paths](../configuration/paths.md).
- **Discovered applications:** Only discovered applications can be tested. Managed (GitOps) applications report
  `Unsupported`.
- **Readiness:** Each application runs at the path's `from` site and is not `NotReady` or `Unknown`. Tests cannot be
  overridden.
- **No concurrent run:** No unfinished recovery action and no earlier unfinished test holds the application.
- **Isolated network for Multus VMs:** KubeVirt VMs attached to Multus networks need an isolated
  NetworkAttachmentDefinition, named on the path as `test.isolatedNad: <namespace>/<name>`. It must have no uplink to
  production networks.
- **Replicated snapshots:** The storage on the target site publishes its replicated consistency points as
  VolumeSnapshotContents (label `dr.simplyblock.io/replicated-snapshot=true`).

A path with a test block looks as follows.

```yaml title="DR path with a test block"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: fra-a-to-fra-b
spec:
  from: fra-a
  to: fra-b
  planRef: fra
  actions: [Failover, Relocate, Test]
  test:
    mode: bubble
    isolatedNad: openshift-adp/drtest
    quotas:
      maxCloneCapacity: 2Ti
    recentWithin: 720h
```

The only test mode is `bubble` (the default). `quotas.maxCloneCapacity` limits the total capacity of the clones a
test may create.

## TestBubble Specification

| Field                 | Description                                                                                       |
|-----------------------|---------------------------------------------------------------------------------------------------|
| `pathRef`             | Name of the DR path to test along. Required.                                                      |
| `applicationRef.name` | The protected application to test. Exactly one of `applicationRef` and `planRef` is set.          |
| `planRef.name`        | A recovery plan whose applications are tested together, in priority order.                        |
| `cloneSource`         | `latest-replicated-snapshot` (default) or `secondary-snapshot`.                                   |
| `holdFor`             | Keeps the restored application running for this duration after validation, for manual inspection. |
| `maxLifetime`         | Upper bound for the whole test (default `24h`). When reached, the test is torn down.              |
| `abort`               | Set to `true` to stop the test and tear it down.                                                  |

The specification is immutable after creation, except `abort` and `holdFor`.

## Running a Test

A test of a single application:

```yaml title="TestBubble for one application"
apiVersion: dr.simplyblock.io/v1alpha1
kind: TestBubble
metadata:
  generateName: orders-test-
  namespace: ramen-ops
spec:
  pathRef: site-a-to-site-b
  applicationRef:
    name: orders
```

A test of a recovery plan restores its applications in priority order into one shared bubble, so the applications
reach each other as they do in production:

```yaml title="TestBubble for a recovery plan"
apiVersion: dr.simplyblock.io/v1alpha1
kind: TestBubble
metadata:
  generateName: erp-stack-test-
  namespace: ramen-ops
spec:
  pathRef: fra-a-to-fra-b
  planRef:
    name: erp-stack
  holdFor: 1h
```

Create the object and follow it with the short name `tbub`:

```bash title="Starting and watching a test"
kubectl create -f testbubble.yaml
kubectl -n ramen-ops get tbub -w
```

## Phases

| Phase          | What happens                                                                                                                                     |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `Pending`      | Pre-flight checks, invariants recorded, and the source inventory read (Ramen state, protected PVCs, the Kubernetes object capture, and the VMs). |
| `Cloning`      | Bubble namespaces are created and one clone PVC is created for every protected PVC, from the latest replicated consistency point.                |
| `Provisioning` | Network isolation is set up in the bubble.                                                                                                       |
| `Restoring`    | The application's Recipe restore workflow runs against Ramen's capture, tier by tier.                                                            |
| `Validating`   | The validation checks run.                                                                                                                       |
| `Holding`      | Only with `holdFor`. Ends early on `abort`.                                                                                                      |
| `TearingDown`  | Everything labeled with the test ID is deleted on the target, then invariants are compared.                                                      |
| `Completed`    | The bubble is verifiably gone, whatever the outcome.                                                                                             |
| `Failed`       | Teardown could not verify that everything was removed.                                                                                           |

A test resumes where it stopped after a restart of dr-hub. The outcome of the test is in `status.report.outcome`, not
in the phase.

## Bubble Isolation

The bubble keeps the test copy away from production:

- **Namespaces:** Each protected namespace `<ns>` is restored as `<ns>-drtest-<id>`. The bubble namespaces are listed
  in `status.bubbleNamespaces`.
- **NetworkPolicy:** Every bubble namespace gets the `drtest-isolation` NetworkPolicy. It denies all traffic except
  traffic within the bubble, DNS, and ingress from dr-agent for health probes.
- **Network attachments:** For each NAD a VM names, a NAD of the same name is created in the bubble namespace with
  the configuration of the path's `test.isolatedNad`.
- **Services:** LoadBalancer and NodePort Services are turned into ClusterIP Services and lose their external IPs.
- **Excluded objects:** Routes, Ingresses, Gateways, HTTPRoutes, NetworkPolicies, and NADs from production are not
  restored.
- **Read-only capture:** Objects are restored from Ramen's Velero capture through a BackupStorageLocation with
  `accessMode: ReadOnly`, so a test can never overwrite production's capture.
- **Health probes:** Probe targets such as `<svc>.<ns>` are mapped to `<svc>.<ns>-drtest-<id>`. Targets the bubble
  cannot answer for (external names, IP addresses) are skipped as not exercised.

## Validation Checks

| Check                   | Meaning                                                                                |
|-------------------------|----------------------------------------------------------------------------------------|
| `pods-ready`            | All pods in the bubble are ready.                                                      |
| `vms-running`           | All VirtualMachines in the bubble are running.                                         |
| `guest-agent-connected` | The guest agent of each VM is connected. Warns only, because many guests run no agent. |
| `probes-healthy`        | The application's `health.probes`, mapped into the bubble, pass.                       |

The results are listed in `status.checks`.

## Holding and Aborting

With `holdFor`, the test stays in `Holding` after validation so that the restored application can be inspected. To
end a test early, set `abort`:

```bash title="Aborting a test"
kubectl -n ramen-ops patch tbub orders-test-x7k2p --type merge -p '{"spec":{"abort":true}}'
```

Once anything has reached the target, any failure, an abort, or reaching `maxLifetime` moves the test to
`TearingDown`.

## Report and Outcomes

`status.report` holds the result:

| Outcome           | Meaning                                                                                            |
|-------------------|----------------------------------------------------------------------------------------------------|
| `Passed`          | The application came up in the bubble and all checks passed.                                       |
| `Failed`          | A step failed. The report names the first failure and the step.                                    |
| `FailedInvariant` | Production, replication, or a Ramen object changed during the test. Overrides every other outcome. |
| `Unsupported`     | The application cannot be tested safely in this release (see below).                               |

The report also records the test point (the consistency point restored), the achieved RPO at test time, the
estimated RTO (from all clones ready until the last restore workflow completed), the consistency (`group` or
`per-volume`), the coverage (what was exercised and what was not), and warnings. When an archive is configured,
the report is stored as JSON and PDF in S3, and the key is recorded in `status.reportKey`.

## Unsupported Cases

Nothing is rewritten in this release, so the test reports `Unsupported` rather than risk a false pass or a connection
to production for:

- **Managed applications:** GitOps-delivered applications.
- **NAD in another namespace:** A VM that uses a NetworkAttachmentDefinition from another namespace.
- **Multus without isolation:** A VM on Multus networks while the path names no `test.isolatedNad`.
- **Host-bound devices:** VMs with SR-IOV interfaces, host devices, or GPUs.

## Clone Sources

- **`latest-replicated-snapshot`:** The default. Clones come from the newest replicated consistency point on the
  target. For a consistency group, all members come from the newest point every member has. The replica's snapshot
  is never modified or deleted.
- **`secondary-snapshot`:** Snapshots of the secondary volumes. Behind the `secondarySnapshot` feature gate and not
  functional yet.

## Teardown

Teardown deletes every object labeled `dr.simplyblock.io/test-id=<id>` on the target site, and bubble namespaces only
if they carry the label, then waits until nothing remains. It then compares the invariants. Finished tests are
retained and pruned together with reports, as described in [Monitoring](../operations/monitoring.md#reports).

!!! info "Coming soon"
    - **Hosted-cluster test mode:** Tests inside a hosted cluster with mirrored test networks, MAC address
      regeneration, guest IP regeneration, and Route host rewriting (with the site mapper).
    - **Managed applications:** Test restores of GitOps-delivered applications.
