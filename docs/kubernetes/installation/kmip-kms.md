---
title: "Deploying a KMIP Key Management Appliance"
description: "Wire a KMIP key management appliance into simplyblock as the external key store for volume encryption, with a PyKMIP reference instance for testing."
weight: 30065
---

[KMIP](https://docs.oasis-open.org/kmip/spec/v1.4/os/kmip-spec-v1.4-os.html){:target="_blank" rel="noopener"} (Key
Management Interoperability Protocol) is a vendor-neutral protocol for key-management appliances. Simplyblock speaks
it directly, so any appliance that implements `Create`, `Activate`, `Revoke`, `Destroy`, `Encrypt`, and `Decrypt` can
serve as the external key store for volume encryption, in place of HashiCorp Vault or OpenBao.

A production-grade appliance is configured and operated independently of simplyblock, following its vendor's own
documentation, and only the requirements in [Before Starting](#before-starting) below apply to it. For environments
without one, this guide also deploys a [PyKMIP](https://pykmip.readthedocs.io/){:target="_blank" rel="noopener"}
reference server, suitable for testing the integration but not for production: its key database lives in the pod and
is lost on every restart.

## What Gets Built

The reference instance, if one is deployed:

| Piece                        | Purpose                                                                          |
|------------------------------|----------------------------------------------------------------------------------|
| A cert-manager `Certificate` | The serving certificate, issued by the simplyblock certificate authority.        |
| A `ConfigMap`                | The PyKMIP server configuration and its entry point script.                      |
| A `Deployment`               | A single PyKMIP server process, reusing the control plane's own container image. |
| A `Service`                  | The in-cluster endpoint, `kmip-server.simplyblock.svc.cluster.local:5696`.       |

## Before Starting

Three things have to be in place. The commands confirm each of them.

**Mutual TLS on the simplyblock cluster.** The control plane authenticates to the appliance with a certificate from
the operator's certificate authority, and the appliance's own serving certificate has to chain to the same
authority. See [Securing the Control Plane](security.md#transport-layer-security-mutual-tls-mtls) to enable it.

```bash title="Confirming the simplyblock certificate authority is present"
kubectl get clusterissuer simplyblock-certificate-authority-issuer
```

**cert-manager**, to issue the reference instance's serving certificate. Skip this check against a production
appliance, whose certificate is provisioned through its own PKI.

```bash title="Confirming cert-manager is running"
kubectl get pods -n cert-manager
```

**A storage cluster that has not been created yet.** The operator hands the KMS endpoint to the control plane only
when it creates the storage cluster, so the endpoint has to be part of the `ClusterDeploymentConfig` before it is
approved. An existing storage cluster cannot be moved to an external KMS. See
[Create a Storage Cluster](k8s-storage-plane.md) for the discovery that produces the draft.

```bash title="Confirming the deployment config is still a draft"
kubectl -n simplyblock get clusterdeploymentconfig
```

The document to use is in phase `Draft` and has `spec.approved: false`.

## Step 1: Issue the Serving Certificate

Skip this step for a production appliance. Its certificate comes from its own PKI, trusted the same way, chained to
`simplyblock-certificate-authority-issuer`.

```yaml title="Certificate for the PyKMIP reference instance"
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: kmip-server-tls
  namespace: simplyblock
spec:
  secretName: kmip-server-tls
  issuerRef:
    name: simplyblock-certificate-authority-issuer
    kind: ClusterIssuer
  commonName: kmip-server.simplyblock.svc.cluster.local
  dnsNames:
    - kmip-server.simplyblock.svc.cluster.local
    - kmip-server
    - kmip-server.simplyblock.svc
```

```bash title="Issuing the certificate and waiting for it"
kubectl apply -f kmip-server-certificate.yaml
kubectl -n simplyblock wait --for=condition=Ready certificate/kmip-server-tls --timeout=120s
```

It is issued before the pod that mounts it, below: a pod whose mounted `Secret` does not exist yet sits in
`ContainerCreating` until kubelet's own retry backoff finds it, which can add minutes to an otherwise instant
rollout.

## Step 2: Deploy the Reference Instance

Reusing the control plane's own container image means no separate image to build: `pykmip` is already one of its
runtime dependencies.

```yaml title="Reference PyKMIP server (kmip-server.yaml)"
apiVersion: v1
kind: ConfigMap
metadata:
  name: kmip-server-config
  namespace: simplyblock
data:
  server.conf: |
    [server]
    hostname=0.0.0.0
    port=5696
    certificate_path=/etc/kmip/tls/tls.crt
    key_path=/etc/kmip/tls/tls.key
    ca_path=/etc/kmip/tls/ca.crt
    auth_suite=TLS1.2
    policy_path=/etc/kmip/policies
    enable_tls_client_auth=True
    logging_level=INFO
    database_path=/var/lib/pykmip/pykmip.db
  run_server.py: |
    from kmip.services.server.server import KmipServer

    if __name__ == "__main__":
        server = KmipServer(config_path="/etc/kmip/server.conf", log_path="/tmp/kmip.log")
        server.start()
        server.serve()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kmip-server
  namespace: simplyblock
  labels:
    app: kmip-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kmip-server
  template:
    metadata:
      labels:
        app: kmip-server
    spec:
      containers:
        - name: kmip-server
          image: registry.simplyblock.ai/simplyblock/simplyblock:<TAG>
          command: ["python", "/etc/kmip/run_server.py"]
          ports:
            - containerPort: 5696
          volumeMounts:
            - {name: config, mountPath: /etc/kmip/server.conf, subPath: server.conf}
            - {name: config, mountPath: /etc/kmip/run_server.py, subPath: run_server.py}
            - {name: tls, mountPath: /etc/kmip/tls, readOnly: true}
            - {name: policies, mountPath: /etc/kmip/policies}
            - {name: db, mountPath: /var/lib/pykmip}
      volumes:
        - {name: config, configMap: {name: kmip-server-config}}
        - {name: tls, secret: {secretName: kmip-server-tls}}
        - {name: policies, emptyDir: {}}
        - {name: db, emptyDir: {}}
---
apiVersion: v1
kind: Service
metadata:
  name: kmip-server
  namespace: simplyblock
spec:
  selector:
    app: kmip-server
  ports:
    - {port: 5696, targetPort: 5696}
```

```bash title="Deploying the reference instance"
kubectl apply -f kmip-server.yaml
kubectl -n simplyblock rollout status deployment/kmip-server --timeout=120s
```

The server entry point is a script rather than an inline command, and guarded by `if __name__ == "__main__":`:
`KmipServer.start()` spawns a `multiprocessing.Manager`, and without the guard the forkserver that spawns re-imports
the entry point as `__main__` and starts a second server mid-bootstrap.

The key database and the policy directory are both `emptyDir` volumes: the reference instance holds no state across
a pod restart, which is what makes it unsuitable for production but keeps it exempt from
[Where the KMS Runs](../../architecture/concepts/external-key-management.md#where-the-kms-runs) (its storage does not
depend on the cluster it serves, since it does not persist anything at all).

## Step 3: Point the Cluster at the Appliance

The storage cluster learns about the appliance through `kms.kmip.endpoint` in the cluster template of the
`ClusterDeploymentConfig`. The expansion copies the block to `StorageCluster.spec.kms`, and the operator sends the
endpoint to the control plane when it creates the cluster. The examples use the draft
`discovered-initial-discovery` from [Create a Storage Cluster](k8s-storage-plane.md), whose cluster template names
the cluster `production`.

```bash title="Adding the KMIP endpoint to the draft deployment config"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge \
    -p '{"spec": {"cluster": {"kms": {"kmip": {"endpoint": "kmip-server.simplyblock.svc.cluster.local:5696"}}}}}'
```

A production appliance outside the cluster is addressed the same way, by its own `host:port`:

```bash title="Pointing the draft deployment config at an external appliance"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge \
    -p '{"spec": {"cluster": {"kms": {"kmip": {"endpoint": "kmip.example.com:5696"}}}}}'
```

With the endpoint in place, the draft is approved as usual:

```bash title="Approving the deployment config"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery \
    --type=merge -p '{"spec": {"approved": true}}'
```

The endpoint must be a `host:port` pair whose host name resolves from the operator. Loopback and link-local
addresses are rejected, and a refused endpoint shows up as an `InvalidConfig` event on the `StorageCluster`.

!!! warning "The KMS setting is immutable"
    Once `spec.kms` is set on a `StorageCluster`, it cannot be changed or removed, and an approved
    `ClusterDeploymentConfig` cannot be changed either. The endpoint has to be correct before approval.

## Step 4: Verify the Whole Path

The setup is proven by an encrypted volume, not by a reachable endpoint. Create one, then look for its key
operations in the appliance's own log.

```yaml title="An encrypted storage class and a claim that uses it (kms-check.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-encrypted
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: production-default
  encryption: "true"
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

The cluster UUID comes from `kubectl get storagecluster production -n simplyblock -o jsonpath='{.status.uuid}'`. The
example uses the default pool of the cluster, `production-default`.

A pool's key-encryption key is created the first time a volume in it is encrypted, and each volume's two
data-encryption keys are wrapped against it. Both surface as `Create`, `Activate`, `Encrypt`, and `Decrypt`
operations in the appliance's log, each carrying the control plane's client identity:

```bash title="Reading the reference instance's log"
kubectl -n simplyblock exec deploy/kmip-server -- cat /tmp/kmip.log
```

```plain title="Example log entries for a pool key and a volume's data-encryption keys"
kmip.server.engine - INFO - Processing operation: Create
kmip.server.engine.cryptography - INFO - Generating a AES symmetric key with length: 256
kmip.server.engine - INFO - Created a SymmetricKey with ID: 2
kmip.server.session.00000003 - INFO - Session client identity: simplyblock-webappapi
kmip.server.engine - INFO - Processing operation: Activate
kmip.server.engine - INFO - Processing operation: Encrypt
kmip.server.engine - INFO - Processing operation: Encrypt
```

No entry, after a volume is created, means the control plane never reached the appliance, and the reason is in its
own log:

```bash title="Reading the control plane log after a failed key operation"
kubectl logs -n simplyblock deploy/simplyblock-webappapi
```

Delete the claim and the storage class once the check is done.

```bash title="Removing the verification volume"
kubectl delete -f kms-check.yaml
```

## Where to Go Next

- [External Key Management](../../architecture/concepts/external-key-management.md) explains the two key layers, the
  authentication model, and what separation of duty the setup buys.
- [Securing the Control Plane](security.md#external-key-management-kms) is the reference for the `kms` block and its
  immutability.
- [Volume Encryption](../usage/volume-encryption.md) covers encrypting volumes through a `StorageClass`.
