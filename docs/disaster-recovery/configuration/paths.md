---
title: "DR Paths"
description: "Declare the directions between the sites of a protection plan with DRPath resources, the actions allowed along each direction, and the test environment."
weight: 10230
---

A DRPath declares one direction between two sites of a protection plan, from a source site to a target site, and the
actions permitted along it. Directions are declared, never inferred: an application can only fail over, relocate, or
be tested along a path that exists and allows the action. DR paths are cluster-scoped and written by the `dr-admin`
role.

A DRPolicy is derived for every pair of sites that is connected by at least one path, so paths also decide which
site pairs replicate at all (see [Protection Plans](protection-plans.md#what-dr-hub-derives)).

## Specification

| Field                               | Required | Description                                                                                                                            |
|-------------------------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------|
| `spec.from`                         | Yes      | Source site name in the plan. Immutable.                                                                                               |
| `spec.to`                           | Yes      | Target site name in the plan. Must differ from `from`. Immutable.                                                                      |
| `spec.planRef`                      | Yes      | Name of the ProtectionPlan both sites belong to. Immutable.                                                                            |
| `spec.actions[]`                    | Yes      | At least one of `Failover`, `Relocate`, and `Test`.                                                                                    |
| `spec.announcementHandover`         | No       | Allows keeping VIPs along the path. Stored, but without effect until site mapping is available.                                        |
| `spec.test.mode`                    | No       | Test environment. Only `bubble` (default) is supported.                                                                                |
| `spec.test.isolatedNad`             | No       | `<namespace>/<name>` of a NetworkAttachmentDefinition on the target without uplink, used for VMs with secondary networks during tests. |
| `spec.test.quotas.maxCloneCapacity` | No       | Maximum total size of the clone PVCs one test may create, for example, `2Ti`.                                                          |
| `spec.test.recentWithin`            | No       | Maximum age of the last passed test before readiness warns (default `720h`).                                                           |

A path that lists `Test` must have a `test` block. Changing `from`, `to`, or `planRef` requires a new DRPath.

## Actions as a Permission Set

The `actions` list is a permission set for the direction:

- **Failover:** An unplanned move to the target without a final sync, for when the source site is lost. See
  [Unplanned Failover](../operations/unplanned-failover.md).
- **Relocate:** A planned move with a final sync and no data loss. See
  [Planned Failover](../operations/planned-failover.md).
- **Test:** A test failover into an isolated environment on the target, without touching the running application.
  See [Test Failover](../testing/test-failover.md).

An action that the path does not declare is refused with `PathActionNotDeclared`. This check cannot be overridden,
not even by an administrator.

## Failback

There is no separate failback action. A failback is a Relocate along the reverse path. For an application that fails
over from `site-a` to `site-b`, the path `site-b-to-site-a` must allow `Relocate` to bring it back:

- **After a relocation:** The reverse path can be used as soon as the relocation is complete.
- **After a failover:** The reverse path reports the application as not ready until the old source site is back and
  replication from the new source has resumed (Ramen `PeerReady`).

See [Relocation](../../architecture/concepts/relocation.md) for the concept.

## Status

```bash title="Listing the DR paths"
kubectl get drpaths
```

```plain title="Example output of the DR path listing"
NAME               FROM     TO       PLAN      ACTIONS                         VALID
site-a-to-site-b   site-a   site-b   aws-fra   ["Failover","Relocate","Test"]   True
site-b-to-site-a   site-b   site-a   aws-fra   ["Relocate"]                    True
```

The path status lists the derived DRPolicies of its site pair, the protected applications on the path, and the most
recent action of each kind. The `Valid` condition reports whether the plan and both sites exist.
`status.profileConsistency` reports `NotAvailable` until site profiles are available.

A path that applications still use can only be deleted after the annotation
`dr.simplyblock.io/confirm-delete: "true"` has been set on it.

## Examples

### Two Sites, Both Directions

The primary direction allows every action. The reverse direction only allows a Relocate, so that the application can
be brought back as a planned move, but a failover back to the original site is not possible.

```yaml title="DR paths between two sites (paths-aws-fra.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: site-a-to-site-b
spec:
  from: site-a
  to: site-b
  planRef: aws-fra
  actions:
    - Failover
    - Relocate
    - Test
  test:
    mode: bubble
---
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: site-b-to-site-a
spec:
  from: site-b
  to: site-a
  planRef: aws-fra
  actions:
    - Relocate
```

### Tests of Virtual Machines With Secondary Networks

A VM with a Multus secondary network can only be tested if the target has an isolated NetworkAttachmentDefinition
without uplink. During the test, a NAD with the original name is created in the test namespace and points to it:

```yaml title="DR path with an isolated test network and clone quota (path-fra-a-to-fra-b.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: fra-a-to-fra-b
spec:
  from: fra-a
  to: fra-b
  planRef: fra
  actions:
    - Failover
    - Relocate
    - Test
  test:
    isolatedNad: openshift-adp/drtest
    quotas:
      maxCloneCapacity: 2Ti
    recentWithin: 720h
```

### Three Sites With a One-Way Fallback

With three sites, `fra-a` and `fra-b` form the primary pair in both directions, and `muc-c` is a fallback site that only
receives failovers from `fra-a`. There is no path back from `muc-c`. Bringing an application back from `muc-c`
requires an additional path from `muc-c` that allows `Relocate`.

```yaml title="DR paths of a three-site plan (paths-eu.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: fra-a-to-fra-b
spec:
  from: fra-a
  to: fra-b
  planRef: eu
  actions:
    - Failover
    - Relocate
---
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: fra-b-to-fra-a
spec:
  from: fra-b
  to: fra-a
  planRef: eu
  actions:
    - Relocate
---
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRPath
metadata:
  name: fra-a-to-muc-c
spec:
  from: fra-a
  to: muc-c
  planRef: eu
  actions:
    - Failover
```

The site pairs `fra-a`/`fra-b` and `fra-a`/`muc-c` each get one DRPolicy per method. The pair `fra-b`/`muc-c` has no
path and therefore no DRPolicy.

!!! note
    Each protected application has exactly one target site. An application protected from `fra-a` to `fra-b` uses the
    first path, and an application protected from `fra-a` to `muc-c` uses the fallback path. Several targets per
    application are not supported.
