---
title: "Installing the Hub"
description: "Install the dr-simplyblock-hub Helm chart, which bootstraps OCM and Ramen, deploys dr-hub, and creates the DR roles on the hub cluster."
weight: 10110
---

The hub cluster runs the DR control plane: the Open Cluster Management (OCM) cluster manager, the Ramen hub operator,
and `dr-hub`. All three are installed by the `dr-simplyblock-hub` Helm chart. The hub should be a dedicated cluster
outside the protected sites, so that it survives the loss of any single site.

Before installing, the hub must meet the [Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md).

!!! warning
    Amazon EKS cannot be used as the hub cluster. OCM requires the hub's API server to sign
    `kube-apiserver-client` certificate signing requests, which EKS does not do. EKS clusters can be used as site
    clusters.

## Preparing the S3 Credentials

Ramen stores the Kubernetes objects and PV metadata of protected applications in one S3 bucket per site. The hub
chart stores the credential for those buckets as Kubernetes Secrets in the Ramen namespace (`ramen-system`), and Ramen
distributes them to the sites.

The credential is provided as an AWS credentials file:

```plain title="S3 credentials file (s3-credentials.conf)"
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

The chart creates one Secret per entry in `s3SecretNames`, each holding the same credential. The secret names are
referenced later by `spec.s3Profiles[].secretRef` of a [protection plan](../configuration/protection-plans.md). A
common convention is one secret name per site, so that the per-site stores can be switched to separate credentials
later without touching the plans.

## Installing the Chart

The chart is published in the simplyblock Helm repository:

```bash title="Adding the simplyblock Helm repository"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update
```

```bash title="Installing the DR hub"
helm install dr-simplyblock-hub simplyblock/dr-simplyblock-hub \
  --namespace dr-simplyblock --create-namespace \
  --set-file s3Credentials=s3-credentials.conf \
  --set s3SecretNames='{ramen-s3-secret-site-a,ramen-s3-secret-site-b}'
```

The installation takes several minutes, because the chart first runs the bootstrap Job (see
[Bootstrap Job](#bootstrap-job)) and only then deploys `dr-hub`.

Settings beyond the defaults are best kept in a values file. The following example also configures the archive
(see [Archive and State Bundle](archive.md)) and the image allow list for hook Jobs:

```yaml title="Example values file for the hub chart (hub-values.yaml)"
s3SecretNames:
  - ramen-s3-secret-site-a
  - ramen-s3-secret-site-b

bootstrap:
  imageRegistry: ""

drConfig:
  spec:
    agent:
      hookImageAllowList:
        - registry.example.com/dr-hooks/
    archive:
      endpoint: s3.eu-central-1.amazonaws.com
      bucket: dr-archive
      region: eu-central-1
      prefix: dr/
      credentialsSecretRef:
        name: dr-archive
      bundle:
        interval: 5m
        retainDays: 30
        signingKeySecretRef:
          name: dr-bundle-key
    retention:
      days: 90
      keepPerApplication: 10
```

```bash title="Installing the DR hub with a values file"
helm install dr-simplyblock-hub simplyblock/dr-simplyblock-hub \
  --namespace dr-simplyblock --create-namespace \
  --set-file s3Credentials=s3-credentials.conf \
  --values hub-values.yaml
