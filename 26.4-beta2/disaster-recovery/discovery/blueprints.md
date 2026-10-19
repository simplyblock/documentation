---
title: "Environment Promotion"
description: "Export the approved DR setup of a test environment as a blueprint and propose it in production, matched against the production site, for approval."
source: "https://docs.simplyblock.io/latest/disaster-recovery/discovery/blueprints/"
---

# Environment Promotion

Applications are usually set up and tested in a non-production environment, for example, UAT, before they go to
production. Discovery has the most data there: the flow collector can watch all traffic, and failovers can be
rehearsed. A blueprint carries the result to production. Production gets the same protection setup without repeating
the discovery and without running the flow collector at all.

A blueprint is the environment-neutral form of approved applications and their recovery plans. In production, an
environment mapping translates its names, matches its members against the production site, and writes ordinary
[bundles](index.md#bundles). They are approved like every other bundle. Nothing is applied without approval.

!!! info
    Environment promotion is part of the discovery preview. The console screens for exporting and mapping blueprints
    are not available yet. Blueprints and mappings are created as resources on the hub.

## Flow

1. **Approve in UAT:** Discover the applications in UAT and approve their bundles until they are `Applied`. See
   [Using Discovery](using-discovery.md).
2. **Export:** A BlueprintExport turns the applied bundles of one UAT site into a DRBlueprint. Bundles that are not
   applied are never exported.
3. **Transfer:** Copy the DRBlueprint to the production hub, as YAML or through the hub's GitOps repository.
4. **Map:** An EnvironmentMapping on the production hub names the blueprint, the production site, and how UAT names
   translate to production names.
5. **Approve in production:** dr-hub matches every member of the blueprint in the production site and writes one
   bundle per application and per recovery plan. Each bundle is dry-run, opened as a pull request, and approved as
   usual.
6. **Update:** A later export from UAT with changed content raises the blueprint's version. The production bundles
   are revised, and a new bundle supersedes the previous one.

## Exporting a Blueprint

A BlueprintExport is a one-shot request in the DR operations namespace of the UAT hub:

```yaml title="Exporting the applied bundles of a UAT site"
apiVersion: dr.simplyblock.io/v1alpha1
kind: BlueprintExport
metadata:
  name: uat-export-1
  namespace: ramen-ops
spec:
  site: uat-a              # managed cluster whose applied bundles are exported
  environment: uat         # recorded in the blueprint's origin
  blueprint: uat           # DRBlueprint to create or update
  applications: [shop, queue, wiki]   # optional; empty exports every applied application
```

For each application, the export takes the newest bundle in phase `Applied`. Applications without an applied bundle
are listed in `status.skipped` with their phase. Applied recovery-plan bundles become the blueprint's recovery plans
if all of their applications are exported. A plan that names an application outside the export is skipped with the
reason.

| Status field       | Meaning                                                |
|--------------------|--------------------------------------------------------|
| `status.phase`     | `Pending`, `Succeeded`, or `Failed`                    |
| `status.version`   | Blueprint version the export wrote, or found unchanged |
| `status.exported`  | Applications in the blueprint                          |
| `status.skipped[]` | Applications and plans left out, each with its reason  |
| `status.message`   | Reason for a failure                                   |

An export writes nothing when the content did not change, so exporting again is safe. The blueprint version rises
only with changed content.

## What a Blueprint Contains

- **Applications:** The approved ProtectedApplication of each application as a template in UAT names, with its tiers,
  readiness gates, and health probes.
- **Members:** The workloads, VMs, and PVCs of each application, with the facts used to find them in another
  environment: name, workload kind, image repositories without tag, role, Helm release or Argo CD application,
  identity labels, and the DR labels they carry.
- **Networks:** The SiteProfile roles of the networks the application's VMs attach to.
- **Recovery plans:** The approved RecoveryPlans in UAT names.
- **Answers:** The answers given to the bundles' questions in UAT. Production shows them, but the approver answers
  again.

A blueprint never carries evidence, IP addresses, MAC addresses, environment variable values, Secret names, image tags
or digests, or names of clusters other than the origin site. Probe targets and gate commands are carried as written.
An IP address in them becomes a question in production unless an endpoint mapping covers it.

## Moving a Blueprint to Production

A DRBlueprint is an ordinary resource. Copy it from the UAT hub and create it on the production hub:

```bash title="Copying a blueprint between hubs"
kubectl --context uat-hub -n ramen-ops get drblueprint uat -o yaml > blueprint-uat.yaml
kubectl --context prd-hub -n ramen-ops apply -f blueprint-uat.yaml
```

The file can also be committed to the production hub's GitOps repository, so that the GitOps tool creates it. dr-hub
does not write blueprints into Git by itself yet.

## Mapping a Blueprint

An EnvironmentMapping on the production hub applies a blueprint to one production site:

```yaml title="Mapping the UAT blueprint onto a production site"
apiVersion: dr.simplyblock.io/v1alpha1
kind: EnvironmentMapping
metadata:
  name: uat-to-prd
  namespace: ramen-ops
spec:
  blueprint: uat
  site: prd-a
  namespaces:
    - {from: "*-uat", to: "*-prd"}
  sites:
    - {from: uat-a, to: prd-a}
    - {from: uat-b, to: prd-b}
  plans:
    - {from: uat-plan, to: prd-plan}
  paths:
    - {from: uat-a-to-uat-b, to: prd-a-to-prd-b}
  endpoints:
    - {from: "db.uat.example.com:5432", to: "db.prd.example.com:5432"}
```

| Field               | Description                                                                      |
|---------------------|----------------------------------------------------------------------------------|
| `spec.blueprint`    | Name of the DRBlueprint in the same namespace                                    |
| `spec.version`      | Pins a blueprint version. `0` (default) follows the blueprint                    |
| `spec.site`         | Managed cluster the blueprint is matched in                                      |
| `spec.namespaces[]` | Namespace rules. One `*` in `from` matches any part and is substituted into `to` |
| `spec.sites[]`      | Translates plan site names                                                       |
| `spec.plans[]`      | Translates ProtectionPlan names                                                  |
| `spec.paths[]`      | Translates DRPath names                                                          |
| `spec.networks[]`   | Renames a network role (`role`, `to`) where production named it differently      |
| `spec.endpoints[]`  | Translates `host` or `host:port` in probe targets and gate commands              |
| `spec.applications` | Limits the mapping to some applications. Empty maps all                          |

Names without a mapping stay as they are, so environments that use the same names need an almost empty mapping. Every
network role must exist in the SiteProfiles of the production sites, otherwise the bundle asks a blocking question. A
pinned version that differs from the blueprint's sets the condition `VersionPinned=False` and proposes nothing.

## Matching

For each member, dr-hub searches the production site's DiscoveryGraph, among objects of the same kind in the mapped
namespace. The first rule with exactly one hit decides:

| Order | Rule                                                                         | Confidence |
|-------|------------------------------------------------------------------------------|------------|
| 1     | Every identity label matches, for example, the `vmID` label of a migrated VM | 1.0        |
| 2     | Same name and workload kind, images and role agree                           | 0.9        |
| 3     | Same name, images or role differ                                             | 0.7        |
| 4     | VMs: a NIC MAC address matches                                               | 0.8        |
| 5     | Same workload kind, role, image repositories, and release                    | 0.6        |

What cannot be matched becomes a question in the bundle:

- **Missing:** No object matches. Blocking: drop the member, or deploy it and wait for the next graph rebuild.
- **Ambiguous:** Several objects match. Blocking: the question lists them.
- **Extra:** Objects in the mapped namespaces that no member claimed. Not blocking: restore them in the last tier, or
  exclude them.
- **Order:** Production shows a dependency from a member to a member of a later tier. Not blocking: keep the
  blueprint's order, or move the dependency earlier.

PVCs mounted by matched workloads and VMs join the application even without a PVC member in the blueprint.

The match result per application is in `status.applications[]` (`matched`, `missing`, `ambiguous`, `extra`, and the
bundle), and the condition `Matched` summarizes it.

## Bundles From a Blueprint

The bundles carry the source `blueprint:<blueprint>@<version>`. They hold the template with production names: the
plan, the source and target sites, the protected namespaces, the namespaces of gates, and Service names and mapped
endpoints in probe targets and gate commands. Label patches set the blueprint's DR labels on the matched objects.

When the production site also has a rules bundle for the same application, `status.baselineDiff` shows the difference
between the two, and the pull request shows it next to the diff against the live objects. Once one of them is
applied, the other one is superseded.

The dry run, the pull request, the approval, and the rollback work as for every bundle. See
[Using Discovery](using-discovery.md).

## Roles

| Role          | Permissions                                                                              |
|---------------|------------------------------------------------------------------------------------------|
| `dr-operator` | Create BlueprintExports, DRBlueprints, and EnvironmentMappings                           |
| `dr-admin`    | Everything `dr-operator` may do, and approve bundles when no GitOps target is configured |

Creating a blueprint or a mapping changes nothing on a site. Only an approved bundle does.
