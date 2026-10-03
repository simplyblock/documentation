---
title: "Site Profiles and Mappings"
description: "Describe each site with a SiteProfile, bind network roles and DHCP servers, and let the site mapper rewrite VM network attachments and reserve guest addresses on the target."
weight: 10260
---

An application that recovers on another site finds a different environment: other network attachment names, other
VLANs, other address ranges, or other DNS domains. The site mapper describes each site in a `SiteProfile`, compares
the two sites of every DR path, and translates what a recovered application references. In the current release, it
maps the secondary networks of KubeVirt virtual machines (NetworkAttachmentDefinitions) and keeps the guest addresses
of their interfaces through DHCP reservations. Everything else is restored as captured and must carry the same name
on both sites.

The resources of the site mapper live in the API group `sitemap.simplyblock.io/v1alpha1` on the hub and are written by
the `dr-admin` role.

## Site Profiles

A `SiteProfile` is cluster-scoped, one per managed cluster, and named after it. dr-hub creates the profile of every
cluster a protection plan names, with an empty `spec`, and never writes the `spec`. A profile outlives the plans that
named it.

- **Inventory:** `status.inventory` is discovered by dr-agent and read-only. It holds the cluster ID, the nodes with
  their zones and readiness, the NetworkAttachmentDefinitions with their parsed CNI configuration (type, master or
  bridge, VLAN, IPAM type and ranges), the storage, snapshot, ingress, and gateway classes, the MetalLB address pools
  with their advertisements and the addresses Services hold from them, the ingress and base domains, the registry
  mirrors, the pod and service CIDRs, and the EgressIPs. `status.reportedAt` is the time of the last report.
- **Bindings:** `spec` binds logical roles to concrete objects of the site. A profile holds site facts only and has
  no direction. Roles are the one convention of the model: the same role name means the same thing on every site.
