---
title: "Activating a Storage Cluster"
description: "Activate a simplyblock storage cluster on Kubernetes with an Activate operation, and learn when the operator raises the activation on its own."
weight: 10112
---

Activation makes a storage cluster serve I/O for the first time. It is normally automatic. A cluster deployed from a
`ClusterDeploymentConfig` is activated by the Simplyblock Operator once every storage node the document created is
`Online`: the operator then creates a `StorageClusterOps` named `<cluster>-activate` with the action `Activate`, and
the document reports the phase `Expanded`. See
[Create a Storage Cluster](../../installation/k8s-storage-plane.md) for the deployment flow.

An `Activate` operation is created by hand for a cluster that was not deployed from a `ClusterDeploymentConfig`, or when
the automatic activation did not complete.

```yaml title="Example of an activation (activate-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: activate-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Activate
```

```bash title="Requesting the activation"
kubectl apply -f activate-cluster.yaml
```

The operation runs the steps `Requesting` and `Awaiting`, and it succeeds once the cluster reports the backend status
`active`. An activation of a cluster that is already `active` succeeds at once without a call to the control plane.

## Activation Gates

Before the activation request is sent, two conditions are checked. Neither fails the operation immediately: it stays
in `Requesting` and emits an event, and it continues on its own once the condition holds.

- **Enough storage nodes:** The cluster has at least as many storage nodes as its erasure coding scheme needs. While it
  has fewer, a `StripeNodesNotReady` event is emitted.
- **Balanced failure domains:** On a cluster with `enableFailureDomains: true`, the failure domains hold an equal number
  of hosts. While they do not, a `FailureDomainNotReady` event names the imbalance. See
  [Managing Failure Domains](failure-domains.md).

The `Requesting` step has a deadline of two minutes, so an activation that waits on a gate for longer fails with
`StepDeadlineExceeded`. A new `Activate` operation is created once the missing nodes are online.

```bash title="Checking why an activation waits"
kubectl get events -n simplyblock \
    --field-selector involvedObject.name=activate-simplyblock-cluster
```

While the control plane activates the cluster, `StorageCluster.status.phase` reads `Activating`, and it moves to
`Online` once the cluster is `active`. How an operation is tracked, aborted, and cleaned up is described in
[Storage Cluster Actions](cluster-actions.md).
