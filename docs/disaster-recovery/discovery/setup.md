---
title: "Setup"
description: "Enable discovery in the DR configuration, run the eBPF flow collector on the sites, connect a GitOps repository, and grant the roles for approval."
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

dr-hub delivers the settings to every site as the ConfigMap `dr-discovery-settings` in the agent namespace. Without
that ConfigMap, discovery is off on the site. With `enabled: false`, dr-agent removes its report and the flow collector
stops recording.

## What the Agents Collect

dr-agent reports facts about the application namespaces of its site. System and infrastructure namespaces are
excluded.

- **Workloads:** Deployments, StatefulSets, DaemonSets, pods without a controller, and KubeVirt VMs, with their owner,
  volume mounts, images, VM networks, packaging labels, ports, and whether their containers only wait (for example,
  `sleep infinity`).
- **Services:** Each Service with its selector and the workloads it selects.
- **PVCs:** Each PVC with its labels.
- **Configuration references:** Endpoints found in environment variables, command lines, and ConfigMaps, such as URLs,
  `host:port` values, and Service names. Credentials are removed from the stored excerpts.
- **Flows:** The connections recorded by the flow collector, resolved to workloads, Services, and VMs.

Secrets are never read. A reference to a Secret is taken from the workload's own spec and recorded as
`<secret>/<key>`, without its value.

The report is written every five minutes, and only when its content changed. It is stored as compressed ConfigMaps
`dr-agent-discovery` (index) and `dr-agent-discovery-<n>` (chunks) in the agent namespace, which dr-hub reads through
Open Cluster Management. A report holds up to 20,000 objects, 50,000 references, and 50,000 flow aggregates. Beyond
that, the weakest items are dropped, and the DiscoveryGraph lists the collector in `status.counts.truncated`.

## The Flow Collector

The flow collector `dr-flows` runs as a DaemonSet on every node of a site. It attaches an eBPF program to the
kernel tracepoint `sock:inet_sock_set_state` and records the client side of every TCP connection that reaches the
established state, over IPv4 and IPv6. It counts the connections per hour, source, destination, and port, and keeps
them for seven days by default. dr-agent resolves the addresses to workloads, Services, and VMs. Pod addresses of a
virt-launcher pod and the addresses of a VM's interfaces, including Multus networks, resolve to the VM.

```yaml title="Example of the flow collector settings"
spec:
  discovery:
    flows:
      optOut: [site-c]   # managed clusters without the collector
      retention: 168h    # default 7 days
```

Requirements and behavior:

- **Kernel:** Linux 5.8 or newer, for the BPF ring buffer. The program is assembled by the collector itself, so it
  needs neither BTF nor a compiler on the node. On an older kernel, the collector reports that flows are unavailable
  and idles instead of failing.
- **Tracing filesystem:** The tracepoint and its record layout are read from tracefs at `/sys/kernel/tracing` or
  `/sys/kernel/debug/tracing`. Both host paths are mounted read-only.
- **Privileges:** The collector runs as root with a read-only root filesystem, drops all capabilities, and adds
  `CAP_BPF` and `CAP_PERFMON` to load and attach the program, and `CAP_SYS_RESOURCE` for the locked-memory limit of
  kernels before 5.11. It needs no host network. These capabilities are outside the Pod Security `baseline` level, so
  the agent namespace must not enforce `baseline` or `restricted`.
- **Scheduling:** The DaemonSet tolerates every taint by default, so it also runs on control-plane and dedicated
  nodes. It is deployed on every site, but records only while discovery is enabled and the site is not in
  `flows.optOut`.
- **Recorded data:** Addresses, ports, and counts only. No payload, process names, or DNS queries are captured.
- **Volume:** Each node keeps up to 20,000 aggregates. Beyond that, the oldest buckets with the fewest connections are
  dropped. The node's aggregates are published every minute in a ConfigMap of the agent namespace and survive a
  restart of the collector.
- **Failures:** When the program cannot be loaded, the collector reports the reason and tries again after ten minutes.
- **Limitation:** Traffic of VMs that are bridged directly onto a VLAN through a secondary network does not pass the
  node's TCP stack and is not seen. Configuration references and Service selectors still cover such VMs.

The settings `flows.udp` and `flows.legacyKernels` are accepted by the API, but have no effect yet. The collector
records TCP only and does not start on kernels older than 5.8.

The collector is deployed with the hub chart's agent add-on:

| Chart value               | Default                              | Description                                  |
|---------------------------|--------------------------------------|----------------------------------------------|
| `agent.flows.enabled`     | `true`                               | `false` removes the collector from all sites |
| `agent.flows.tolerations` | `[{operator: Exists}]`               | Tolerations of the DaemonSet                 |
| `agent.flows.resources`   | 10m CPU, 32 Mi request, 128 Mi limit | Resources of the collector on every node     |

## Connecting a GitOps Repository

With a GitOps target, every bundle is proposed as a pull request. Without one, bundles are approved in the Control
Center (see [Approval Without GitOps](using-discovery.md#approval-without-gitops)).

```yaml title="Example of a GitOps target for bundles"
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
  branches, commits, and pull requests in the repository, to read pull requests, and to comment on, close, label,
  and request reviewers for them.
- **Providers:** GitHub and Gitea 1.20 or newer. For GitHub Enterprise, the API is called at
  `https://<host>/api/v3`, and for Gitea at `https://<host>/api/v1`. On Gitea, labels that do not exist in the
  repository are skipped. The provider `gitlab` is accepted by the API but not implemented. Its bundles report the
  condition `GitOpsError`.
- **Synchronization:** The hub's GitOps tool (such as Argo CD) must sync the configured path to the hub. dr-hub detects
  the applied objects by their bundle annotations (`syncDetection: objects`, the default). The values `argocd` and
  `flux` and the field `syncRef` are accepted by the API, but only `objects` is implemented.
- **Polling:** dr-hub reads the state of every open pull request once a minute. No webhook from the Git server is
  needed.

## Roles

Discovery uses the DR roles of the hub chart (see [Access Control](../configuration/access-control.md)):

| Role          | Discovery permissions                                                                                           |
|---------------|-----------------------------------------------------------------------------------------------------------------|
| `dr-viewer`   | Read graphs, bundles, runs, blueprints, mappings, and imports                                                   |
| `dr-operator` | Start and delete DiscoveryRuns, patch bundles (request a pull request, reject, answer questions)                |
| `dr-admin`    | Approve and roll back bundles in the Control Center, when no GitOps target is configured, and create SRMImports |

Approve and roll back are custom verbs on `drproposals`. An admission webhook admits the request only after a
SubjectAccessReview grants the verb to the requesting user. The roles for blueprints are listed in
[Environment Promotion](blueprints.md#roles).
