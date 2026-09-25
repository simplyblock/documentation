---
title: "Parallel Storage Node Addition"
description: "How the Simplyblock Operator adds storage nodes in parallel within a node-provisioning budget, while workers that host FoundationDB are added one at a time."
weight: 10320
---

When a deployment document creates storage nodes on several workers, the Simplyblock Operator can add them
concurrently rather than one after another. This significantly reduces the provisioning time of large deployments and
expansions.

A node addition reboots its host, so the concurrency is capped by a node-provisioning budget. Workers that host a
FoundationDB pod are always added one at a time, regardless of the budget, so that the control plane's own datastore
keeps enough coordinators to remain available.

## Configuring the Budget

The budget is `spec.storageNodes.nodeProvisioningBudget` of the `StorageCluster`. A deployment document sets it for a
new cluster with `spec.cluster.nodeProvisioningBudget`.

| Value         | Behavior                                                           |
|---------------|--------------------------------------------------------------------|
| `1` (default) | Workers are added one at a time, which is safe for all topologies. |
| `n > 1`       | Up to `n` workers are in the node-add process at the same time.    |

```yaml title="Example of a deployment document with a budget of four workers"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
    nodeProvisioningBudget: 4
  nodeSets:
    - name: rack-a
      groups:
        - name: default
          workers:
            - worker-1
            - worker-2
            - worker-3
            - worker-4
            - worker-5
            - worker-6
            - worker-7
            - worker-8
          devices:
            nvme: ["0000:01:00.0"]
```

```bash title="Raising the budget of an existing cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock --type=merge \
    -p '{"spec": {"storageNodes": {"nodeProvisioningBudget": 4}}}'
```

The budget counts workers, not storage nodes. A worker with two NUMA sockets, or with several nodes per socket, is
added with one request and consumes one slot.

## How Slots Are Taken

A new storage node walks its provisioning steps `CheckingHost`, `CheckingConfig`, `AwaitingSlot`, `Posting`, and
`Resolving`. In `AwaitingSlot`, it waits until it can take a slot of the budget, and it holds the slot from the moment
its node addition is posted until it has received a backend UUID or its addition has given up. The slot stays taken
while the worker reboots.

The slots in use are recorded in `StorageCluster.status.provisioningSlots`, each with the `worker` it was taken for,
the `node` that took it, and the time `takenAt`.

```bash title="Listing the slots in use"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{range .status.provisioningSlots[*]}{.worker}{"\t"}{.node}{"\t"}{.takenAt}{"\n"}{end}'
```

A node that waits for a slot emits an `AwaitingSlot` event, which names how many slots are in flight and which
workers hold them. Waiting workers go first in the order of their names, so a worker that is told to wait is not
overtaken by one that arrived later. `AwaitingSlot` has a deadline of four hours.

```bash title="Checking which nodes wait for a slot"
kubectl get events -n simplyblock \
    --field-selector reason=AwaitingSlot
```

## FoundationDB Workers

A worker counts as a FoundationDB worker when it runs a pod labeled `foundationdb.org/fdb-cluster-name`. Such a worker
waits, with an `AwaitingSlot` event, while any other FoundationDB worker is being added, even when the budget has free
slots. Rebooting several FoundationDB hosts at once would reduce the number of available coordinators below the quorum
and make the control plane unavailable.

!!! note
    The FoundationDB rule is independent of the budget. On a cluster where FoundationDB runs on every worker, the
    additions are sequential whatever the budget says.

## Pinning FoundationDB to Dedicated Workers

For the parallelism to be most effective, FoundationDB runs on a dedicated subset of workers rather than on all of
them. The node selector of the control plane, `ControlPlane.spec.source.local.nodeSelector`, also applies to the
FoundationDB pods. The Helm chart renders it from `controlplane.nodeSelector`, so the dedicated workers are labeled
before the installation.

```bash title="Labeling the workers dedicated to the control plane"
kubectl label node worker-1 worker-2 worker-4 simplyblock-control-plane=true
```

```bash title="Installing with a control-plane node selector"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --create-namespace \
    --set controlplane.nodeSelector.create=true \
    --set controlplane.nodeSelector.key=simplyblock-control-plane \
    --set controlplane.nodeSelector.value=true
```

With this setup, only the labeled workers host FoundationDB and are added one at a time. All remaining workers are
added in parallel within the budget. The installation itself is described in
[Install the Control Plane](../../installation/k8s-control-plane.md).

## Verifying the Parallelism

```bash title="Watching the provisioning steps of the new nodes"
kubectl get storagenodes -n simplyblock -w
```

While the additions run, up to the budget of workers show the step `Posting` or `Resolving` at the same time, and the
others show `AwaitingSlot`. The control plane integrates an expansion of an active cluster one node at a time
regardless of the budget, as described in [Expanding a Storage Cluster](expanding-storage-cluster.md).
