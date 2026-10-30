---
title: "Securing the Control Plane"
description: "Configure TLS and mutual TLS for simplyblock control plane traffic on Kubernetes and store volume encryption keys in HashiCorp Vault or OpenBao."
weight: 30050
---

This page covers two security features for simplyblock on Kubernetes: transport-layer encryption and mutual
authentication for the control plane (mTLS), and offloading volume encryption keys to an external Key Management
Service (KMS).

mTLS must be configured before an external KMS can be wired up: the KMS authenticates simplyblock components using a
certificate issued by the operator-managed certificate authority, which is only provisioned when mTLS is active.

## Transport Layer Security (Mutual TLS / mTLS)

Internal traffic between the control plane, the operator, the CSI driver, and the storage nodes is encrypted with TLS.
When mutual TLS is enabled, every component must additionally present a valid client certificate, which means
components authenticate each other rather than relying on network position alone.

TLS and mutual TLS are **enabled by default**. The settings are made with the `tls.*` Helm values at installation. The
chart copies them into the `tls` block of the `ControlPlane` resource (`spec.source.local.tls`) and of the
`SimplyblockDriver` resource (`spec.tls`):

| Helm value                                | Default        | Resource field                             |
|-------------------------------------------|----------------|--------------------------------------------|
| `tls.enabled`                             | `true`         | `enableTLS`                                |
| `tls.mutual_enabled`                      | `true`         | `enableMutualTLS`                          |
| `tls.provider`                            | `cert-manager` | `provider` (`cert-manager` or `OpenShift`) |
| `tls.cert-manager.cluster-issuer`         | `selfsigned`   |                                            |
| `tls.cert-manager.createSelfSignedIssuer` | `true`         |                                            |
| `tls.cert-manager.namespace`              | `cert-manager` |                                            |

The chart refuses to render if TLS is enabled but the provider is not available: `tls.provider=cert-manager`
requires that the cluster serves `cert-manager.io/v1`, and `tls.provider=openshift` requires an OpenShift cluster. A
cluster that has neither must set `tls.enabled=false`.

