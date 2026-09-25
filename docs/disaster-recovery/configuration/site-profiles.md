---
title: "Site Profiles and Mappings"
description: "Naming requirements between sites, the planned site mapper for differing networks and classes, and how site networking designs affect failover."
weight: 10260
---

An application that recovers on another site finds a different environment: other network attachment names, other
address ranges, other load balancer pools, or other DNS domains. How these differences are handled decides whether the
application works after a failover. The current release restores applications exactly as they were captured, which
requires identical names on all sites. A site mapper that translates between sites is planned.

## Identical Names Between Sites

In the current release, an application recovers exactly as captured. No object is rewritten during a failover, a
relocation, or a test. The following names must therefore be identical on the source and the target site of every DR
path:

- **NetworkAttachmentDefinitions:** Multus NADs referenced by pods and virtual machines must exist with the same name,
  in the same namespace, on both sites.
- **StorageClasses and VolumeSnapshotClasses:** The protected classes must have the same names on both sites. Ramen
  pairs them as peer classes.
- **Zones:** Node affinities and topology spread constraints that name a `topology.kubernetes.io/zone` must find the
  same zone names on the target.
- **Other class names:** Ingress classes, load balancer classes, priority classes, and runtime classes referenced by
  the application.
- **Container registries:** Images must be pullable under the same names on both sites, for example, through a shared
  registry or identical mirrors.

IP addresses, MAC addresses, Service addresses, and Route or Ingress host names are restored unchanged. Whether they
work on the target depends on the network design of the sites (see [Site Networking Designs](#site-networking-designs)).

The readiness of every application reports the check `site-mapping` as informational, and `status.siteMapping` of
the ProtectedApplication and `status.profileConsistency` of the DR path report `NotAvailable`.

## Planned Site Mapper

!!! info "Coming soon"
    A site mapper will describe each site and translate the differences along a DR path. It is not part of the
    current release, and the resources below are not yet available.

    - **SiteProfile:** One profile per cluster. Its status holds the discovered inventory (NADs, zones, storage and
      other classes, MetalLB pools, domains, registry mirrors, CIDRs, and egress IPs). Its spec binds site roles to
      that inventory, for example, logical networks per role, guest networks, and address pools. A profile describes
      a site and has no direction.
    - **Findings and resolutions:** The mapper scans protected applications for site-specific values and records each
      one as a finding. A resolution decides, per DR path, how a finding is handled, with the precedence resource over
      namespace over global.
    - **Strategies:** `map` (translate to a named value on the target), `keep` (use the same value), `derive` (compute
      the target value, for example, the same offset in a target pool), `regenerate` (create a new value, for
      example, a MAC address), `ramen` (leave it to Ramen), `ignore`, and `create` (create the missing object on the
      target).
    - **Categories:** NADs, zones, guest addresses, addresses (VIPs, egress IPs, CIDRs), domains, classes, registries,
      host devices, MAC addresses, NodePorts, IP families, and literal values in configuration.

    Failback uses the mapping of the reverse path. Addresses hard-coded in ConfigMaps, Secrets, or environment
    variables will be reported, but not rewritten.

## Site Networking Designs

The network design of the sites decides which identities survive a failover. Four common designs and their effect on
disaster recovery are described below.

### Stretched Layer 2 With Identical Address Ranges

Both sites share the same layer 2 segments, or use identical CIDRs and identical load balancer (for example, MetalLB)
pool names and ranges. Pod networks are local to each cluster, but VM guest addresses and VIPs are valid on both sites.

- **Failover behavior:** VMs keep their guest IP addresses, and Services keep their load balancer VIPs. Clients do not
  need to change their target address.
- **Announcement:** Only one site may announce a VIP at a time. During the cutover, the source site withdraws the
  announcement, and the target site starts announcing it, for example, by changing the node selectors of the MetalLB
  BGPAdvertisement or L2Advertisement.
- **Mapping strategy:** `keep` for guest addresses and VIPs, with `announcementHandover: true` on the DR path.
- **Current release:** Works without rewriting, because the names and ranges are identical. The announcement handover
  is not automated: a `preSource` hook withdraws the VIPs, and a `postTargetReady` hook announces them on the target
  (see [External Hooks](workflows-and-recipes.md#external-hooks)). `announcementHandover` is stored, but has no effect
  yet.

### Separate Routed Subnets With DNS or GSLB Cutover

Each site has its own routed subnets and load balancer pools. Addresses are not valid on the other site, and clients
reach the application by a DNS name that is switched to the active site, for example, by a GSLB.

- **Failover behavior:** VIPs and guest addresses change. Clients follow the DNS change, delayed by the record TTL.
- **Host names:** Route and Ingress host names, TLS certificates, and external-dns annotations under a shared domain
  (for example, `shop.example.com`) are kept, and the DNS or GSLB record is updated after the application is ready on
  the target.
- **Mapping strategy:** `derive` or `map` for VIPs, guest addresses re-derived into the target network (keeping the
  host part in the target CIDR or using fixed per-site addresses), and `keep` for host names under the shared domain.
  Host names under a site-specific cluster domain are regenerated.
- **Current release:** Works for containers whose Services receive a new VIP from the target pool. The DNS or GSLB
  switch is implemented as a `postTargetReady` hook. VMs with static guest addresses keep their source addresses,
  which are not valid on the target, and guest IP customization is not yet available.

### Different NAD or VLAN Names per Site

The sites provide the same logical networks, but under different NetworkAttachmentDefinition names or VLAN IDs, for
example, `vlan-120` on one site and `prod-app` on the other.

- **Failover behavior:** A VM or pod that references a NAD name that does not exist on the target does not start.
- **Mapping strategy:** `map` by VLAN ID or by the role of the network, as bound in the SiteProfiles. `create` creates
  the missing NAD on the target.
- **Current release:** Not supported without renaming. The NADs must exist under the same name on both sites. A
  common workaround is to create a NAD on each site under a shared logical name that points to the local VLAN.

### Load Balancer Pools of Different Size

Both sites use load balancer VIP pools, but with different ranges or sizes, for example, a `/26` on the primary site
and a `/28` on the fallback site.

- **Failover behavior:** A Service that requests a specific VIP from the source pool does not get it on the target.
- **Mapping strategy:** `derive` when the pools have the same size (the VIP keeps its offset in the pool), and `map`
  with explicit address pairs when they do not.
- **Current release:** Services without a fixed VIP receive a new address from the target pool, and a
  `postTargetReady` hook updates DNS. Services with a fixed VIP need the same address range on both sites.

## Summary

| Design                              | Current release                                  | With site mapper                                       |
|-------------------------------------|--------------------------------------------------|--------------------------------------------------------|
| Stretched layer 2, identical ranges | Works, VIP handover through hooks                | `keep` with automated announcement handover            |
| Routed subnets, DNS or GSLB         | Works for dynamic VIPs, DNS switch through hooks | `derive` or `map` for VIPs, re-derived guest addresses |
| Different NAD or VLAN names         | Requires identical NAD names                     | `map` by VLAN or role, `create`                        |
| Different pool sizes                | Works for dynamic VIPs only                      | `derive` or `map`                                      |