- **Renderings:** `status.renderings` holds the generation of every artifact dr-hub rendered for the site (see
  [Renderings](#renderings)).

| Field                                     | Description                                                                                                 |
|-------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `spec.logicalNetworks[].role`, `.nad`     | The NetworkAttachmentDefinition (`<namespace>/<name>`) that plays the role on this site.                    |
| `spec.guestNetworks[].role`, `.cidr`      | The guest subnet of the role on this site.                                                                  |
| `spec.guestNetworks[].gateway`            | The gateway address of the guest subnet. Never handed out as a reservation.                                 |
| `spec.guestNetworks[].reservedHostIDs[]`  | Host IDs that are never used for a derived address, for example, the gateway and the DHCP server.           |
| `spec.guestNetworks[].dhcpServerRef`      | The `DHCPServer` of the role, overriding `spec.dhcpServerRef`.                                              |
| `spec.addressPools[].role`, `.pool`       | The MetalLB address pool that plays the role (compared between sites, not rewritten yet).                   |
| `spec.domains.apps`, `.base`, `.shared[]` | The application and base domains of the site and the domains shared by all sites (compared, not rewritten). |
| `spec.registryMirror`                     | The registry mirror recovered workloads pull from (compared, not rewritten).                                |
| `spec.dhcpServerRef`                      | The site's `DHCPServer` for every guest network without its own.                                            |

```yaml title="Site profiles of two sites with different VLANs"
apiVersion: sitemap.simplyblock.io/v1alpha1
kind: SiteProfile
metadata:
  name: site-a
spec:
  logicalNetworks:
    - role: app
      nad: app-net/vlan110
  guestNetworks:
    - role: app
      cidr: 192.168.110.0/24
      reservedHostIDs: [1, 2]
      dhcpServerRef: site-a
  dhcpServerRef: site-a
---
apiVersion: sitemap.simplyblock.io/v1alpha1
kind: SiteProfile
metadata:
  name: site-b
spec:
  logicalNetworks:
    - role: app
      nad: app-net/vlan210
  guestNetworks:
    - role: app
      cidr: 192.168.210.0/24
      reservedHostIDs: [1, 2]
      dhcpServerRef: site-b
  dhcpServerRef: site-b
```

## Profile Comparison per Path

For every DR path, dr-hub compares the profiles of its two sites and writes the result to the path:
`status.profileConsistency` is `Consistent`, `Inconsistent`, or `Unknown` (a profile has no inventory yet), and
`status.profileComparison[]` holds one row per field with `Pass`, `Fail`, `Warn`, or `NotApplicable` and a message
that names what differs.

| Row                  | Passes when                                                                                                    |
|----------------------|----------------------------------------------------------------------------------------------------------------|
| `inventory-reported` | Both dr-agents reported their inventory within five minutes.                                                   |
| `logical-networks`   | The same roles are bound on both sites, each to a NetworkAttachmentDefinition that exists on its site.         |
| `guest-networks`     | The same roles exist on both sites. Warns when the target prefix is smaller than the source prefix.            |
| `address-pools`      | The same roles are bound on both sites, each to a pool that exists on its site.                                |
| `domains`            | The shared domains are equal on both sites.                                                                    |
| `registry-mirror`    | A mirror is bound on both sites or on neither. Warns when a bound mirror is not among the site's mirrors.      |
| `storage-classes`    | Every StorageClass the plan selects on the source has a selected class of the same name on the target (warns). |
| `zones`              | Both zones of a sync path have Ready nodes. Not applicable to paths between clusters.                          |
| `test-target`        | A path that declares `Test` names an isolated NetworkAttachmentDefinition that exists on the target.           |

The readiness check `profile-consistent` reads this verdict. It is advisory: an inconsistent or unknown comparison
makes a path `Degraded`, not `NotReady`, because whether a difference matters depends on what an application
references. That is decided by its findings.

## Findings and Guest Addresses

dr-agent reports every KubeVirt virtual machine of its cluster with, per Multus network, the NetworkAttachmentDefinition
it resolves to, the pinned MAC address of the interface, and the addresses the running instance reports. From the
report of the site an application runs on, dr-hub derives the application's findings and evaluates them along every
declared path that starts there:

| Situation                                                                                                            | Result                                                       |
|----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| The NAD is bound to a role on the source profile, the role is bound on the target profile, and that NAD exists there | `Resolved` by role (strategy `map`) to the target's NAD      |
| A NAD of the same name exists on the target and no role binds it                                                     | `Resolved` (strategy `keep`)                                 |
| Anything else                                                                                                        | `Open`, with the reason and the target NADs of the same VLAN |

For every interface on a role that has a guest network on both sites, dr-hub derives the guest address on the target:
the host ID of the current address is kept and placed into the target subnet (`192.168.110.178` becomes
`192.168.210.178`). The derivation needs a pinned MAC address and a current address inside the source subnet. It is
`Open` when the MAC is not pinned, the address lies outside the subnet or is not known yet, the host ID does not fit
the target prefix, it is a reserved host ID or the gateway, or it collides with the derived address of another
virtual machine.

The results are in the ProtectedApplication:

- **Verdict:** `status.siteMapping` is `Resolved`, `Open`, `NotApplicable` (no VM on a Multus network), or `Unknown`
  (the site's dr-agent has not reported yet).
- **Findings:** `status.mapping.findings[]` holds one entry per VM and network, with the result, strategy, role, and
  target value per path.
- **Guests:** `status.mapping.guests[]` holds one entry per VM interface on a guest network, with its MAC address,
  current addresses, and the reservation per site.
- **Counts:** `status.mapping.counts` holds the numbers of open and resolved items.

The readiness check `findings-resolved` blocks a path while a finding on it is `Open`: an unresolved NAD leaves the
restored VM without its network, an unresolved address leaves the guest without its reservation. While an application
moves, the mapping of its previous site is kept until the new site reports all of its VMs running.

```bash title="Showing the site mapping of an application"
kubectl -n ramen-ops get papp wordpress -o jsonpath='{.status.siteMapping}{"\n"}'
kubectl -n ramen-ops get papp wordpress -o jsonpath='{.status.mapping}' | jq
```

## DHCP Servers

A `DHCPServer` is cluster-scoped and describes one DHCP server of a site. dr-hub renders the reservations of every
server into a ConfigMap on the server's site and never talks to the server itself: the ConfigMap is the API.

| Field                    | Description                                                                                                                                        |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `spec.site`              | The managed cluster the server runs on.                                                                                                            |
| `spec.type`              | `dnsmasq`, the only type.                                                                                                                          |
| `spec.dnsmasq.namespace` | Namespace of the ConfigMap dnsmasq reads its reservations from.                                                                                    |
| `spec.dnsmasq.configMap` | Name of that ConfigMap. dr-hub writes the key `sitemap.hosts` with one `<mac>,<ip>,<name>` line per reservation (the format of `--dhcp-hostsdir`). |

```yaml title="DHCP server of a site"
apiVersion: sitemap.simplyblock.io/v1alpha1
kind: DHCPServer
metadata:
  name: site-b
spec:
  site: site-b
  type: dnsmasq
  dnsmasq:
    namespace: sitemap-dhcp
    configMap: dnsmasq-reservations
```

A site profile names the server in `spec.dhcpServerRef` or per guest network. The server holds the current address of
every VM on its site and the derived address of every VM that may arrive along a declared path. Reservations are
sticky: an address once reserved for a MAC address is kept. `status.reservations` is the number of reservations, and
`status.generation` the rendered generation. The dnsmasq deployment has to reload its hosts file when the ConfigMap
changes, for example, through a sidecar that sends `SIGHUP`, and should publish the VM names in DNS, so that
applications that reach each other by name keep working on the other site.

## Renderings

For every site, dr-hub renders what a recovery there needs and delivers it with one ManifestWork per site:

- **Velero resource modifier:** The ConfigMap `sitemap-live` in the site's Velero namespace holds one rule per `map`
  finding of every application that may arrive on the site. A rule rewrites the VM's
  `spec.template.spec.networks[].multus.networkName` from the source value to the target value during the restore.
  dr-agent runs a mutating admission webhook for Velero `Restore` objects in its Velero namespace that points every
  restore without a resource modifier at `sitemap-live`. The webhook fails open.
- **DHCP reservations:** The ConfigMap of every `DHCPServer` of the site.

The readiness check `artifacts-current` (advisory) compares the generation of the artifacts on each site with the
rendered one and warns when a rendering has not arrived, is stale, or the restore webhook is not registered. The
RecoveryAction report of every move lists the expected and the observed guest address of every interface
(`status.report.guests[]`). A mismatch is reported, not fatal.

## Tests

A test failover does not use the production mapping. Every Multus network of a VM is replaced by a same-name copy of
the path's isolated NetworkAttachmentDefinition (`spec.test.isolatedNad`) in the bubble namespace, and a reference to a
NAD in another namespace is rewritten to that copy. A DHCP server on the isolated network that serves the production
reservations gives the VMs in the bubble their production addresses. See [Test Failover](../testing/test-failover.md).

## What Is Not Mapped Yet

Everything the site mapper does not translate is restored as captured and must exist under the same name on both
sites of a path: StorageClasses and VolumeSnapshotClasses (the plan's selector picks them by label, and the
`storage-classes` comparison warns about a missing name), zone names referenced by node affinities, ingress, load
balancer, priority, and runtime classes, and container image names. IP addresses in Services, Routes, and Ingresses
and host names are restored unchanged.

!!! info "Coming soon"
    - **Further categories:** Mapping of StorageClasses, zones, load balancer addresses and pools, domains and Route
      host names, registries, and literal values in ConfigMaps and Secrets, with the strategies `derive`,
      `regenerate`, `create`, and `ignore` next to `map` and `keep`.
    - **Managed applications:** The renderings cover what a Velero restore creates. Applications delivered by GitOps
      are not rewritten.
    - **Announcement handover:** `spec.announcementHandover` of a DR path is stored, but has no effect yet. VIPs are
      withdrawn and announced through the `preSource` and `postTargetReady` hooks.

## Site Networking Designs

The network design of the sites decides which identities survive a failover.

| Design                                  | Behavior with the site mapper                                                                                                                                                           |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Stretched layer 2, identical ranges     | Nothing to map. VMs keep their addresses, Services keep their VIPs. Only one site may announce a VIP at a time: a `preSource` hook withdraws it, a `postTargetReady` hook announces it. |
| Different VLANs or NAD names per site   | Bind the NADs to one role on both profiles. VMs are restored with the target's NAD, and their guest addresses keep the host ID in the target subnet through the DHCP reservations.      |
| Routed subnets with DNS or GSLB cutover | Services receive a new VIP from the target pool, and a `postTargetReady` hook switches DNS. VM guest addresses are derived into the target subnet when the roles have guest networks.   |
| Load balancer pools of different size   | Services without a fixed VIP receive a new address. Services with a fixed VIP need the same address range on both sites until pools are mapped.                                         |
