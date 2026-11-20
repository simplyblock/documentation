---
title: "Deploying a SAN Datastore"
description: "Deploy a simplyblock SAN datastore on Kubernetes: state the storage array before discovery, review the draft, and let the operator provision the LUNs."
weight: 30110
---

{{experimental}}

A SAN datastore is deployed with the same discovery and approval flow as any other storage plane (see
[Install Simplyblock Storage Plane on Kubernetes](k8s-storage-plane.md)). The difference is the order of knowledge.
The cluster's data LUNs do not exist before the deployment, so they cannot be discovered. They are created on the
array when each storage node is added. The array is therefore stated before discovery, and the discovery run drafts
the deployment around it.

The array, the hosts, and the credentials are prepared as described in
[SAN Datastore](../../deployment-preparation/san-datastore.md) first.

## Deployment Flow

```plain title="Deployment flow of a SAN datastore"
Secret / Vault KV / KMIP secret  ──► the array login, stored before anything else
OperatorOps (Discover, multiAttach) ──► probes the workers, reads their initiators,
                                         writes a draft that carries the array
ClusterDeploymentConfig          ──► Draft  (review the findings, then spec.approved: true)
  StorageCluster                 ──► Creating ──► Online
    status.array                 ──► registered (the control plane has connected to the array)
  StorageNode(s)                 ──► AwaitingArray ──► Provisioning ──► Online
                                     (each node add creates, maps, and adopts its LUN)
```

Nothing is sent to the array during discovery. The array is contacted for the first time when the cluster
registers it, after approval.

## Storing the Array Login

