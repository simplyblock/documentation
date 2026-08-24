---
title: "Deploying OpenBao as a KMS"
description: "Step-by-step tutorial that deploys OpenBao on Kubernetes and wires it into a simplyblock cluster as the external key management system for volume encryption."
weight: 20100
---

{{ experimental }}

This tutorial deploys [OpenBao](https://openbao.org/){:target="_blank" rel="noopener"} into a Kubernetes cluster and
wires it into simplyblock as the external key management system for volume encryption. It starts from a running
simplyblock cluster with mutual TLS enabled and ends with an encrypted volume whose key material is stored in OpenBao
rather than in the cluster. Plan for about 30 minutes.

The same steps apply to [HashiCorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"}. The few
places where the two differ are collected in [Using HashiCorp Vault Instead](#using-hashicorp-vault-instead) at the
end.

## What Gets Built

| Piece                        | Purpose                                                                          |
|------------------------------|----------------------------------------------------------------------------------|
| An OpenBao release           | A single-node instance in the `vault` namespace, serving TLS on port 8200.       |
| A cert-manager `Certificate` | The serving certificate, issued by the simplyblock certificate authority.        |
| A `transit` engine           | Wraps the data-encryption keys of the volumes. Mounted at `simplyblock/transit`. |
| A `kv` engine, version 2     | Stores the wrapped keys per volume. Mounted at `simplyblock/kv`.                 |
| A certificate policy         | Lets the control plane in, and nothing else, for ten minutes at a time.          |

## Before Starting

Four things have to be in place. The commands confirm each of them.

**Mutual TLS on the simplyblock cluster.** The control plane authenticates to OpenBao with a certificate from the
operator's certificate authority, so the authority has to exist. See
[Securing the Control Plane](../kubernetes/installation/security.md#transport-layer-security-mutual-tls-mtls) to
enable it.

```bash title="Confirming the simplyblock certificate authority is present"
kubectl get clusterissuer simplyblock-certificate-authority-issuer
```

**cert-manager.** It issues the serving certificate of the instance.

```bash title="Confirming cert-manager is running"
kubectl get pods -n cert-manager
```

**A storage class for the OpenBao data that is not backed by simplyblock.** OpenBao keeps its state on a
`PersistentVolumeClaim`, and that claim has to be served by something other than the cluster it becomes the key
management system for.

```bash title="Listing the available storage classes"
kubectl get storageclass
```

**Helm.** The instance is installed from the upstream chart.

```bash title="Confirming Helm is available"
helm version --short
```

The namespace `vault` is used throughout, for OpenBao as well, because the upstream charts and their service names are
built around it. A different namespace has to be carried through every DNS name below.

## Step 1: Write the Values File

Save the file below as `openbao-values.yaml`. It configures TLS on the listener, file storage for the data, and the
serving certificate as an extra object, so no resource has to be applied beforehand.

```yaml title="Values for an OpenBao instance serving as a simplyblock KMS (openbao-values.yaml)"
global:
  openshift: true
  tlsDisable: false

server:
  dataStorage:
    storageClass: ssd-csi

  extraEnvironmentVars:
    BAO_CACERT: /openbao/tls/ca.crt

  volumes:
    - name: tls-cert
      secret:
        secretName: openbao-server-tls

  volumeMounts:
    - name: tls-cert
      mountPath: /openbao/tls
      readOnly: true

  standalone:
    enabled: true
    config: |
      ui = true

      listener "tcp" {
        tls_disable     = 0
        address         = "[::]:8200"
        cluster_address = "[::]:8201"
        tls_cert_file   = "/openbao/tls/tls.crt"
        tls_key_file    = "/openbao/tls/tls.key"
        tls_min_version = "tls12"
      }

      storage "file" {
        path = "/openbao/data"
      }

injector:
  enabled: false

extraObjects:
  - apiVersion: cert-manager.io/v1
    kind: Certificate
    metadata:
      name: openbao-server-tls
    spec:
      secretName: openbao-server-tls
      duration: 8760h
      renewBefore: 720h
      privateKey:
        algorithm: ECDSA
        size: 256
      dnsNames:
        - openbao
        - openbao.vault
        - openbao.vault.svc
        - openbao.vault.svc.cluster.local
        - openbao-internal
        - openbao-internal.vault
        - openbao-internal.vault.svc
        - openbao-internal.vault.svc.cluster.local
      issuerRef:
        name: simplyblock-certificate-authority-issuer
        kind: ClusterIssuer
```

Two values need attention before installing. Replace `ssd-csi` with a storage class from the listing above, one that
is not backed by simplyblock, and remove `global.openshift` outside OpenShift. The DNS names are written for the `vault` namespace. The upstream sample
templates them with `.Release.Namespace`, which resolves to the same names.

## Step 2: Install OpenBao

```bash title="Installing OpenBao into the vault namespace"
helm repo add openbao https://openbao.github.io/openbao-helm
helm install openbao openbao/openbao \
    -n vault \
    --create-namespace \
    -f ./openbao-values.yaml
```

The pod stays `Running` but not ready, which is expected: an uninitialized instance reports itself unready.

```bash title="Watching the OpenBao pod come up"
kubectl -n vault get pods -w
```

```plain title="Example output of the pod listing"
NAME        READY   STATUS    RESTARTS   AGE
openbao-0   0/1     Running   0          38s
```

A pod stuck in `Pending` means the data volume was not bound, which points back at the storage class in the values
file.

## Step 3: Initialize the Instance

Initialization generates the unseal keys and the first root token. It happens once in the lifetime of an instance.

```bash title="Initializing the OpenBao instance"
kubectl -n vault exec openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ bao operator init
```

The command prints five unseal keys and one root token. Record all of them now, outside the cluster and outside the
storage they protect. They are the only copy that exists, and a lost set makes every wrapped volume key unrecoverable.

## Step 4: Unseal the Instance

An instance holds its data encrypted until three of the five keys have been supplied. Run the command three times,
with a different key each time.

```bash title="Unsealing the OpenBao instance"
kubectl -n vault exec openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ bao operator unseal <UNSEAL_KEY>
```

```bash title="Checking the seal state"
kubectl -n vault exec openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ bao status
```

The instance is ready once `Sealed` reads `false` and the pod turns ready. Note that a restart seals it again, which
makes unsealing an operational task rather than a one-off. Anything beyond a test instance is worth configuring for
auto-unseal against a cloud KMS.

## Step 5: Open a Configuration Shell

The remaining configuration runs inside the pod, with the root token from step 3. The shell carries the address, the
token, the name of the command line interface, and the path of the certificate authority, so that the commands below
are copied unchanged.

```bash title="Opening a configuration shell on the OpenBao instance"
kubectl -n vault exec -it openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ BAO_TOKEN=<ROOT_TOKEN> CLI=bao \
    CA=/openbao/tls/ca.crt sh
```

## Step 6: Write the Policy

The policy is the boundary of what simplyblock may do with the instance. It may manage its own keys, wrap and unwrap
data keys, and store key material per volume. Nothing else.

```bash title="Writing the policy for the simplyblock control plane"
$CLI policy write simplyblock-webappapi-policy - <<EOF
path "simplyblock/transit/keys/*" {
  capabilities = ["create", "update", "read", "delete"]
}

path "simplyblock/transit/datakey/plaintext/*" {
  capabilities = ["create", "update"]
}

path "simplyblock/transit/datakey/wrapped/*" {
  capabilities = ["create", "update"]
}

path "simplyblock/transit/encrypt/*" {
  capabilities = ["create", "update"]
}

path "simplyblock/transit/decrypt/*" {
  capabilities = ["create", "update"]
}

path "simplyblock/kv/*" {
  capabilities = ["create", "read", "update", "delete"]
}
EOF
```

## Step 7: Bind the Policy to the Control Plane

Certificate authentication ties the policy to exactly one client: one whose certificate chains to the simplyblock
certificate authority and whose DNS SAN is `simplyblock-webappapi`. The tokens it hands out live ten minutes, thirty
at the most, so a leaked token expires on its own.

```bash title="Enabling certificate authentication for the control plane"
$CLI auth enable cert
$CLI write auth/cert/certs/simplyblock-webappapi \
    certificate=@${CA} \
    allowed_dns_sans="simplyblock-webappapi" \
    token_policies=simplyblock-webappapi-policy \
    token_ttl=10m \
    token_max_ttl=30m
```

## Step 8: Enable the Secret Engines

```bash title="Enabling the secret engines simplyblock stores its keys in"
$CLI secrets enable -path=simplyblock/transit transit
$CLI secrets enable -path=simplyblock/kv -version=2 kv
```

```bash title="Confirming both engines are mounted"
$CLI secrets list
```

Leave the shell with `exit` once both engines appear.

!!! important
    The two mount paths and the role name are fixed. The control plane expects the transit engine at
    `simplyblock/transit`, the key-value engine at `simplyblock/kv`, and the certificate role
    `simplyblock-webappapi`, and none of the three is configurable through the operator. An instance set up at
    different paths is reachable and still rejects every key operation.

    The key-value engine has to be version 2, which is why `-version=2` is given: the control plane speaks the
    version 2 API, whose endpoints do not exist on a version 1 mount, and `secrets enable kv` creates version 1 by
    default.

## Step 9: Point the Cluster at OpenBao

The cluster learns about the instance through one field on its `StorageCluster` resource.

```bash title="Wiring the storage cluster to the OpenBao endpoint"
kubectl patch storagecluster simplyblock-cluster -n simplyblock --type=merge \
    -p '{"spec": {"hashicorpVaultSettings": {"baseURL": "https://openbao.vault:8200/"}}}'
```

The operator picks the setting up on its next reconciliation. From that point on, the encryption keys of newly created
volumes are wrapped against the transit engine instead of being held in the cluster. Volumes that already exist keep
their keys where they are.

## Step 10: Verify the Whole Path

The setup is proven by an encrypted volume, not by a reachable endpoint. Create one, then look for its key material
inside OpenBao.

```yaml title="An encrypted storage class and a claim that uses it (kms-check.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-encrypted
provisioner: csi.simplyblock.io
parameters:
  encryption: "True"
  pool_name: <POOL_NAME>
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kms-check
  namespace: simplyblock
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: simplyblock-encrypted
  resources:
    requests:
      storage: 1Gi
```

```bash title="Creating the encrypted volume"
kubectl apply -f kms-check.yaml
kubectl -n simplyblock get pvc kms-check
```

Once the claim is bound, the wrapped keys of the volume sit under `cluster/<CLUSTER_UUID>/lvol/` in the key-value
engine, and the key that wraps them is a transit key named after the storage pool.

```bash title="Listing the wrapped volume keys in OpenBao"
kubectl -n vault exec openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ BAO_TOKEN=<ROOT_TOKEN> \
    bao kv list -mount=simplyblock/kv cluster/<CLUSTER_UUID>/lvol
```

```bash title="Listing the wrapping keys in OpenBao"
kubectl -n vault exec openbao-0 -- \
    env BAO_ADDR=https://openbao.vault:8200/ BAO_TOKEN=<ROOT_TOKEN> \
    bao list simplyblock/transit/keys
```

The cluster UUID comes from `kubectl get storagecluster simplyblock-cluster -n simplyblock -o jsonpath='{.status.uuid}'`.
An entry per encrypted volume and a `pool-<POOL_UUID>` key mean the path works end to end. An empty listing means the
control plane never reached the instance, and the reason is in its log:

```bash title="Reading the control plane log after a failed key operation"
kubectl logs -n simplyblock deploy/simplyblock-operator
```

Delete the claim and the storage class once the check is done.

```bash title="Removing the verification volume"
kubectl delete -f kms-check.yaml
```

## Using HashiCorp Vault Instead

Vault is configured identically and differs in four places:

- **The chart and the certificate.** The `hashicorp/vault` chart has no `extraObjects`, so the `Certificate` is
  applied as its own resource, into the `vault` namespace and with `vault` DNS names, before the chart is installed.
- **The values.** Every `/openbao` path becomes `/vault`, `BAO_CACERT` becomes `VAULT_CACERT`, and the secret is named
  `vault-server-tls`.
- **The commands.** The binary is `vault` rather than `bao`, the address variable is `VAULT_ADDR`, the token variable
  is `VAULT_TOKEN`, and the pod is `vault-0`.
- **The endpoint.** The service is `https://vault.vault:8200/`, which is what `spec.hashicorpVaultSettings.baseURL`
  then carries.

```bash title="Installing Vault into the vault namespace"
helm repo add hashicorp https://helm.releases.hashicorp.com
kubectl create namespace vault
kubectl apply -f ./vault-certificate.yaml
helm install vault hashicorp/vault \
    -n vault \
    -f ./vault-values.yaml
```

## Where to Go Next

- [External Key Management](../architecture/concepts/external-key-management.md) explains the two key layers and what
  separation of duty the setup buys.
- [Securing the Control Plane](../kubernetes/installation/security.md#external-key-management-kms) is the reference
  for the `StorageCluster` field and the behavior of existing volumes.
- [Volume Encryption](../kubernetes/usage/volume-encryption.md) covers encrypting volumes through a `StorageClass`.
