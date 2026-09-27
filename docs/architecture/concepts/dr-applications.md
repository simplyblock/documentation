---
title: "DR Applications"
description: "A protected application binds workloads and volumes to a protection plan as a discovered or managed application, with tiers, hooks, probes, and path readiness."
weight: 30910
---

A protected application is the unit that simplyblock Disaster Recovery (DR) replicates, fails over, relocates, and
tests. It binds a set of Kubernetes objects and their persistent volumes to a protection plan, names the site it runs
on and the one site it recovers to, and describes how it is started and checked on the target site. A protected
application is a namespaced `ProtectedApplication` resource on the DR hub.

## Source, Target, and Method

Every protected application references one protection plan, a source site, and exactly one target site of that plan.
A DR path from the source to the target has to exist. If the plan declares more than one replication method, the
application also names the method it uses. The plan and the target cannot be changed later. A different target
requires a new protected application and a full initial synchronization.

## Discovered and Managed Applications

Simplyblock DR distinguishes two kinds of applications by how they are deployed.

- **Discovered applications:** Deployed directly into namespaces on the source site, for example, with `kubectl` or
  a Helm chart. The application lists its protected namespaces and selects its persistent volume claims (PVCs) with
  a label selector. Velero captures the Kubernetes objects of these namespaces, and Ramen replicates the selected
  volumes. Discovered applications are declared in the `ramen-ops` namespace on the hub.
- **Managed applications:** Delivered to the sites through GitOps, for example, through an Argo CD ApplicationSet or an OCM
  Subscription that uses an OCM Placement. The application references the existing
  Placement, and the GitOps tooling redeploys the objects on the target site. Only the volumes are replicated.
  Managed applications are declared in the namespace of their Placement.

Existing Ramen DRPlacementControls can be adopted into a protected application instead of being recreated.

## Tiers and Boot Order

Applications often have to start in a defined order: configuration first, then databases or virtual machines, then
the services that depend on them. For discovered applications, tiers define this boot order. Each tier selects a
group of resources by type or by label, for example, `dr.simplyblock.io/tier: db`, and optionally lists readiness
conditions that must be met before the next tier starts.

| Readiness condition | Waits until                                                                                   |
|---------------------|-----------------------------------------------------------------------------------------------|
| `vmRunning`         | The selected KubeVirt virtual machines are running.                                           |
| `deploymentsReady`  | The selected Deployments are ready.                                                           |
| `statefulSetsReady` | The selected StatefulSets are ready.                                                          |
| `podsReady`         | The selected pods are ready.                                                                  |
| `exec`              | A command in a container succeeds, for example, a database readiness check.                   |
| `condition`         | An expression on a resource status is true, for example, a custom resource reporting `Ready`. |

The DR hub turns the tiers into a Ramen Recipe and delivers it to the sites. Without tiers, a default order of
configuration objects first and workloads second is used. As an alternative, a hand-written Ramen Recipe can be
referenced, which is used unchanged. Managed applications take their order from the GitOps tooling.

## Hooks

External hooks run steps outside of Kubernetes object restoration, such as draining traffic or switching DNS and
load balancer entries.

- **Pre-source hooks (`preSource`):** Run on the source site before anything moves, for example, to drain
  connections. On a relocation, a failing hook aborts the action. On a failover, the hooks run on a best-effort
  basis.
- **Post-target-ready hooks (`postTargetReady`):** Run on the target site once the application is healthy, for
  example, to announce the application under its public name.

Hooks run as Kubernetes Jobs from an allow-listed set of container images.

## Health Probes

Health probes decide when a recovered application counts as up. They check TCP or HTTP endpoints, whether virtual
machines are running, or whether their guest agents are connected. The recovery time (RTO) of an action is measured
from its start until all probes pass.

## Readiness per Path

For every DR path the application can move along, the DR hub continuously computes a readiness verdict.

| Verdict    | Meaning                                                                                            |
|------------|----------------------------------------------------------------------------------------------------|
| `Ready`    | All checks pass. Actions run.                                                                      |
| `Degraded` | Advisory checks fail, for example, no successful test within 30 days. Actions run with warnings.   |
| `NotReady` | A blocking check fails, for example, replication is behind. Actions are refused unless overridden. |
| `Unknown`  | The state cannot be determined.                                                                    |

Readiness covers, among others, whether the path is declared, whether the application is protected and currently at
the path's source, and whether an asynchronous replication is within 1.5 times its interval.

## Further Reading

- [Protected Applications](../../disaster-recovery/configuration/applications.md)
- [Workflows and Recipes](../../disaster-recovery/configuration/workflows-and-recipes.md)
- [DR Protection Plans](dr-protection-plans.md)
- [Failover](failover.md)
- [Relocation](relocation.md)
