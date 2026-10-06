---
title: "Installing the Hub"
description: "Install the dr-simplyblock-hub Helm chart, which bootstraps OCM and Ramen, deploys dr-hub, and creates the DR roles on the hub cluster."
source: "https://docs.simplyblock.io/latest/disaster-recovery/install/hub/"
---

# Installing the Hub

The hub cluster runs the DR control plane: the Open Cluster Management (OCM) cluster manager, the Ramen hub operator,
and `dr-hub`. All three are installed by the `dr-simplyblock-hub` Helm chart. The hub should be a dedicated cluster
outside the protected sites, so that it survives the loss of any single site.

Before installing, the hub must meet the [Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md).

!!! warning
    Amazon EKS cannot be used as the hub cluster. OCM requires the hub's API server to sign
    `kube-apiserver-client` certificate signing requests, which EKS does not do. EKS clusters can be used as site
    clusters.

## Preparing the S3 Credentials

The hub needs S3 credentials per bucket, not per site. Simplyblock DR configures two kinds of buckets, and each has
its own credential:

| Credential         | Bucket                                                                                   | Provided with                                                                               | Used by                                                                                                 |
|--------------------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| DR metadata bucket | Kubernetes objects of protected applications (Velero captures) and their volume metadata | The chart value `s3Credentials`, stored as a Secret in the Ramen namespace (`ramen-system`) | The protection plans (`spec.s3Profiles[].secretRef`). The hub distributes the credential to every site. |
| Archive bucket     | Signed state bundles and reports                                                         | A Secret in the `dr-simplyblock` namespace, see [Archive and State Bundle](archive.md)      | The hub only (`drConfig.spec.archive.credentialsSecretRef`)                                             |

The simplyblock backup buckets of the storage clusters are not configured in DR. They are set when each storage
cluster is deployed. See [S3 Buckets](../../deployment-preparation/dr-requirements.md#s3-buckets).

The sites do not need credentials of their own. All sites use the DR metadata credential that the hub distributes
to them, so a single DR metadata bucket with a single credential can serve every site of every plan. That bucket must
not be located at one of the protected sites, since it is needed when that site is lost.

The DR metadata credential is provided as an AWS credentials file:

```plain title="S3 credentials file (s3-credentials.conf)"
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

The chart stores it as the Secret `ramen-s3-secret`, which the protection plans reference in
`spec.s3Profiles[].secretRef`. The chart value `s3SecretNames` only renames that Secret or stores the same credential
under several names. For DR metadata buckets that need different credentials, the additional Secrets are created in
the Ramen namespace directly, with the keys `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`:

```bash title="Creating a Secret for a second DR metadata bucket with its own credential"
kubectl --context hub -n ramen-system create secret generic dr-metadata-eu-south \
  --from-literal=AWS_ACCESS_KEY_ID=<access key id> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<secret access key>
```

## Installing the Chart

The chart is published in the simplyblock Helm repository:

```bash title="Adding the simplyblock Helm repository"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update
```

```bash title="Installing the DR hub"
helm install dr-simplyblock-hub simplyblock/dr-simplyblock-hub \
  --namespace dr-simplyblock --create-namespace \
  --set-file s3Credentials=s3-credentials.conf
```

The installation takes several minutes, because the chart first runs the bootstrap Job (see
[Bootstrap Job](#bootstrap-job)) and only then deploys `dr-hub`.

Settings beyond the defaults are best kept in a values file. The following example also configures the archive
(see [Archive and State Bundle](archive.md)) and the image allow list for hook Jobs:

```yaml title="Example values file for the hub chart (hub-values.yaml)"
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
| `hub.replicas`                        | `1`                                   | Replicas of the `dr-hub` Deployment.                                                                                             |
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
| `drConfig.veleroNamespace`            | `velero`                              | Velero namespace on the sites.                                                                                                   |
| `drConfig.opsNamespace`               | `ramen-ops`                           | Ramen operations namespace.                                                                                                      |
| `drConfig.spec`                       | See the chart                         | Initial `DRConfig` spec (executor, agent, archive, retention, feature gates).                                                    |
| `console.enabled`                     | `false`                               | Deploys the DR-only Control Center next to `dr-hub`. See [Control Center](../control-center.md).                                 |
| `console.role`                        | `operator`                            | The DR role the console's ServiceAccount holds in service-account mode: `viewer`, `operator`, or `admin`.                        |
| `console.ingress.enabled`, `.host`    | `false`, empty                        | The console's Ingress. Authentication belongs in front of it.                                                                    |

The `DRConfig` created by the chart is kept when the release is uninstalled. After the installation, it is changed
directly:

```bash title="Editing the DR configuration"
kubectl edit drconfig default
```

## Bootstrap Job

With `bootstrap.enabled=true`, the chart runs the `dr-bootstrap` Job in the `dr-simplyblock` namespace as a Helm
pre-install and pre-upgrade hook. The Job is idempotent and installs:

- **OCM cluster manager:** With auto-approval for clusters that join with a bootstrap token.
- **OCM addons:** The governance-policy addon and `ocm-controller`.
- **Ramen hub operator:** Pinned by image digest.
- **Operations namespace:** The `ramen-ops` namespace.

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
    While `dr-hub` is unavailable, DR objects cannot be created, changed, or deleted. Running two replicas (`hub.replicas=2`) keeps the webhooks available during node maintenance.

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
| `dr-viewer`   | Read access to all DR objects.                                                                                                                  |
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

These ClusterRoleBindings grant the roles for all namespaces. To limit a team to the applications of one namespace,
`dr-operator` or `dr-viewer` is bound with a RoleBinding in that namespace instead. The roles and the scoping per
namespace are described in [Access Control](../configuration/access-control.md#scoping-access).

## Next Steps

- [Archive and State Bundle](archive.md)
- [Joining Site Clusters](sites.md)
