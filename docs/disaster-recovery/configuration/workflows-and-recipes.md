---
title: "Workflows and Recipes"
description: "Define the boot order of an application on the target site with tiers and ready conditions, add external hooks, and use hand-written Ramen Recipes."
weight: 10250
---

When an application recovers on the target site, its objects must often start in a particular order: configuration
before workloads, the database before the application servers, the application servers before the web front end. A
protected application describes this order with tiers. For discovered applications, `dr-hub` translates the tiers into
a Ramen Recipe, which Ramen executes during the capture on the source and the restore on the target. Steps outside the
cluster, such as DNS or load balancer changes, are declared as external hooks.

The recovery workflow of an application consists of:

- **Tiers:** The boot order inside the cluster, with ready conditions as gates between tiers. Executed by Ramen.
- **External hooks:** Steps before the move (`preSource`) and after the application is healthy on the target
  (`postTargetReady`). Executed by `dr-agent`.
- **Health probes:** The final confirmation that the application serves (see
  [Protected Applications](applications.md#health-probes)).

## Tiers

`spec.tiers[]` is an ordered list. Each tier selects a group of objects and, optionally, lists ready conditions that
must be met before the next tier is restored.

| Field                         | Description                                                                                              |
|-------------------------------|----------------------------------------------------------------------------------------------------------|
| `name`                        | Tier name, at most 30 characters.                                                                        |
| `selector.resourceTypes[]`    | Resource types of the tier, for example, `configmaps`, `deployments.apps`, or `kafkas.kafka.strimzi.io`. |
| `selector.matchLabels`        | Labels the objects of the tier carry.                                                                    |
| `selector.matchExpressions[]` | Label selector expressions.                                                                              |
| `ready[]`                     | Up to 16 ready conditions that gate the next tier.                                                       |

A tier selects objects by resource type, by label, or both. The tiers are evaluated in order, and objects that no
tier selects are restored last, in a final group. Only the last tier may be unrestricted (without any selector).
Otherwise, the application reports `TierSelectsEverything`.

### Tier Label Convention

The recommended way to assign objects to tiers is the label `dr.simplyblock.io/tier`, with the tier name as value:

```bash title="Assigning objects to tiers"
kubectl --context site-a -n orders label deployment api dr.simplyblock.io/tier=app
kubectl --context site-a -n orders label deployment frontend dr.simplyblock.io/tier=web
kubectl --context site-a -n orders label virtualmachine orders-db dr.simplyblock.io/tier=db
```

Pods carry the labels of their template, not those of their owner. For a `podsReady` condition, the label must be in
the pod template.

### Default Order

Without tiers, the generated Recipe uses two tiers: `tier-config` with ConfigMaps, Secrets, and ServiceAccounts, and
`tier-workloads` with everything else.

### Suggested Tiers

`dr-hub` inspects the objects of a discovered application and suggests a boot order in `status.suggestedTiers`. The
suggestion follows the order operators, configuration, stateful workloads (StatefulSets and virtual machines), Deployments,
and network objects (Services and Routes). It is never applied automatically:

```bash title="Showing the suggested tiers of an application"
kubectl -n ramen-ops get protectedapplication orders -o jsonpath='{.status.suggestedTiers}'
```

## Ready Conditions

A ready condition is a gate after a tier. The restore of the next tier starts only when all conditions of the tier are
met, or fails after `timeoutSeconds`.

| Type                | Checks                                                                    | Fields                               |
|---------------------|---------------------------------------------------------------------------|--------------------------------------|
| `vmRunning`         | Every selected VirtualMachine reports `status.printableStatus` `Running`. | `selector`                           |
| `deploymentsReady`  | Every selected Deployment has all replicas available.                     | `selector`                           |
| `statefulSetsReady` | Every selected StatefulSet has all replicas ready.                        | `selector`                           |
| `podsReady`         | Every selected pod has the `Ready` condition.                             | `selector`                           |
| `exec`              | A command in one selected pod exits with 0.                               | `selector`, `command[]`, `container` |
| `condition`         | A Ramen check expression on objects of any resource type.                 | `resource`, `expression`             |

Common fields:

- **`selector`:** A label map that selects the objects to check. It defaults to the labels of the tier.
- **`namespace`:** The namespace of the checked objects. Required when the application has more than one protected
  namespace. Otherwise, the application reports `GateNamespaceRequired`.
- **`timeoutSeconds`:** 1 to 3600 seconds (default 120).

The following rules apply to `exec` and `condition` gates:

- **Idempotent commands:** An `exec` command runs again on every pass of Ramen's restore sequence and must be
  idempotent.
- **Pods, not guests:** An `exec` command runs in a pod container, never inside a VM guest. The virt-launcher pod of a
  VirtualMachine does not contain the guest's tools. A guest service is checked over the network from a pod, for
  example, `pg_isready -h <service>`.
- **Expression syntax:** A `condition` expression uses Ramen's check syntax, for example,
  `'{$.status.conditions[?(@.type=="Ready")].status} == {True}'`. `resource` is given as `<group>/<version>/<plural>`.

```yaml title="Tiers of a KubeVirt application with an exec gate"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: erp
  namespace: ramen-ops
spec:
  planRef: fra
  source: fra-a
  target: fra-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - erp
    pvcSelector:
      matchLabels:
        app: erp
  tiers:
    - name: config
      selector:
        resourceTypes:
          - configmaps
          - secrets
          - serviceaccounts
    - name: tools
      selector:
        matchLabels:
          app: erp-tools
      ready:
        - type: deploymentsReady
    - name: database
      selector:
        matchLabels:
          dr.simplyblock.io/tier: db
      ready:
        - type: vmRunning
        - type: exec
          selector:
            app: erp-tools
          command:
            - pg_isready
            - -h
            - erp-db
          timeoutSeconds: 60
    - name: app
      selector:
        matchLabels:
          dr.simplyblock.io/tier: app
      ready:
        - type: vmRunning
        - type: deploymentsReady
```

```yaml title="Tiers with a condition gate on an operator-managed resource"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: kafka
  namespace: ramen-ops
spec:
  planRef: fra
  source: fra-a
  target: fra-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - streaming
  tiers:
    - name: brokers
      selector:
        resourceTypes:
          - kafkas.kafka.strimzi.io
      ready:
        - type: condition
          resource: kafka.strimzi.io/v1beta2/kafkas
          expression: '{$.status.conditions[?(@.type=="Ready")].status} == {True}'
          timeoutSeconds: 600
    - name: consumers
      selector:
        resourceTypes:
          - deployments.apps
      ready:
        - type: deploymentsReady
```

## Generated Recipe

For a discovered application without `recipeRef`, `dr-hub` generates a Ramen Recipe named `<application>-dr` in the
first protected namespace and delivers it to both sites through the OCM ManifestWork `dr-recipe-<application>`:

- **Groups:** Each tier becomes a resource group `tier-<name>`. A final group `rest` collects everything no tier
  selected.
- **Volumes:** A volume group is built from the PVC selector.
- **Hooks:** Each ready condition becomes an essential check or exec hook, run right after the tier's group.
- **Workflows:** The backup and restore workflows follow the tier order. The restore workflow runs the hooks of a tier
  before the next group.

The generated Recipe for the KubeVirt example above:

```yaml title="Recipe generated by dr-hub for the erp application"
apiVersion: ramendr.openshift.io/v1alpha1
kind: Recipe
metadata:
  name: erp-dr
  namespace: erp
  annotations:
    dr.simplyblock.io/generated-from: ramen-ops/erp
  labels:
    app.kubernetes.io/managed-by: dr-hub
    dr.simplyblock.io/application: erp
spec:
  appType: simplyblock-dr
  groups:
    - name: tier-config
      type: resource
      includedNamespaces:
        - erp
      includedResourceTypes:
        - configmaps
        - secrets
        - serviceaccounts
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: tier-tools
      type: resource
      includedNamespaces:
        - erp
      labelSelector:
        matchLabels:
          app: erp-tools
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: tier-database
      type: resource
      includedNamespaces:
        - erp
      labelSelector:
        matchLabels:
          dr.simplyblock.io/tier: db
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: tier-app
      type: resource
      includedNamespaces:
        - erp
      labelSelector:
        matchLabels:
          dr.simplyblock.io/tier: app
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: rest
      type: resource
      includedNamespaces:
        - erp
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
  volumes:
    name: volumes
    type: volume
    includedNamespaces:
      - erp
    labelSelector:
      matchLabels:
        app: erp
  hooks:
    - name: tools-0-deployments
      namespace: erp
      type: check
      selectResource: deployment
      labelSelector:
        matchLabels:
          app: erp-tools
      essential: true
      onError: fail
      timeout: 120
      chks:
        - name: ready
          condition: '{$.status.conditions[?(@.type=="Available")].status} == {True}'
          onError: fail
          timeout: 120
    - name: database-0-vms
      namespace: erp
      type: check
      selectResource: kubevirt.io/v1/virtualmachines
      labelSelector:
        matchLabels:
          dr.simplyblock.io/tier: db
      essential: true
      onError: fail
      timeout: 120
      chks:
        - name: ready
          condition: '{$.status.printableStatus} == {Running}'
          onError: fail
          timeout: 120
    - name: database-1-exec
      namespace: erp
      type: exec
      selectResource: pod
      labelSelector:
        matchLabels:
          app: erp-tools
      singlePodOnly: true
      essential: true
      onError: fail
      timeout: 60
      ops:
        - name: run
          command: '["pg_isready","-h","erp-db"]'
          onError: fail
          timeout: 60
    - name: app-0-vms
      namespace: erp
      type: check
      selectResource: kubevirt.io/v1/virtualmachines
      labelSelector:
        matchLabels:
          dr.simplyblock.io/tier: app
      essential: true
      onError: fail
      timeout: 120
      chks:
        - name: ready
          condition: '{$.status.printableStatus} == {Running}'
          onError: fail
          timeout: 120
    - name: app-1-deployments
      namespace: erp
      type: check
      selectResource: deployment
      labelSelector:
        matchLabels:
          dr.simplyblock.io/tier: app
      essential: true
      onError: fail
      timeout: 120
      chks:
        - name: ready
          condition: '{$.status.conditions[?(@.type=="Available")].status} == {True}'
          onError: fail
          timeout: 120
  workflows:
    - name: backup
      failOn: any-error
      sequence:
        - group: tier-config
        - group: tier-tools
        - group: tier-database
        - group: tier-app
        - group: rest
    - name: restore
      failOn: any-error
      sequence:
        - group: tier-config
        - group: tier-tools
        - hook: tools-0-deployments/ready
        - group: tier-database
        - hook: database-0-vms/ready
        - hook: database-1-exec/run
        - group: tier-app
        - hook: app-0-vms/ready
        - hook: app-1-deployments/ready
        - group: rest
```

The Recipe in effect is shown in `status.recipe` of the ProtectedApplication, with its name, namespace, whether it was
generated, and its hash.

!!! warning
    The generated Recipe is owned by `dr-hub`. Manual edits of `<application>-dr` are reverted by the ManifestWork.
    Changes are made in the tiers of the ProtectedApplication.

## External Hooks

External hooks are the only steps that run outside of Ramen. They are meant for actions on systems around the
cluster, for example, draining a load balancer, withdrawing a VIP, or switching DNS or a global server load balancer
(GSLB) to the target site.

- **`preSource`:** Runs on the source site before the move. On a Relocate, a failing hook aborts the action, and
  nothing is moved. On a Failover, the hooks run best effort and are capped at 2 minutes in total, because the
  source site may be unreachable.
- **`postTargetReady`:** Runs on the target site once the application is healthy there.

Each hook is a Kubernetes Job:

| Field                         | Description                                                                      |
|-------------------------------|----------------------------------------------------------------------------------|
| `name`                        | Hook name.                                                                       |
| `job.image`                   | Container image. Its prefix must be in `DRConfig.spec.agent.hookImageAllowList`. |
| `job.command[]`, `job.args[]` | Command and arguments.                                                           |
| `job.env[]`                   | Environment variables.                                                           |
| `job.serviceAccountName`      | ServiceAccount of the Job.                                                       |
| `timeout`                     | Deadline of the Job (default `10m`).                                             |

Hook semantics:

- **Allow list:** Only images whose prefix is listed in `hookImageAllowList` are run. An empty allow list refuses
  every hook.
- **Execution:** Hooks run as Jobs in the `dr-agent` namespace of the site, one after the other, without retries
  (backoff limit 0). The first failing hook stops the sequence.
- **Report:** The last log line of each hook is recorded in the action report.

```yaml title="Allowing hook images in the DR configuration"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRConfig
metadata:
  name: default
spec:
  agent:
    hookImageAllowList:
      - registry.example.com/dr-hooks/
```

```yaml title="Application with external hooks for draining and DNS cutover"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: shop
  namespace: ramen-ops
spec:
  planRef: aws-fra
  source: site-a
  target: site-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - shop
  externalHooks:
    preSource:
      - name: drain
        job:
          image: registry.example.com/dr-hooks/lb-drain:1.0
          args:
            - --pool=shop
        timeout: 5m
    postTargetReady:
      - name: announce
        job:
          image: registry.example.com/dr-hooks/gslb-switch:1.0
          args:
            - --record=shop.example.com
            - --site=site-b
```

Recovery plans can declare plan-level hooks in addition (see [Recovery Plans](../operations/recovery-plans.md)).

!!! info "Coming soon"
    Hooks as Ansible Automation Platform (AAP) job templates (`aap.jobTemplate`, `aap.extraVars`) and the AAP
    executor in `DRConfig.spec.executor` are part of the API but not yet available.

## Hand-Written Ramen Recipes

For applications whose capture and restore need more than tiers and gates, for example, a pre-backup hook that
quiesces a database, a Ramen Recipe can be written by hand and referenced from the ProtectedApplication:

1. **Write the Recipe:** A Ramen Recipe (`ramendr.openshift.io/v1alpha1`) in the first protected namespace, or in the
   namespace given in `recipeRef.namespace`.
2. **Deploy it to both sites:** The Recipe must exist on the source and the target cluster. `dr-hub` does not deliver
   hand-written Recipes.
3. **Reference it:** Set `spec.discovered.recipeRef` and remove `spec.tiers`. Tiers and `recipeRef` are mutually
   exclusive.

The Recipe is used as it is, and `dr-hub` never modifies it. The `recipe-valid` readiness check blocks actions until
the Recipe exists on the cluster the application currently runs on.

```yaml title="Hand-written Ramen Recipe with a quiesce hook (recipe-shop.yaml)"
apiVersion: ramendr.openshift.io/v1alpha1
kind: Recipe
metadata:
  name: shop-recipe
  namespace: shop
spec:
  appType: shop
  groups:
    - name: config
      type: resource
      includedNamespaces:
        - shop
      includedResourceTypes:
        - configmaps
        - secrets
        - serviceaccounts
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: database
      type: resource
      includedNamespaces:
        - shop
      labelSelector:
        matchLabels:
          app: shop-db
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
    - name: rest
      type: resource
      includedNamespaces:
        - shop
      excludedResourceTypes:
        - recipes.ramendr.openshift.io
  volumes:
    name: volumes
    type: volume
    includedNamespaces:
      - shop
    labelSelector:
      matchLabels:
        app: shop
  hooks:
    - name: db-quiesce
      namespace: shop
      type: exec
      selectResource: pod
      labelSelector:
        matchLabels:
          app: shop-db
      singlePodOnly: true
      onError: fail
      timeout: 120
      ops:
        - name: checkpoint
          command: '["psql","-U","postgres","-c","CHECKPOINT"]'
          container: postgres
          onError: fail
          timeout: 60
    - name: db-ready
      namespace: shop
      type: check
      selectResource: statefulset
      labelSelector:
        matchLabels:
          app: shop-db
      essential: true
      onError: fail
      timeout: 300
      chks:
        - name: ready
          condition: '{$.spec.replicas} == {$.status.readyReplicas}'
          onError: fail
          timeout: 300
  workflows:
    - name: backup
      failOn: any-error
      sequence:
        - hook: db-quiesce/checkpoint
        - group: config
        - group: database
        - group: rest
    - name: restore
      failOn: any-error
      sequence:
        - group: config
        - group: database
        - hook: db-ready/ready
        - group: rest
```

```yaml title="ProtectedApplication referencing the hand-written Recipe"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: shop
  namespace: ramen-ops
spec:
  planRef: aws-fra
  source: site-a
  target: site-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - shop
    pvcSelector:
      matchLabels:
        app: shop
    recipeRef:
      name: shop-recipe
```

```bash title="Deploying the Recipe to both sites"
kubectl --context site-a apply -f recipe-shop.yaml
kubectl --context site-b create namespace shop --dry-run=client -o yaml | kubectl --context site-b apply -f -
kubectl --context site-b apply -f recipe-shop.yaml
```

The Recipe schema is defined by Ramen. The generated Recipe above is a valid starting point for a hand-written one.
