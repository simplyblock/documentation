---
title: "Securing the Control Plane"
description: "Configure mTLS for simplyblock control plane communication and offload at-rest encryption keys to an external KMS (Hashicorp Vault or Openbao)."
weight: 30050
---

This page covers two security features for simplyblock on Kubernetes: transport-layer encryption and mutual
authentication for the control plane (mTLS), and offloading volume encryption keys to an external Key Management
Service (KMS).

mTLS must be configured before an external KMS can be wired up: the KMS authenticates simplyblock components using a
certificate issued by the operator-managed certificate authority, which is only provisioned when mTLS is active.

## Transport Layer Security (mTLS)

{{ experimental }}

Internal control-plane traffic between the webappapi, the operator, and the storage-node handlers can be encrypted
with TLS. When mutual TLS is additionally enabled, every component must present a valid client certificate, which
means components authenticate each other rather than relying on network position alone.

**mTLS is only supported with the cert-manager provider.** On OpenShift, the cluster's built-in certificate manager
provides one-way TLS (server certificates) but does not issue the client certificates required for mutual
authentication; running mTLS on OpenShift therefore also requires installing
[cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"} and switching the provider over.

### Prerequisites

- cert-manager installed in the cluster.
- A `ClusterIssuer` (or namespaced `Issuer`) that cert-manager can use to mint certificates. Most installations point
  this at an internal corporate CA or at the cluster-local self-signed issuer; any issuer that simplyblock components
  can trust is acceptable.

### Enabling mTLS

mTLS is configured at Helm install time by setting four values on the operator chart:

```yaml title="Helm values for mTLS"
tls:
  enabled: true
  mutual_enabled: true
  provider: cert-manager
  cert-manager:
    issuer: my-cluster-issuer
```

Apply the values during the operator install (see [Install Simplyblock Operator](k8s-control-plane.md)):

```bash title="Install the operator with mTLS"
helm upgrade --install simplyblock -n simplyblock simplyblock/spdk-csi \
    --create-namespace \
    --set operator.enabled=true \
    --set tls.enabled=true \
    --set tls.mutual_enabled=true \
    --set tls.provider=cert-manager \
    --set tls.cert-manager.issuer=my-cluster-issuer
```

Replace `my-cluster-issuer` with the name of the `ClusterIssuer` the operator should use to obtain its certificates.

### What the Operator Provisions

When mTLS is enabled, the operator creates a dedicated `ClusterIssuer` named
`simplyblock-certificate-authority-issuer` and issues all internal component certificates from it. The same issuer can
be used to mint certificates for other workloads that need to talk to simplyblock — most notably an external KMS, as
described in the next section.

!!! note "OpenShift"
    On OpenShift, setting `tls.enabled=true` with the default `tls.provider=openshift` activates one-way TLS using
    OpenShift-managed certificates. Mutual TLS is **not** available with this provider — `tls.mutual_enabled=true`
    requires `tls.provider=cert-manager` regardless of the underlying Kubernetes distribution.

## External Key Management (KMS)

{{ experimental }}

By default, simplyblock manages volume encryption keys internally. For environments that require stricter key handling
— separation of duty between storage administrators and key custodians, regular rotation, or audit trails — the
cluster can be configured to keep the key-encryption material in an external KMS. Both
[Hashicorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"} and
[Openbao](https://openbao.org/){:target="_blank" rel="noopener"} are supported; the configuration is identical for
either.

### Prerequisites

- [mTLS configured](#transport-layer-security-mtls) — required, because the vault is authenticated to the cluster via
  a certificate issued by the operator's `simplyblock-certificate-authority-issuer`.
- A Vault or Openbao instance reachable from the simplyblock namespace. The instance must be initialized and unsealed
  before configuring authentication.

### Step 1 — Issue a TLS certificate for the vault

Create a cert-manager `Certificate` resource that uses the operator-managed issuer. The resulting Secret holds the
TLS material the vault serves to clients, and is trusted by the simplyblock components because it chains to the same
CA.

```yaml title="vault-tls.yaml"
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: vault-tls
  namespace: vault
spec:
  secretName: vault-tls
  issuerRef:
    name: simplyblock-certificate-authority-issuer
    kind: ClusterIssuer
  commonName: vault
  dnsNames:
    - vault
    - vault.vault
    - vault.vault.svc
    - vault.vault.svc.cluster.local
```

Mount the resulting `vault-tls` Secret into the vault deployment as its serving certificate. Mount the issuer's CA
bundle (typically `ca.crt`) at a path the vault can read — the example below assumes `/vault/tls/ca.crt` for Vault
and `/bao/tls/ca.crt` for Openbao.

### Step 2 — Deploy the vault

Install Vault or Openbao using the upstream Helm chart and expose it inside the cluster. For the rest of this guide
the in-cluster Service is assumed to be `vault.vault:8200`; adjust the URL to match the actual deployment.

### Step 3 — Configure auth, policy, and secret engines

Configure the vault with a policy that grants simplyblock access to the `transit` and `kv` backends, enable
certificate authentication bound to the simplyblock CA, and enable the required secret engines. The script below
works for both Vault (`vault`) and Openbao (`bao`) — assign the appropriate CLI to `$CLI`.

```bash title="Configure the vault for simplyblock"
CLI=vault   # or: CLI=bao

# Policy granting access to the transit and kv backends
$CLI policy write webappapi-policy - <<EOF
path "transit/keys/*" {
  capabilities = ["create", "update", "read", "delete"]
}

path "transit/datakey/plaintext/*" {
  capabilities = ["create", "update"]
}

path "transit/datakey/wrapped/*" {
  capabilities = ["create", "update"]
}

path "transit/decrypt/*" {
  capabilities = ["create", "update"]
}

path "kv/*" {
  capabilities = ["create", "read", "update", "delete"]
}
EOF

# Certificate authentication, bound to the simplyblock cluster CA
$CLI auth enable cert
$CLI write auth/cert/certs/webappapi \
    certificate=@/${CLI}/tls/ca.crt \
    allowed_dns_sans="simplyblock-webappapi" \
    token_policies=webappapi-policy \
    token_ttl=10m \
    token_max_ttl=30m

# Secret engines used by simplyblock
$CLI secrets enable transit
$CLI secrets enable -version=1 kv
```

- The **policy** gives simplyblock the minimum capabilities it needs: managing keys and performing envelope
  encryption on the `transit` backend, and storing per-volume key material on the `kv` backend.
- The **cert auth** role only accepts clients that present a certificate chaining to the simplyblock CA *and* whose
  DNS SAN is `simplyblock-webappapi`. Tokens are short-lived (10 min, 30 min maximum) so a compromised token expires
  quickly.
- **Transit** is used for wrapping data-encryption keys; **kv** version 1 is used as the per-volume metadata store.

### Step 4 — Point the StorageCluster at the vault

Set `spec.hashicorpVaultSettings.base_url` on the `StorageCluster` resource:

```yaml title="StorageCluster with external KMS"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfname: eth0
  fabricType: tcp
  haType: ha
  hashicorpVaultSettings:
    base_url: "https://vault.vault:8200/"
```

The operator picks the setting up on the next reconcile. From that point on, volume encryption keys for this cluster
are wrapped against the vault's transit backend instead of being held inside the cluster.

### Verification

Once configured, check the operator and webappapi pod logs for vault connection messages and watch the cluster
status:

```bash title="Verify the KMS connection"
kubectl get storagecluster -n simplyblock
kubectl logs -n simplyblock deploy/simplyblock-operator
```

Creating a new encrypted volume after the vault is wired up exercises the path end-to-end; the volume's encryption key
material is then stored in the vault rather than alongside the cluster.
