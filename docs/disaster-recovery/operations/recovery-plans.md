---
title: "Recovery Plans"
description: "Fail over or relocate several applications in order with a RecoveryPlan: priorities, dependencies, gates, failure handling, and plan-level hooks."
weight: 10460
---

A `RecoveryPlan` groups applications that must move together along one DR path, for example, a database, the
services that use it, and a web front end. A recovery action that references the plan moves all of its applications
in a defined order, runs plan-level hooks once, and produces one combined report next to one report per application.

## RecoveryPlan Specification

| Field                                      | Description                                                                                                                                                                |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pathRef`                                  | The DR path every application of the plan must be on. Required.                                                                                                            |
| `applications[]`                           | 1 to 256 entries, each with `name` (a ProtectedApplication in the plan's namespace), `priority`, and `dependsOn`.                                                          |
| `applications[].priority`                  | Lower priorities run first, equal priorities run in parallel. Minimum and default: `1`.                                                                                    |
| `applications[].dependsOn`                 | Applications of the same plan that must have completed (be healthy on the target) before this one starts.                                                                  |
| `gates.betweenPriorities`                  | `allHealthy` (default): the next priority starts only when every lower priority has finished. `none`: priorities do not wait for each other, `dependsOn` is still honored. |
| `continueOnFailure`                        | When `false` (default), a failed application stops the plan from starting anything else. When `true`, only the applications that depend on it directly are skipped.        |
| `hooks.preSource`, `hooks.postTargetReady` | Plan-level external hooks, run once for the plan rather than per application.                                                                                              |

The plan's `status.readiness` combines a `plan-order` check with one `app/<name>` check per application, carrying
that application's verdict on the plan's path. A plan is only as ready as its least ready application.

## Example

```yaml title="RecoveryPlan"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryPlan
metadata:
  name: erp-stack
  namespace: ramen-ops
spec:
  pathRef: fra-a-to-fra-b
  applications:
    - name: erp-db
      priority: 1
    - name: erp
      priority: 2
      dependsOn: [erp-db]
    - name: portal
      priority: 2
  gates:
    betweenPriorities: allHealthy
  continueOnFailure: false
  hooks:
    postTargetReady:
      - name: announce
        job:
          image: registry.example/hooks:1
```

`erp-db` moves first. Once it is healthy on the target, `erp` and `portal` move in parallel. The `announce` hook runs
once, after all applications are up. Its image prefix must be in `DRConfig.spec.agent.hookImageAllowList`.

```bash title="Listing recovery plans"
kubectl -n ramen-ops get rplan
```

## Running a Plan

A plan is moved by a RecoveryAction with `planRef` instead of `applicationRef`:

```yaml title="Plan-level recovery action"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  name: erp-stack-relocate
  namespace: ramen-ops
spec:
  kind: Relocate
  pathRef: fra-a-to-fra-b
  planRef:
    name: erp-stack
```

For an unplanned failover, set `kind: Failover` and, if the plan is `NotReady`, an `override.reason`.

## How a Plan Action Runs

1. **PreFlight:** Checks the whole plan up front: the plan runs along the action's path, the path declares the kind,
   the order is valid, and every application exists, is bound, and runs at the path's `from` site. No other
   unfinished action may hold the plan or any of its applications. The plan's readiness follows the same override
   rules as an application's.
2. **PreSource:** Runs the plan's `hooks.preSource` once on the source site. On a Relocate, a failure fails the plan
   and nothing moves. On a Failover, the hooks are best effort (capped at 2 minutes).
3. **Workflow:** Starts one child RecoveryAction per application, in priority order.
4. **PostTargetReady:** Runs the plan's `hooks.postTargetReady` once on the target site.
5. **Confirming:** Completes the plan report.

## Child Actions

- **Naming:** Each child is named `<action>-<application>`, for example, `erp-stack-relocate-erp-db`. It carries the
  plan action's kind, path, override, and timeout, and is owned by the plan action.
- **Tracking:** `status.children` of the plan action lists each child with its application, priority, action name, phase, and final message. Each child
  has its own journal and report.
- **Failure:** Without `continueOnFailure`, every child not yet started is marked `Failed` with a message starting
  with `not started:`. Running children are never stopped, because Ramen cannot abort a move.
- **Result:** The plan action completes only if every child completed. Otherwise, it fails and names the applications
  that did not complete.

```bash title="Listing child actions"
kubectl -n ramen-ops get ract erp-stack-relocate -o jsonpath='{range .status.children[*]}{.application}{"\t"}{.phase}{"\n"}{end}'
```

The plan report holds the operator and override reason, the plan RTO (from plan creation until every child
completed), the largest achieved RPO among the children, the children's warnings prefixed with the application name,
and the plan hooks' results.

A recovery plan can also be tested as a whole with a [TestBubble](../testing/test-failover.md) that references it
with `planRef`.
