---
title: "Setup"
description: "Enable discovery in the DR configuration, run the eBPF flow collector on the sites, connect a GitOps repository and grant the roles for approval."
weight: 10281
---

Discovery is configured in the section `spec.discovery` of the DRConfig `default` on the hub. The site agents receive
their settings from the hub, so no configuration is needed on the sites.

## Enabling Discovery

```yaml title="Enabling discovery in the DR configuration"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DRConfig
metadata:
  name: default
spec:
  discovery:
    enabled: true
    autoRules: true      # write bundles on every graph change (default)
    rebuild: 2m          # debounce of graph rebuilds (default)
```

With `enabled: true`, every dr-agent publishes a discovery report of its site, and dr-hub builds one DiscoveryGraph
per site. With `autoRules`, the rule engine writes bundles whenever a graph changes. Without it, bundles are only
written by a [DiscoveryRun](using-discovery.md#running-discovery).

## What the Agents Collect

dr-agent reports facts about the application namespaces of its site. System and infrastructure namespaces are
excluded.

- **Workloads:** Deployments, StatefulSets, DaemonSets, pods without a controller and KubeVirt VMs, with their owner,
  volume mounts, images, VM networks, packaging labels, and ports.
- **Services:** Each Service with its selector and the workloads it selects.
- **PVCs:** Each PVC with its labels.
- **Configuration references:** Endpoints found in environment variables, command lines, and ConfigMaps, such as URLs,
  `host:port` values and Service names. Credentials are removed from the stored excerpts.

Secrets are never read. A reference to a Secret is taken from the workload's own spec and recorded as
`<secret>/<key>`, without its value.

## The Flow Collector

The flow collector `dr-flows` runs as a DaemonSet on every node of a site. It records the TCP connections that pods and
VMs open, counts them per hour and source, destination and port, and keeps them for seven days by default. dr-agent
resolves the addresses to workloads, Services, and VMs.

```yaml title="Flow collector settings"
spec:
  discovery:
    flows:
      optOut: [site-c]   # managed clusters without the collector
      retention: 168h    # default 7 days
      udp: false         # TCP only (default)
```

Requirements and behavior:

- **Kernel:** Linux 5.8 or newer. On an older kernel the collector reports that flows are unavailable instead of
  failing. `legacyKernels: true` lets it start with `CAP_SYS_ADMIN` on older kernels.
- **Privileges:** The collector runs as root with the capabilities `CAP_BPF`, `CAP_PERFMON` and `CAP_SYS_RESOURCE`,
  and mounts tracefs and debugfs read-only. It needs no host network.
- **Recorded data:** Addresses, ports, and counts only. No payload is captured.
- **Limitation:** Traffic of VMs that are bridged directly onto a VLAN through a secondary network does not pass the
  node's TCP stack and is not seen. Configuration references and Service selectors still cover such VMs.

The collector is deployed with the hub chart's agent add-on. The chart value `agent.flows.enabled: false` removes it
from all sites.

## Connecting a GitOps Repository

With a GitOps target, every bundle is proposed as a pull request. Without one, bundles are approved in the Control
Center (see [Approval Without GitOps](using-discovery.md#approval-without-gitops)).

```yaml title="A GitOps target for bundles"
spec:
  discovery:
    gitOps:
      provider: github            # github or gitea
      url: https://github.com/acme/dr-config
      baseBranch: main
      path: dr/                   # directory of the bundles (default)
      credentialsSecretRef:
        name: dr-gitops-token
      reviewers: [platform-team]
      labels: [dr-bundle]
```

- **Credentials:** A Secret in the namespace of dr-hub with the key `token`. The token needs permission to create
  branches, commits and pull requests in the repository.
- **Providers:** GitHub (including GitHub Enterprise) and Gitea 1.20 or newer.
- **Synchronization:** The hub's GitOps tool (such as Argo CD) must sync the configured path to the hub. dr-hub detects
  the applied objects by their bundle annotation (`syncDetection: objects`, the default).

## Roles

Discovery uses the DR roles of the hub chart (see [Access Control](../configuration/access-control.md)):

| Role          | Discovery permissions                                                                    |
|---------------|------------------------------------------------------------------------------------------|
| `dr-viewer`   | Read graphs, bundles and runs                                                            |
| `dr-operator` | Start and delete DiscoveryRuns, request a pull request for a bundle, reject a bundle     |
| `dr-admin`    | Approve and roll back bundles in the Control Center, when no GitOps target is configured |

Approve and roll back are custom verbs on `drproposals`. An admission webhook admits the request only after a
SubjectAccessReview grants the verb to the requesting user.