The login is stored in one of the three [credential sources](../../deployment-preparation/san-datastore.md#credentials).
A Kubernetes Secret lives in the namespace of the storage cluster, and its keys are the login fields of the plug-in
(see the [array plug-in reference](../../reference/san-array-plugins.md)).

=== "Secret"
    ```yaml title="Example of the array login as a Secret (pure01-login.yaml)"
    apiVersion: v1
    kind: Secret
    metadata:
      name: pure01-login
      namespace: simplyblock
    type: Opaque
    stringData:
      api_token: "<API_TOKEN>"
    ```

=== "Vault KV"
    ```bash title="Storing the array login in a Vault KV v2 secret"
    vault kv put secret/arrays/ontap01 \
        username=simplyblock \
        password='<PASSWORD>'
    ```

=== "KMIP secret"
    The login is stored as a secret-data object on the KMIP server with the server's own tools. The object holds the
    login fields as a JSON object, for example, `{"username": "simplyblock", "password": "<PASSWORD>"}`, or a single
    value such as an API token. Its unique identifier is used in the deployment.

Without an external key management service, a `Secret` login is refused unless the cluster opts in to storing it in
the local key store, where it is effectively unencrypted. The opt-in is meant for test environments and is given once
the cluster exists. The refused registration is then retried automatically:

```bash title="Allowing the local key store to hold array credentials (test environments only)"
kubectl -n simplyblock exec -it deploy/simplyblock-admin-control -- \
    {{ cliname }} cluster set <CLUSTER_ID> allow_local_kms_credentials true
```

## Discovery with the Storage Array

The initial discovery of a fresh installation drafts a regular storage plane and is not used for a SAN datastore. A
discovery run is requested with the array stated under `spec.discover.multiAttach`. It requires logical block
devices.

```yaml title="Example of a discovery run for a SAN datastore on Pure Storage FlashArray (discover-san.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-san
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: san-draft
    enableLogicalBlockDevices: true
    nodeSelector:
      storage.simplyblock.io/storage: "true"
    multiAttach:
      faultTolerance: 1
      array:
        plugin: pure-flasharray
        endpoint: https://pure01.example.com
        protocol: iscsi
        lunSize: 4Ti
        caBundle: |
          -----BEGIN CERTIFICATE-----
          ...
          -----END CERTIFICATE-----
        options:
          eradicate: "true"
        credentials:
          source: Secret
          secretRef:
            name: pure01-login
```

```bash title="Running the discovery"
kubectl apply -f discover-san.yaml
kubectl -n simplyblock get operatorops discover-san -w
```

The `multiAttach` block has the same fields as the one of the `StorageCluster`:

| Field                          | Meaning                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------|
| `faultTolerance`               | Storage-node failures the cluster survives: `1` or `2`. Fixed when the cluster is created. |
| `array.plugin`                 | The [array plug-in](../../reference/san-array-plugins.md) key                              |
| `array.endpoint`               | The array's management URL. Omitted for `aws-ebs`.                                         |
| `array.protocol`               | `iscsi`, `fc`, `nvme-tcp`, `nvme-rdma`, `nvme-fc`, or `sdc`. Omitted for `aws-ebs`.        |
| `array.lunSize`                | The size of every storage node's LUN                                                       |
| `array.caBundle`               | The PEM certificate the management endpoint is verified against                            |
| `array.options`                | The plug-in's own options, as strings                                                      |
| `array.credentials.source`     | `Secret`, `VaultKV`, `KMIPSecret`, or `None` (`aws-ebs` on the instance role)              |
| `array.credentials.secretRef`  | The Secret with the login, for `Secret`                                                    |
| `array.credentials.vaultKV`    | `mount`, `path`, and optionally `version` of the Vault KV v2 secret, for `VaultKV`         |
| `array.credentials.kmipSecret` | `uid`, and optionally `field`, of the KMIP object, for `KMIPSecret`                        |

```yaml title="Example of a login kept in Vault instead of a Secret"
credentials:
  source: VaultKV
  vaultKV:
    mount: secret
    path: arrays/ontap01
```

## Reviewing the Draft

The draft differs from a regular one in three places:

- **The array:** `spec.cluster.multiAttach` carries the array as stated in the run, and `spec.cluster.raidDevices` is
  set, because the array protects every LUN.
- **One device per node:** Every group names one local device per storage node, the smallest disk of the worker. It
  becomes the node's journal. The node's data device is its LUN.
- **The stripe:** A stated stripe has no effect. The cluster runs `1+0`.

The run's findings are reported as events on the `OperatorOps` resource and are cleared before approval:

| Finding                        | Meaning                                                                                                |
|--------------------------------|--------------------------------------------------------------------------------------------------------|
| `ArrayInitiatorMissing`        | The named workers report no initiator for the array's protocol, so the array cannot present them a LUN |
| `MultiAttachNeedsBlockDevices` | The run found NVMe devices. It is repeated with `enableLogicalBlockDevices`.                           |

```bash title="Listing the findings of the discovery run"
kubectl -n simplyblock get events \
    --field-selector involvedObject.name=discover-san
```

The document is validated against the needs of a SAN datastore as well. These findings are reported on the
`ClusterDeploymentConfig` while it is a draft. A document approved with any of them is not expanded but fails, and
an approved document can no longer be edited, so they are cleared before approval:

| Finding                     | Meaning                                                                  |
|-----------------------------|--------------------------------------------------------------------------|
| `StripeBelowMinimumNodes`   | Fewer storage nodes than the fault tolerance plus one                    |
| `StripeBelowMinimumWorkers` | The storage nodes sit on fewer workers than the fault tolerance plus one |
| `MultiAttachJournalDevice`  | A group names more or fewer local devices than one per storage node      |

The document's schema also refuses a SAN datastore without `raidDevices`, on NVMe devices, in the `Single` cluster
mode, or with `enableJournalDevice`.

## Approval and Provisioning

The draft is approved by setting `spec.approved: true`. The cluster is then created in multi-attach mode, and the
array is registered as soon as the cluster exists. The control plane connects to the array with the login before it
saves anything, so a wrong endpoint, certificate, or login shows up here.

```bash title="Following the array registration"
kubectl -n simplyblock get storagecluster <CLUSTER_NAME> \
    -o jsonpath='{.status.array}'
```

```plain title="Example output of a registered array"
{"id":"5e0c2f6a-...","observedGeneration":1,"protocols":["fc","iscsi","nvme-fc","nvme-rdma","nvme-tcp"],"registered":true}
```

A refused registration leaves `registered` unset, carries the control plane's reason in `message`, and raises the
event `ArrayRegistrationRefused`. The storage nodes wait in the step `AwaitingSlot` with the reason `AwaitingArray`,
and no node is added until the array is registered. A corrected `StorageCluster` or Secret is registered again
automatically.

Once the array is registered, the storage nodes are added one by one. For every node, the host is registered on the
array with its initiator, the node's LUN is created and mapped to it, and the host is rescanned until the LUN appears.
The LUN is then presented to the node's standby nodes as their roles are assigned. Activation follows as for any
other cluster.

## Deployment without Discovery

A SAN datastore can be declared directly in a `StorageCluster` as well. The `StorageNode` resources then name one local
device per node, the journal disk.

```yaml title="Example of a StorageCluster for a SAN datastore on NetApp ONTAP (storage-cluster-san.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: san
  namespace: simplyblock
spec:
  maxSubsystemCount: 30
  vcpuCount: 8
  deviceClass: LogicalBlock
  raidDevices: true
  multiAttach:
    faultTolerance: 2
    array:
      plugin: netapp-ontap
      endpoint: https://ontap01.example.com
      protocol: nvme-tcp
      lunSize: 8Ti
      options:
        svm: svm_simplyblock
        aggregates: aggr1,aggr2
      credentials:
        source: VaultKV
        vaultKV:
          mount: secret
          path: arrays/ontap01
```