```

## Chart Values

| Value                                 | Default                               | Description                                                                                                                      |
|---------------------------------------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `image.registry`                      | `quay.io/simplyblock-io`              | Registry of the `dr-hub` image. The same image carries `dr-bootstrap` and `dr-restore`.                                          |
| `image.tag`                           | Chart `appVersion`                    | Image tag.                                                                                                                       |
| `image.pullPolicy`                    | `IfNotPresent`                        | Image pull policy.                                                                                                               |
| `imagePullSecrets`                    | `[]`                                  | Pull secrets for the hub images.                                                                                                 |
| `hub.replicas`                        | `1`                                   | Replicas of the `dr-hub` Deployment. Replicas use leader election.                                                               |
| `hub.logLevel`                        | `info`                                | Log level of `dr-hub`.                                                                                                           |
| `hub.resources`                       | 50m CPU, 128 Mi request, 512 Mi limit | Resources of `dr-hub`.                                                                                                           |
| `hub.nodeSelector`, `hub.tolerations` | Empty                                 | Scheduling of `dr-hub`.                                                                                                          |
| `webhooks.enabled`                    | `true`                                | Deploys the admission webhooks.                                                                                                  |
| `webhooks.certManager`                | `false`                               | Issues the webhook serving certificate with cert-manager instead of a chart-generated one.                                       |
| `bootstrap.enabled`                   | `true`                                | Installs OCM and Ramen on the hub and delivers the site stack to joining clusters. Set to `false` on an existing ACM or ODF hub. |
| `bootstrap.imageRegistry`             | Empty                                 | Mirror registry for every bootstrapped image.                                                                                    |
| `bootstrap.waitTimeout`               | `15m`                                 | Maximum time for each wait of the bootstrap Job.                                                                                 |
| `bootstrap.timeoutSeconds`            | `1500`                                | Maximum run time of the whole bootstrap Job.                                                                                     |
| `s3Credentials`                       | Empty                                 | AWS credentials file with `aws_access_key_id` and `aws_secret_access_key`, passed with `--set-file`.                             |
| `s3SecretNames`                       | `[ramen-s3-secret]`                   | Names of the S3 Secrets created in the Ramen namespace.                                                                          |
| `agent.installNamespace`              | `simplyblock-dr-agent`                | Namespace of `dr-agent` on every site.                                                                                           |
| `agent.statusInterval`                | `15s`                                 | How often `dr-agent` reports its status to the hub.                                                                              |
| `agent.veleroNamespace`               | `velero`                              | Velero namespace on the sites.                                                                                                   |
| `agent.testReadRules`                 | `[]`                                  | Extra read rules for kinds that the Recipe checks of applications select during a test.                                          |
| `agent.resources`                     | 20m CPU, 64 Mi request, 256 Mi limit  | Resources of `dr-agent`.                                                                                                         |
| `agent.installStrategy.type`          | `Manual`                              | Rollout of the `dr-agent` addon when the bootstrap is disabled: `Manual` or `Placements`.                                        |
| `agent.installStrategy.placements`    | `[]`                                  | Placements that select the sites for the `Placements` strategy.                                                                  |
| `drConfig.create`                     | `true`                                | Creates the `DRConfig` singleton on install.                                                                                     |
| `drConfig.ramenNamespace`             | `ramen-system`                        | Ramen namespace on the hub.                                                                                                      |
| `drConfig.veleroNamespace`            | `velero`                              | Velero namespace on the sites, written to the Ramen configuration.                                                               |
| `drConfig.opsNamespace`               | `ramen-ops`                           | Ramen operations namespace, where discovered applications are declared.                                                          |
| `drConfig.spec`                       | See the chart                         | Initial `DRConfig` spec (executor, agent, archive, retention, feature gates).                                                    |

The `DRConfig` created by the chart is kept when the release is uninstalled. After the installation, it is changed
directly:

```bash title="Editing the DR configuration"
kubectl edit drconfig default
```

## Bootstrap Job

With `bootstrap.enabled=true`, the chart runs the `dr-bootstrap` Job in the `dr-simplyblock` namespace as a Helm
pre-install and pre-upgrade hook. The Job is idempotent and installs:

- **OCM cluster manager:** Including the join service account `agent-registration-bootstrap` in the
  `open-cluster-management` namespace, with auto-approval for clusters that join with a bootstrap token.
- **OCM addons:** The governance-policy addon (Ramen distributes the S3 Secrets to the sites through OCM policies)
  and `ocm-controller` (ManagedClusterView and the work-manager addon).
- **Ramen hub operator:** With its configuration written by `dr-hub`.
- **Operations namespace:** The `ramen-ops` namespace and a ManagedClusterSetBinding for the `default` cluster set.

The Job is removed once it succeeds. If it fails, its logs show the step that did not complete:

```bash title="Checking the bootstrap Job logs"
kubectl -n dr-simplyblock logs job/dr-bootstrap
```

Because the Job also runs on every `helm upgrade`, upgrading the chart upgrades OCM and Ramen to the versions pinned
in the new release.

## Admission Webhooks

`dr-hub` validates DR objects with admission webhooks on port 9443, served through the `dr-hub-webhook` Service. The
webhooks check references between objects (for example, the path an action takes), whether the requester may
override a readiness verdict, and that finished runs are not changed. They also stamp the creator on every
RecoveryAction and TestBubble.

The serving certificate is generated by the chart and kept across upgrades. To have cert-manager issue it instead,
cert-manager must be installed on the hub, and `webhooks.certManager=true` is set.

!!! warning
    The webhooks use `failurePolicy: Fail`. While `dr-hub` is unavailable, DR objects cannot be created, changed, or
    deleted. Running two replicas (`hub.replicas=2`) keeps the webhooks available during node maintenance.

## Verifying the Installation

All hub components must be running:

```bash title="Checking the hub components"
kubectl -n dr-simplyblock get pods
kubectl -n open-cluster-management-hub get pods
kubectl -n ramen-system get pods
```

The `DRConfig` singleton must exist, and its `RamenConfigured` condition reports whether `dr-hub` has written the
Ramen hub configuration:

```bash title="Checking the DR configuration"
kubectl get drconfig default
kubectl get drconfig default -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
```

```plain title="Example output of the DR configuration conditions"
RamenConfigured=True Written
```

Before any protection plan exists, the condition reports that the configuration carries no S3 profiles. The agents
and site stacks appear in `status.agents` and `status.stack` once site clusters have joined (see
[Joining Site Clusters](sites.md)).

## Granting Access

The chart creates three ClusterRoles but binds none of them. They must be bound to the users or groups that work with
disaster recovery:

| ClusterRole   | Grants                                                                                                                                          |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `dr-viewer`   | Read access to all DR objects and to the Ramen DRCluster, DRPolicy, and DRPlacementControl objects.                                             |
| `dr-operator` | `dr-viewer`, plus writing protected applications, recovery actions, recovery plans, test bubbles, and test schedules.                           |
| `dr-admin`    | `dr-operator`, plus writing protection plans, DR paths, the DR configuration, and restore actions, and the `override` verb on recovery actions. |

```yaml title="Binding the DR roles to groups (dr-rolebindings.yaml)"
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dr-operators
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dr-operator
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: platform-operations
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dr-admins
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dr-admin
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: dr-administrators
```

The roles are described in detail in [Access Control](../configuration/access-control.md).

## Next Steps

- [Archive and State Bundle](archive.md)
- [Joining Site Clusters](sites.md)