!!! important "Mutual TLS on OpenShift"
    **mTLS is only supported with the cert-manager certificate provider.**

    On OpenShift, the built-in service CA provides one-way TLS (server certificates) but does not issue the client
    certificates required for mutual authentication. With `tls.provider=openshift`, the value `tls.mutual_enabled`
    must be set to `false`. To enable mTLS on OpenShift,
    [cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"} must be installed and the certificate
    provider must be switched to `cert-manager`.

### Prerequisites

- **Cert-manager:** cert-manager must be installed in the cluster.
- **Issuer:** By default, the chart creates a self-signed `ClusterIssuer` named `selfsigned`. To use an existing
  issuer instead, for example, one backed by an internal corporate certificate authority (CA), set
  `tls.cert-manager.createSelfSignedIssuer=false` and name the issuer in `tls.cert-manager.cluster-issuer`.

### Enabling mTLS With an Existing Issuer

```yaml title="Helm values for mTLS"
tls:
  enabled: true
  mutual_enabled: true
  provider: cert-manager
  cert-manager:
    createSelfSignedIssuer: false
    cluster-issuer: my-cluster-issuer
```

Apply the values during the operator installation (see [Install Simplyblock Operator](k8s-control-plane.md)):

```bash title="Install the operator with mTLS"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --create-namespace \
    --set tls.enabled=true \
    --set tls.mutual_enabled=true \
    --set tls.provider=cert-manager \
    --set tls.cert-manager.createSelfSignedIssuer=false \
    --set tls.cert-manager.cluster-issuer=my-cluster-issuer
```

Replace `my-cluster-issuer` with the name of the `ClusterIssuer` the chart should use to mint its CA certificate.

### What Gets Provisioned

With `tls.provider=cert-manager`, the chart mints a CA certificate from the configured issuer and creates a dedicated
`ClusterIssuer` named `simplyblock-certificate-authority-issuer`, which signs all internal component certificates. With
mutual TLS, client certificates are issued for the operator, the two CSI plugins, Prometheus, and the FoundationDB
peers. The same issuer can be used to mint certificates for other workloads that need to talk to simplyblock, in
particular an external KMS, as described in the next section.

### Checking the Effective Settings

```bash title="Show the TLS settings of the control plane and the CSI driver"
kubectl -n simplyblock get controlplane simplyblock -o jsonpath='{.spec.source.local.tls}'
kubectl -n simplyblock get simplyblockdriver simplyblock -o jsonpath='{.spec.tls}'
```

## External Key Management (KMS)

By default, simplyblock manages volume encryption keys internally. For environments that require stricter key handling,
the cluster can be configured to keep the key-encryption material in an external KMS. This especially includes
environments with strict separation of duty between storage administrators and key custodians, regular rotation, or
audit trails.

As of now, [HashiCorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"} and
[OpenBao](https://openbao.org/){:target="_blank" rel="noopener"} are supported. The configuration is identical for
either of them.

### Prerequisites

- **Mutual TLS:** [mTLS](#transport-layer-security-mutual-tls-mtls) has to be configured first, because the control
  plane authenticates to the KMS with a certificate issued by the `simplyblock-certificate-authority-issuer`.
- **A prepared instance:** A Vault or OpenBao instance reachable from the simplyblock namespace, initialized,
  unsealed, and configured as described in [Deploying OpenBao as a KMS](../../tutorials/openbao-kms.md).
- **Storage for that instance that is not simplyblock:** A KMS holding its own state on the cluster it serves
  deadlocks on a cold start, as described in
  [Where the KMS Runs](../../architecture/concepts/external-key-management.md#where-the-kms-runs).

### Deploying the Instance

The instance is deployed from the upstream Helm chart, initialized, unsealed, and configured with the policy, the
certificate authentication, and the secret engines simplyblock expects. Every step of that is described in
[Deploying OpenBao as a KMS](../../tutorials/openbao-kms.md), for OpenBao as well as for Vault.

The configuration is not free-form. The control plane expects the transit engine at `simplyblock/transit`, the
key-value engine at `simplyblock/kv`, and a certificate role named `simplyblock-webappapi` that accepts a client whose
certificate chains to the simplyblock certificate authority and whose DNS SAN is `simplyblock-webappapi`. None of the
three is configurable through the operator, which exposes the endpoint URL alone.

### Point the Storage Cluster to the KMS

The KMS is configured with `kms.vault.endpoint`. It is set in the cluster template of the
`ClusterDeploymentConfig` before approving it (see [Create a Storage Cluster](k8s-storage-plane.md)):

```yaml title="ClusterDeploymentConfig with an external KMS"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: production-deployment
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: production
    maxSubsystemCount: 50
    vcpuCount: 8
    kms:
      vault:
        endpoint: "https://vault.vault.svc:8200"
  nodeSets:
    - name: rack-a
      groups:
        - name: default
          workers: [worker-1, worker-2, worker-3]
          devices:
            nvme: ["0000:01:00.0"]
```

The expansion copies the block to `StorageCluster.spec.kms`. The operator hands the KMS endpoint to the control
plane when it creates the storage cluster, so the KMS has to be configured before the cluster is created.

The endpoint must be an `http` or `https` URL whose host name resolves. Loopback and link-local addresses are
rejected.

!!! warning "The KMS setting is immutable"
    Once `spec.kms` is set on a `StorageCluster`, it cannot be changed or removed. An approved
    `ClusterDeploymentConfig` cannot be changed either.

!!! warning "Existing volumes are not affected"
    Only encryption keys for volumes that are created after the KMS is wired up are wrapped and stored in the KMS.
    Existing volumes keep their internally managed keys.

### Verification

Once configured, check the cluster status and the operator logs:

```bash title="Verify the KMS connection"
kubectl -n simplyblock get storagecluster production -o jsonpath='{.status.message}'
kubectl -n simplyblock logs deploy/simplyblock-operator
```

Creating a new encrypted volume after the KMS is wired up exercises the path end-to-end. The volume's encryption key
material is then stored in the KMS rather than alongside the cluster. See
[Volume Encryption](../usage/volume-encryption.md).
