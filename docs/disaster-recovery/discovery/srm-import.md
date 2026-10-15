---
title: "Migration From VMware Live Site Recovery"
description: "Import the protection groups and recovery plans of VMware Live Site Recovery (SRM) and propose them for the VMs migrated to KubeVirt, for approval."
weight: 10285
---

{{ experimental }}

A VMware Live Site Recovery setup consists of protection groups, recovery plans with priorities and dependencies,
startup settings, network mappings, and IP customization. An SRM import turns that setup into a
[blueprint](blueprints.md). The VMs migrated by the Migration Toolkit for Virtualization (MTV) are
then proposed with the same grouping and boot order, through the same matching, approval, and rollback as every
other bundle.

simplyblock DR does not migrate VMs. MTV migrates them, and the import uses its result.

!!! info
    The SRM import is part of the discovery preview. It reads the offline export of the Configuration Import/Export
    Tool. Reading the configuration live from the VMware Live Site Recovery REST API is not available yet, and
    neither are console screens for the import.

## Supported Versions

The import targets VMware Live Site Recovery 9.0.5, formerly Site Recovery Manager (SRM). Older releases export the
same objects and are expected to work. The parser looks elements and attributes up by name, accepts both the
attribute form and the child-element form, and accepts common aliases.

## Exporting the SRM Configuration

The Configuration Import/Export Tool on the VMware Live Site Recovery appliance writes the inventory mappings,
protection groups, and recovery plans of both sites into one XML file. See the
[VMware documentation](https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/live-site-recovery/9-0/overview/exporting-and-importing-site-recovery-manager-configuration-data/export-site-recovery-manager-configuration-data-by-using-a-script.html){:target="_blank" rel="noopener"}
for running the tool.

Store the file in a ConfigMap or Secret in the DR operations namespace of the hub. A gzip-compressed file is
accepted in `binaryData`:

```bash title="Storing the SRM export on the hub"
gzip -k srm-export.xml
kubectl -n ramen-ops create configmap srm-export --from-file=export.xml.gz=srm-export.xml.gz
```

## Importing

An SRMImport is a one-shot request that creates or updates a DRBlueprint:

```yaml title="Importing an SRM export into a blueprint"
apiVersion: dr.simplyblock.io/v1alpha1
kind: SRMImport
metadata:
  name: srm-fra-1
  namespace: ramen-ops
spec:
  source:
    configMapRef: {name: srm-export, key: export.xml.gz}
  blueprint: srm-fra             # DRBlueprint to create or update
  environment: vsphere-fra       # recorded in the blueprint's origin
  protectedSite: fra-site-a      # optional; limits the import to one SRM site
```

| Status field           | Meaning                                                                    |
|------------------------|----------------------------------------------------------------------------|
| `status.phase`         | `Pending`, `Succeeded`, or `Failed`                                        |
| `status.srmVersion`    | Version the export declares                                                |
| `status.version`       | Blueprint version the import wrote, or found unchanged                     |
| `status.counts`        | Protection groups, recovery plans, and VMs read                            |
| `status.translation[]` | Every translated feature with its SRM object and support level (up to 500) |
| `status.message`       | Reason for a failure                                                       |

An import changes nothing on a site. It only writes the blueprint, which an
[EnvironmentMapping](blueprints.md#mapping-a-blueprint) then matches against the site with the migrated VMs.

## Translation

| SRM                                                       | Becomes                                                                       | Support           |
|-----------------------------------------------------------|-------------------------------------------------------------------------------|-------------------|
| Protection group                                          | One application, its VMs are the members                                      | Full              |
| Protection group, array-based (SAN, vVols)                | One consistency group for the application's PVCs                              | Full, new volumes |
| Recovery plan, protected and recovery site                | RecoveryPlan on the DR path between the mapped sites                          | Full              |
| VM priority groups 1 to 5                                 | Tier order inside an application, plan priority across applications           | Full              |
| VM dependencies                                           | Tier split inside a priority, `dependsOn` across applications                 | Full              |
| Wait for VMware Tools, with timeout                       | `vmRunning` gate and a gate on the guest agent's connection, with the timeout | Full              |
| Network mappings                                          | Network roles, matched to SiteProfile roles through the mapping               | Full              |
| Test network mappings                                     | The isolated test network of the DR path                                      | Full              |
| IP customization, subnet rules                            | Network CIDR hints                                                            | Partial           |
| IP customization, per-VM addresses                        | A question per VM: a DHCP reservation through the site mapping                | Partial           |
| Additional delay after power-on                           | A question, there is no delay gate                                            | Question          |
| Pre-power-on and post-power-on commands on the SRM server | A question: recreate as a Job or a hook                                       | Partial           |
| Commands in the guest, prompt steps                       | A question, there is no guest command and no manual pause gate                | Question          |
| Startup action "Do not power on"                          | A blocking question                                                           | Question          |
| vSphere Replication RPO                                   | A question when the plan's replication interval is longer                     | Question          |
| Folder, resource pool, and placeholder datastore mappings | Not applicable                                                                | Ignored, listed   |

Partial and question rows become notes in the blueprint, and so questions in every bundle built from it. Every row is
also recorded in `status.translation` with the SRM object it came from.

## Matching the Migrated VMs

MTV labels every VM it creates with the source VM's ID (`vmID`, the vSphere managed object ID, such as `vm-1001`). A
member of an SRM blueprint matches on that label first, with full confidence. Then it matches on the VM name as MTV
normalizes it (lower case, invalid characters replaced by `-`) and on its NIC MAC addresses, which MTV keeps by
default. A VM that matches none of these is a blocking question in the bundle.

The bundles carry the source `srm:<blueprint>@<version>`. SRM's grouping and boot order take precedence over the
roles discovery assigns, but they do not silently override what is observed. When the production graph shows a
dependency that SRM's order contradicts, for example, a VM that connects to a VM SRM starts later, the bundle asks.
VMs that SRM protects but that are not migrated yet are `missing` questions. VMs in the namespaces that SRM never
protected are `extra` questions.

## Migration in Waves

When an MTV migration finishes, the new VM appears in the site's report, the graph is rebuilt, and every
EnvironmentMapping of that site is matched again. A `missing` member becomes matched, and a revised bundle supersedes
the open one. Waves of migrations therefore converge to one bundle per protection group without starting a run. Each
revision waits for approval.

## Roles

| Role          | Permissions                                                                                 |
|---------------|---------------------------------------------------------------------------------------------|
| `dr-operator` | Create the EnvironmentMapping for the SRM blueprint                                         |
| `dr-admin`    | Create SRMImports, because the export is read from a ConfigMap or Secret of their namespace |

See [Environment Promotion](blueprints.md#roles) for the other blueprint roles.
