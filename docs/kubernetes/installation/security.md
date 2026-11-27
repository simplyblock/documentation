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

| Helm value                                | Default        | Resource field              |
|-------------------------------------------|----------------|-----------------------------|
| `tls.enabled`                             | `true`         | `enableTLS`                 |
| `tls.mutual_enabled`                      | `true`         | `enableMutualTLS`           |
| `tls.provider`                            | `cert-manager` | `provider` (`cert-manager`) |
| `tls.cert-manager.cluster-issuer`         | `selfsigned`   |                             |
| `tls.cert-manager.createSelfSignedIssuer` | `true`         |                             |
| `tls.cert-manager.namespace`              | `cert-manager` |                             |

The chart refuses to render if TLS is enabled but the provider is not available: `tls.provider=cert-manager`
requires that the cluster serves `cert-manager.io/v1`, and `tls.provider=openshift` requires an OpenShift cluster.
Mutual TLS is only allowed with `tls.provider=cert-manager`, so every other setting is combined with
`tls.mutual_enabled=false`. A cluster without cert-manager sets `tls.enabled=false` and `tls.mutual_enabled=false`.

!!! important "TLS on OpenShift"
    On OpenShift, a Helm installation can use the OpenShift service CA with `tls.provider=openshift` and
    `tls.mutual_enabled=false`, and needs no cert-manager. The service CA issues serving certificates only, so mutual
    TLS, and with it an external KMS, requires [cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"}.
    An OperatorHub installation uses cert-manager as well, because the CA bundle ConfigMap the service CA provider
    depends on is created only by the Helm chart. See [OpenShift](openshift.md#tls-on-openshift).

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

As of now, [HashiCorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"},
[OpenBao](https://openbao.org/){:target="_blank" rel="noopener"}, and
[KMIP](https://docs.oasis-open.org/kmip/spec/v1.4/os/kmip-spec-v1.4-os.html){:target="_blank" rel="noopener"}-speaking
appliances are supported. The configuration is identical for Vault and OpenBao, and differs for KMIP where noted
below.

### Prerequisites

- **Mutual TLS:** [mTLS](#transport-layer-security-mutual-tls-mtls) has to be configured first, because the control
  plane authenticates to the KMS with a certificate issued by the `simplyblock-certificate-authority-issuer`. The
  serving certificate of the KMS itself has to chain to the same certificate authority. Without mutual TLS, the
  control plane refuses the cluster with `External KMS requires mTLS authentication to be used`, reported in a
  `ClusterCreationFailed` event on the `StorageCluster`.
- **A prepared instance:**
    === "Vault / OpenBao"
        A Vault or OpenBao instance reachable from the simplyblock namespace, initialized, unsealed, and configured
        as described in [Deploying OpenBao as a KMS](openbao-kms.md).
    === "KMIP"
        A KMIP 1.0 or later appliance reachable from the simplyblock namespace, as described in
        [Deploying a KMIP Key Management Appliance](kmip-kms.md).
- **Storage for that instance that is not simplyblock:** A KMS holding its own state on the cluster it serves
  deadlocks on a cold start, as described in
  [Where the KMS Runs](../../architecture/concepts/external-key-management.md#where-the-kms-runs).

### Deploying the Instance

=== "Vault / OpenBao"
    The instance is deployed from the upstream Helm chart, initialized, unsealed, and configured with the policy, the
    certificate authentication, and the secret engines simplyblock expects. Every step of that is described in
    [Deploying OpenBao as a KMS](openbao-kms.md), for OpenBao as well as for Vault.

    The configuration is not free-form. The control plane expects the transit engine at `simplyblock/transit`, the
    key-value engine at `simplyblock/kv`, and a certificate role named `simplyblock-webappapi` that accepts a client
    whose certificate chains to the simplyblock certificate authority and whose DNS SAN is `simplyblock-webappapi`.
    None of the three is configurable through the operator, which exposes the endpoint URL alone.

=== "KMIP"
    The appliance is configured and operated independently of simplyblock, following its vendor's own documentation.
    The only requirements the control plane places on it are a serving certificate that chains to the simplyblock
    certificate authority and a `Create`/`Activate`/`Revoke`/`Destroy`/`Encrypt`/`Decrypt` operation set, which every
    KMIP-conformant appliance implements. See
    [Deploying a KMIP Key Management Appliance](kmip-kms.md) for a reference instance suitable for testing.

### Point the Storage Cluster to the KMS

The KMS is configured with `kms.vault.endpoint` or `kms.kmip.endpoint`. It is set in the cluster template of the
`ClusterDeploymentConfig` before approving it (see [Create a Storage Cluster](k8s-storage-plane.md)):

```yaml title="ClusterDeploymentConfig with an external KMS (HashiCorp Vault or OpenBao)"
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

```yaml title="ClusterDeploymentConfig with an external KMS (KMIP)"
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
      kmip:
        endpoint: "kmip.vault.svc:5696"
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

The Vault or OpenBao endpoint must be an `https` URL whose host name resolves. The `StorageCluster` schema also admits
an `http` URL, but the control plane then refuses the cluster with a `ClusterCreationFailed` event. The KMIP endpoint
must be a `host:port` pair whose host name resolves instead, carrying no URL scheme, because KMIP is a binary protocol
over TLS rather than an HTTP API. Either form rejects a loopback or a link-local address.

!!! warning "The KMS setting is immutable"
    Once `spec.kms` is set on a `StorageCluster`, it cannot be changed or removed. An approved
    `ClusterDeploymentConfig` cannot be changed either.

!!! warning "The KMS is set when the cluster is created"
    The KMS endpoint reaches the control plane only in the request that creates the cluster. `spec.kms` added to an
    existing `StorageCluster` is accepted, but it is never sent to the control plane, so new volumes keep using the
    internal key store as well. Because the block is immutable once set, it cannot be removed afterward either.

### Verification

Neither the operator nor the creation of the cluster contacts the KMS. The first contact is the creation of the
cluster's default pool, which creates the pool's key-encryption key in the KMS. The default `StoragePool` therefore
has to reach the `Ready` phase. A KMS that cannot create the key leaves the pool with a `PoolCreationFailed` event, and
the control plane logs `Failed to create pool key`:

```bash title="Verify the KMS connection through the default pool"
kubectl -n simplyblock get storagepool production-default
kubectl -n simplyblock describe storagepool production-default
kubectl -n simplyblock logs deploy/simplyblock-webappapi | grep "pool key"
```

Creating a new encrypted volume after the KMS is wired up exercises the path end-to-end. The volume's encryption key
material is then stored in the KMS rather than alongside the cluster. See
[Volume Encryption](../usage/volume-encryption.md).
