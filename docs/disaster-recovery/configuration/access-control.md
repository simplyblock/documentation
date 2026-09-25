---
title: "Access Control"
description: "The dr-viewer, dr-operator, and dr-admin roles, the override verb for readiness overrides, creator stamping, and the admission webhook behavior."
weight: 10270
---

Access to disaster recovery is controlled with Kubernetes RBAC on the hub cluster. The hub chart creates three
ClusterRoles that separate reading, operating, and administering disaster recovery. The admission webhooks of
`dr-hub` add checks that RBAC alone cannot express, such as who may override a readiness verdict.

## Roles

| ClusterRole   | Read                                                          | Write                                                                        | Special                      |
|---------------|---------------------------------------------------------------|------------------------------------------------------------------------------|------------------------------|
| `dr-viewer`   | All DR objects, Ramen DRCluster, DRPolicy, DRPlacementControl | None                                                                         | None                         |
| `dr-operator` | As `dr-viewer`                                                | ProtectedApplication, RecoveryAction, RecoveryPlan, TestBubble, TestSchedule | None                         |
| `dr-admin`    | As `dr-viewer`                                                | As `dr-operator`, plus ProtectionPlan, DRPath, DRConfig, and RestoreAction   | `override` on RecoveryAction |

The division follows the responsibilities in a typical organization:

- **Viewers:** Application owners and auditors see the readiness, actions, and reports of all applications.
- **Operators:** Platform operators protect applications, run planned failovers, unplanned failovers, and tests. They
  cannot change sites, paths, or the DR configuration, and they cannot move an application that is `NotReady`.
- **Administrators:** DR administrators define the topology (plans and paths), change the DR configuration, restore
  applications from backups, and decide on overrides.

The chart binds none of the roles. They are bound to users or groups with ClusterRoleBindings, as shown in
[Installing the Hub](../install/hub.md#granting-access). `dr-operator` and `dr-admin` are aggregated ClusterRoles, so
their rules can be extended with additional ClusterRoles that carry the labels
`dr.simplyblock.io/aggregate-to-operator: "true"` or `dr.simplyblock.io/aggregate-to-admin: "true"`.

## Readiness Overrides

A recovery action is refused when the application's readiness for the path is `NotReady`, for example, because the
last asynchronous sync is too old, or because the source site is down during an unplanned failover. An administrator
can override the verdict by setting `spec.override.reason` on the RecoveryAction:

```yaml title="Unplanned failover with a readiness override"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  generateName: billing-
  namespace: ramen-ops
spec:
  kind: Failover
  pathRef: site-a-to-site-b
  applicationRef:
    name: billing
  override:
    reason: "Site A is down after a power outage, accepting the data loss since the last sync."
```

The webhook checks with a SubjectAccessReview whether the requester holds the `override` verb on `recoveryactions`.
Only `dr-admin` grants it. The reason must be 10 to 1024 characters long and is recorded in the action report.

Some checks cannot be overridden by anyone: an action along a path that does not declare it
(`PathActionNotDeclared`), and a test of an application that is not ready. See
[Unplanned Failover](../operations/unplanned-failover.md) for the procedure.

A custom role can grant the verb, for example, to an on-call group, without the other administrator rights:

```yaml title="ClusterRole granting only the override verb"
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dr-override
rules:
  - apiGroups:
      - dr.simplyblock.io
    resources:
      - recoveryactions
    verbs:
      - override
```

## Creator Stamping

The mutating webhook stamps the identity of the requester into the annotation `dr.simplyblock.io/created-by` of every
new RecoveryAction and TestBubble, replacing any value the request carried. The annotation cannot be changed or
removed afterward. Reports name this identity as the operator of the action or test.

Actions and tests that `dr-hub` creates itself, for example, the child actions of a recovery plan or the runs of a
test schedule, are stamped with the identity of the `dr-hub` service account.

## Admission Webhook Behavior

The validating webhooks enforce rules that involve other objects or the requester:

- **References:** An action or test must take a path that exists and belongs to the application's plan.
- **Immutability:** Finished recovery actions and test bubbles cannot be changed.
- **Deletion:** A DR path or protection plan that applications still use can only be deleted after
  `dr.simplyblock.io/confirm-delete: "true"` has been set on it.
- **Overrides:** A readiness override requires the `override` verb.

!!! warning
    All webhooks use `failurePolicy: Fail`. While `dr-hub` is unavailable, DR objects cannot be created or changed,
    including recovery actions. In an emergency where the hub is degraded, restoring `dr-hub` comes first. Running
    `dr-hub` with two replicas reduces the risk.
