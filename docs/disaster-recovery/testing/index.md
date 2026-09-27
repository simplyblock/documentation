---
title: "Test"
description: "Why and how to rehearse a disaster recovery failover with simplyblock DR test bubbles, what a test proves, and how recent tests affect readiness."
weight: 10300
---

A disaster recovery setup that has never been tested is an assumption. simplyblock DR rehearses a failover without
touching production: it clones the replicated volumes on the target site, restores the application into renamed and
isolated namespaces, validates that it comes up, reports the result, and tears everything down again. Production,
replication, and the Ramen objects stay unchanged, and the test proves this by comparing digests recorded before and
after.

## Why Test

A test answers questions that configuration alone cannot:

- **Recoverability:** Whether the replicated data and the captured Kubernetes objects are enough to start the
  application on the target site.
- **Boot order:** Whether the tiers and readiness gates bring the application up in the right order.
- **Recovery point:** How old the data on the target is at the time of the test (the achieved RPO).
- **Recovery time:** How long the restore takes (the estimated RTO).

## What a Test Proves and What It Never Exercises

A test failover exercises the restore of the application from the latest replicated consistency point and its
startup on the target site. It never exercises the following, and every test report states so:

- **Promotion:** Ramen's promotion of the replicated volumes on the target.
- **Fencing:** NetworkFence of the source site.
- **External cutover:** The `preSource` and `postTargetReady` external hooks, for example, DNS or load balancer
  changes.
- **Network identity:** Routes, Ingresses, LoadBalancer addresses, and production network attachments.

A planned relocation (see [Planned Failover](../operations/planned-failover.md)) is the only way to exercise the
complete move.

## Readiness and Recent Tests

The readiness check `test-recent` runs on every DR path that declares the `Test` action. It warns, and the
application's readiness on that path becomes `Degraded`, when no test along the path has passed, or when the last
passed test is older than the path's `test.recentWithin` (default `720h`, i.e., 30 days). A test of a recovery plan
counts for each of its applications. On paths without `Test`, the check is not applicable.

Recurring tests with a [test schedule](test-schedules.md) keep this check green.

## Section Contents

- [Test Failover](test-failover.md)
- [Test Schedules](test-schedules.md)
