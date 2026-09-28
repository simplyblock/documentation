---
title: "Access Control"
description: "The dr-viewer, dr-operator, and dr-admin roles, the override verb for readiness overrides, creator stamping, and the admission checks."
weight: 10270
---

Access to disaster recovery is controlled with Kubernetes RBAC on the hub cluster. The hub chart creates three
ClusterRoles that separate reading, operating, and administering disaster recovery. Admission checks add rules that
RBAC alone cannot express, such as who may override a readiness verdict.

## Roles

| ClusterRole   | Read           | Write                                                                        | Special                      |
|---------------|----------------|------------------------------------------------------------------------------|------------------------------|
| `dr-viewer`   | All DR objects | None                                                                         | None                         |
| `dr-operator` | As `dr-viewer` | ProtectedApplication, RecoveryAction, RecoveryPlan, TestBubble, TestSchedule | None                         |
| `dr-admin`    | As `dr-viewer` | As `dr-operator`, plus ProtectionPlan, DRPath, DRConfig, and RestoreAction   | `override` on RecoveryAction |

The division follows the responsibilities in a typical organization:

- **Viewers:** Application owners and auditors see the readiness, actions, and reports of all applications.
- **Operators:** Platform operators protect applications, run planned failovers, unplanned failovers, and tests. They
  cannot change sites, paths, or the DR configuration, and they cannot move an application that is `NotReady`.
- **Administrators:** DR administrators define the topology (plans and paths), change the DR configuration, restore
  applications from backups, and decide on overrides.

The chart binds none of the roles. They are bound to users or groups with ClusterRoleBindings for access to all
namespaces, as shown in [Installing the Hub](../install/hub.md#granting-access), or with RoleBindings for access to
single namespaces (see [Scoping Access](#scoping-access)). `dr-operator` and `dr-admin` are aggregated ClusterRoles, so
their rules can be extended with additional ClusterRoles that carry the labels
`dr.simplyblock.io/aggregate-to-operator: "true"` or `dr.simplyblock.io/aggregate-to-admin: "true"`.

## Scoping Access

The DR roles are ClusterRoles, but they do not have to be granted cluster-wide. How far a binding reaches depends on
the kind of binding and on where the DR resources live.

### Where DR Resources Live

| Resource                                                                  | Scope      | Namespace                                                                            |
|---------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------|
| ProtectionPlan, DRPath, DRConfig                                          | Cluster    | None                                                                                 |
| ProtectedApplication of a managed (GitOps) application                    | Namespaced | The application's own namespace, next to its Placement                               |
| ProtectedApplication of a discovered application                          | Namespaced | The Ramen ops namespace (`ramen-ops` by default, `DRConfig.spec.ramen.opsNamespace`) |
| RecoveryAction, RecoveryPlan, TestBubble, TestSchedule, and RestoreAction | Namespaced | The namespace of the applications they act on                                        |

A RecoveryAction, TestBubble, or RestoreAction references its application by name, and only within its own namespace.
A RecoveryPlan groups applications of one namespace. The namespace is therefore the boundary of every DR action.

### Cluster-Wide and Per-Namespace Bindings

- **ClusterRoleBinding:** Grants the role for all namespaces and for the cluster-scoped resources. This is required
  for `dr-admin`, since protection plans, DR paths, and the DR configuration are cluster-scoped.
- **RoleBinding:** Grants the role in one namespace only. A RoleBinding can reference a ClusterRole, so `dr-viewer`
  and `dr-operator` can be bound per namespace. The holder then sees and acts on the DR resources of that namespace
  and nothing else. Cluster-scoped resources are not covered by a RoleBinding.

### Access per Team for Managed Applications

Managed applications live in their own namespaces, so access can be separated per application or per team. A
RoleBinding of `dr-operator` in the namespace of an application lets a team protect, test, fail over, and relocate
that application, and no other:

```yaml title="Operator access for one team, limited to one application namespace"
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dr-operator-portal-team
  namespace: portal
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dr-operator
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: portal-team
```

A second team gets a RoleBinding in the namespace of its own application, and neither team can act on the other's.
Recovery actions and tests are created in the same namespace as the application.

A team that works with a per-namespace binding cannot read the cluster-scoped protection plans and DR paths, which
it needs to choose a path. A small additional ClusterRole grants read access to them without exposing the DR
resources of other namespaces:

```yaml title="Read access to plans and paths for all teams"
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dr-topology-viewer
rules:
  - apiGroups:
      - dr.simplyblock.io
    resources:
      - protectionplans
      - drpaths
    verbs:
      - get
      - list
      - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dr-topology-viewers
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dr-topology-viewer
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: portal-team
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: billing-team
```

### Discovered Applications

All discovered applications are declared in the Ramen ops namespace, together with their recovery actions and
tests. Access to them can therefore only be granted as a whole: a `dr-operator` binding in that namespace allows
actions on every discovered application of the hub. Kubernetes RBAC cannot limit the creation of a recovery action
to one application, because the application is named in the action's specification, not in the object name.

Access per application is currently only possible for managed applications. Discovered applications are operated
by one group of operators that is trusted with all of them.

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

The requester must hold the `override` verb on `recoveryactions`. Of the built-in roles, only `dr-admin` grants it. The reason must be 10 to 1024 characters long and is recorded in the action report.

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

The identity of the requester is stamped into the annotation `dr.simplyblock.io/created-by` of every
new RecoveryAction and TestBubble, replacing any value the request carried. The annotation cannot be changed or
removed afterward. Reports name this identity as the operator of the action or test.

Actions and tests that are created automatically, for example, the child actions of a recovery plan or the runs of a
test schedule, are stamped with the identity of the `dr-hub` service account.

## Admission Checks

The admission checks enforce rules that involve other objects or the requester:

- **References:** An action or test must take a path that exists and belongs to the application's plan.
- **Immutability:** Finished recovery actions and test bubbles cannot be changed.
- **Deletion:** A DR path or protection plan that applications still use can only be deleted after
  `dr.simplyblock.io/confirm-delete: "true"` has been set on it.
- **Overrides:** A readiness override requires the `override` verb.

!!! warning
    While `dr-hub` is unavailable, DR objects cannot be created or changed,
    including recovery actions. In an emergency where the hub is degraded, restoring `dr-hub` comes first. Running
    `dr-hub` with two replicas reduces the risk.
