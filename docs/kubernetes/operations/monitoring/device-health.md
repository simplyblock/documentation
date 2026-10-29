---
title: "Device Health"
description: "Slow-device detection and SMART health checks of the Simplyblock Operator, recorded on each StorageDevice and reported as alerts."
weight: 10625
---

A storage device rarely fails all at once. A drive that wears out, or whose host storage degrades, usually keeps
answering I/O for a long time before it stops, so the control plane never marks it unavailable. In the meantime, it
slows down the whole cluster: every write is mirrored or erasure-coded across devices, and a write completes only when
its slowest copy does. One slow device therefore sets the latency of every volume striped across it.

The Simplyblock Operator watches for both signs. It compares the performance of each device with the other devices of
its cluster, and it reads the SMART health log of each device on a schedule and on request. Both results are recorded
on the `StorageDevice`, emitted as Kubernetes events and Prometheus metrics, and reported to the control plane. The
control plane then raises them as alerts, next to every other alert of the cluster.

## Performance Monitoring

Once a minute, the operator compares every storage device with the other devices of its fleet, using the I/O counters
that the control plane exports to Prometheus. The fleet of a device is the set of serving devices (phase `Online` or
`Degraded`) of the same cluster and the same role. Journal devices are compared only with other journal devices,
because they carry the journal's small sequential writes, not data stripes.

Each comparison covers the past ten minutes:

- **IOPS** is the rate of read and write operations.
- **Latency** is the mean time per operation.
- **Weight** is the device's capacity, because capacity is what the cluster places data by. The **share** of a device
  is the part of the fleet's IOPS that its weight entitles it to.
- **Fleet latency** is the median latency of the fleet's I/O, weighted by IOPS. A median keeps the device being
  assessed from pulling the reference toward itself.

| Condition                                                                                       | Verdict   |
|-------------------------------------------------------------------------------------------------|-----------|
| The device serves fewer than 5 IOPS, or its fleet has fewer than 3 devices that serve 5 or more | `Unknown` |
| The device serves at least twice its share                                                      | `Ok`      |
| Its latency is at least 3 times the fleet latency and at least 2 ms above it                    | `Slow`    |
| It serves at most half its share at 1.5 times the fleet latency or more, and at least 2 ms more | `Slow`    |
| None of the above                                                                               | `Ok`      |

The comparison is relative to the load, so heavy load alone does not make a device slow. A node that returns after an
outage receives the writes it missed, and its devices queue them. They then carry more than their share, and their
latency is caused by that load, not by the hardware, so a rebuild raises no alert. A device that is saturated, in
contrast, serves less than its share while it is slower, and is reported. A device that serves less than its share at
normal latency is usually one that data has not been rebalanced onto yet, and is `Ok`.

A verdict changes only after it is confirmed: three assessments in a row must find a device slow before it is reported
`Slow`, and five must find it fine before it returns to `Ok`. An `Unknown` assessment changes neither the verdict nor
the count. The verdict survives a restart of the operator.

The performance check needs the Prometheus of the control plane, which the operator reads at the address set in the
Helm value `metricsAPI.prometheusURL`. Without it, only the SMART check runs.

## SMART Health Checks

The operator reads the health log of every device every six hours, oldest first, and at most ten devices per pass, so a
large fleet is read over several minutes instead of in one burst. The control plane performs the read:

- An NVMe device attached to SPDK is read through SPDK.
- A Linux block device (see [Linux Block Devices](../../../architecture/concepts/linux-block-devices.md)) is read by
  the storage node agent, with `nvme smart-log` for an NVMe namespace and with `smartctl` for any other device.
- A device without a health log, such as a virtual disk, reports `Unsupported`.

| Health log                                                                                                         | Verdict       |
|--------------------------------------------------------------------------------------------------------------------|---------------|
| NVMe critical warning: spare capacity, reliability degraded, read-only mode, volatile backup, or persistent memory | `Failing`     |
| Available spare at or below the threshold of the device                                                            | `Failing`     |
| SATA or SAS self-assessment failed                                                                                 | `Failing`     |
| NVMe critical warning: temperature                                                                                 | `Warning`     |
| At least 90% of the rated life used, media errors, reallocated sectors, or pending sectors                         | `Warning`     |
| None of the above, with at least one reading reported                                                              | `Ok`          |
| No reading that can be judged                                                                                      | `Unknown`     |
| No health log available                                                                                            | `Unsupported` |

Only what the device itself declares about its own reliability makes it `Failing`. Wear, temperature, and error
counts that a drive keeps working through are warnings.

A read that fails, for example, because the control plane cannot reach the node, keeps the previous verdict, records
the failure in the reason, and is retried after fifteen minutes. An unreachable node says nothing about the drive, so
a `Failing` verdict is not cleared because of it.

!!! note
    On Linux block devices, SATA and SAS drives are read with `smartctl`. On a storage node without `smartctl`, these
    drives report `Unsupported`. NVMe namespaces are read with `nvme smart-log`.

## Reading Device Health

The verdicts appear as the `Performance` and `SMART` columns of the `StorageDevice` list:

```bash title="Listing the health of every device"
kubectl get storagedevices -n simplyblock
```

```plain title="Example output"
NAME                                       PHASE    PERFORMANCE   SMART     ...
simplyblock-cluster-worker-1-0-5e0000a1    Online   Ok            Ok
simplyblock-cluster-worker-2-0-7c11d2f0    Online   Slow          Ok
simplyblock-cluster-worker-3-0-a03b9e44    Online   Ok            Warning
```

The details are held in `status.health`:

```bash title="Reading the health of one device"
kubectl get storagedevice simplyblock-cluster-worker-2-0-7c11d2f0 -n simplyblock \
    -o jsonpath='{.status.health}' | jq
```

| Field                                              | Description                                                             |
|----------------------------------------------------|-------------------------------------------------------------------------|
| `performance.verdict`                              | `Ok`, `Slow`, or `Unknown`.                                             |
| `performance.reason`                               | Why the device has the verdict, in words.                               |
| `performance.since`                                | When the verdict last changed.                                          |
| `performance.assessedAt`                           | When the device was last assessed.                                      |
| `performance.latencyMicroseconds`                  | The mean latency of the device.                                         |
| `performance.fleetLatencyMicroseconds`             | The fleet latency it was compared with.                                 |
| `performance.latencyRatioPercent`                  | The latency of the device as a percentage of the fleet latency.         |
| `performance.iopsRatioPercent`                     | The IOPS of the device as a percentage of its share.                    |
| `smart.verdict`                                    | `Ok`, `Warning`, `Failing`, `Unsupported`, or `Unknown`.                |
| `smart.reason`                                     | Why the device has the verdict, in words.                               |
| `smart.checkedAt`                                  | When the health log was last read.                                      |
| `smart.source`                                     | What read the health log: `spdk`, `nvme-cli`, or `smartctl`.            |
| `smart.criticalWarning`                            | The NVMe critical warning bits.                                         |
| `smart.temperatureCelsius`                         | The temperature of the device.                                          |
| `smart.availableSparePercent`                      | The remaining spare capacity of an NVMe device.                         |
| `smart.availableSpareThresholdPercent`             | The spare capacity below which the NVMe device declares itself failing. |
| `smart.percentageUsed`                             | The estimated part of the rated life used.                              |
| `smart.mediaErrors`                                | The number of unrecovered data integrity errors.                        |
| `smart.powerOnHours`, `smart.unsafeShutdowns`      | The power-on hours and the number of unsafe shutdowns.                  |
| `smart.smartPassed`                                | The result of the self-assessment of a SATA or SAS drive.               |
| `smart.reallocatedSectors`, `smart.pendingSectors` | The remapped and pending sectors of a SATA or SAS drive.                |

The status is written when a verdict changes, and otherwise at most every fifteen minutes. The Prometheus metrics
below carry the readings at full resolution.

## Checking a Device on Demand

A `StorageDeviceOps` with the action `CheckHealth` reads the health log of one device immediately, instead of at the
next scheduled read. It is the way to confirm a suspicion, or to check a replacement drive, without waiting for the
schedule.

```yaml title="Example of an on-demand health check (check-device.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageDeviceOps
metadata:
  name: check-device-a03b9e44
  namespace: simplyblock
spec:
  deviceRef: simplyblock-cluster-worker-3-0-a03b9e44
  action: CheckHealth
```

```bash title="Running the check and reading its result"
kubectl apply -f check-device.yaml
kubectl get storagedeviceops check-device-a03b9e44 -n simplyblock \
    -o jsonpath='{.status.phase}{"\t"}{.status.message}{"\n"}'
```

The operation has a single step, `Requesting`. It changes nothing on the device and can be aborted at any time. Its
result is recorded, published, and reported exactly as a scheduled read is, and the message of the succeeded operation
states the verdict. If the health log cannot be read, the operation fails with the reason.

## Centralized Reporting

The operator reports the verdicts of every serving device to the control plane. A report is sent when a verdict
changes, and repeated every five minutes while it does not. The control plane stores the latest report on the device,
where it is returned with the device by the API, and turns it into alerts:

| Alert kind         | Severity                                      | Fires while                                    |
|--------------------|-----------------------------------------------|------------------------------------------------|
| `device_slow`      | warning                                       | The performance verdict of the device is slow. |
| `device_unhealthy` | critical for `Failing`, warning for `Warning` | The SMART verdict is failing or warning.       |

These alerts are raised and resolved like every other alert of the cluster, through the
[Alerts Endpoint](../../../reference/api/alerts.md). They stay quiet while the node of the device is not online, while
the device is not serving (it already raises `device_unavailable`), and for a device that was removed on purpose.

Each report is valid for fifteen minutes. If the operator stops reporting, the alerts resolve once the last report
expires, instead of firing forever on stale information.

## Events and Metrics

The operator records each change of a verdict as an event on the `StorageDevice`:

| Event                        | Type      | Recorded when                              |
|------------------------------|-----------|--------------------------------------------|
| `DeviceSlow`                 | `Warning` | The device became slow.                    |
| `DevicePerformanceRecovered` | `Normal`  | The device is no longer slow.              |
| `DeviceSMARTWarning`         | `Warning` | The health log raised a warning.           |
| `DeviceSMARTFailing`         | `Warning` | The health log reports the device failing. |
| `DeviceSMARTRecovered`       | `Normal`  | The health log no longer raises a concern. |
| `DeviceHealthCheckFailed`    | `Warning` | The health log could not be read.          |

```bash title="Listing the health events of the storage devices"
kubectl get events -n simplyblock --field-selector involvedObject.kind=StorageDevice
```

It also exports the verdicts and readings as Prometheus metrics, with the labels `cluster`, `node`, and `device`:

| Metric                                        | Description                                                           |
|-----------------------------------------------|-----------------------------------------------------------------------|
| `simplyblock_storagedevice_performance_state` | 1 for the current performance verdict (label `verdict`), 0 otherwise. |
| `simplyblock_storagedevice_smart_state`       | 1 for the current SMART verdict (label `verdict`), 0 otherwise.       |
| `simplyblock_storagedevice_latency_ratio`     | The latency of the device over the fleet latency.                     |
| `simplyblock_storagedevice_iops_share_ratio`  | The IOPS of the device over its share.                                |

A Prometheus Alertmanager that already watches the Kubernetes cluster can alert on the metrics directly:

```yaml title="Example of Prometheus alert rules for device health"
groups:
  - name: simplyblock-device-health
    rules:
      - alert: SimplyblockDeviceSlow
        expr: simplyblock_storagedevice_performance_state{verdict="Slow"} == 1
        labels:
          severity: warning
        annotations:
          summary: "A simplyblock storage device is slow"
      - alert: SimplyblockDeviceFailing
        expr: simplyblock_storagedevice_smart_state{verdict="Failing"} == 1
        labels:
          severity: critical
        annotations:
          summary: "A simplyblock storage device reports failing SMART health"
```

## Acting on a Verdict

The operator reports a slow or failing device and leaves the decision to an administrator. It does not restart or
fail a device by itself, because a measurement is not a decision: a device can be slow because of its host, and a
restart of the device is the first thing to try.

- A **slow** device is first restarted, as described in
  [Restarting a Storage Device](../storage-nodes/storage-node-actions.md#restarting-a-storage-device). A device that
  stays slow afterward, or a device whose host storage cannot be fixed, is failed.
- A **failing** device is failed and replaced. The control plane then rebuilds its data onto the remaining devices, as
  described in [Failing a Storage Device](../storage-nodes/storage-node-actions.md#failing-a-storage-device).
- A **warning** is a reason to plan a replacement and to watch the device more closely, for example, with an on-demand
  check.

## Configuration

The checks are enabled by default. They are controlled by these arguments of the operator:

| Argument                   | Default | Description                                           |
|----------------------------|---------|-------------------------------------------------------|
| `--enable-device-health`   | `true`  | Runs the checks and accepts the `CheckHealth` action. |
| `--device-health-interval` | `1m`    | How often the performance of the fleet is assessed.   |
| `--device-health-window`   | `10m`   | The period each performance assessment averages over. |
| `--device-smart-interval`  | `6h`    | How often the health log of each device is read.      |

The thresholds of the performance comparison are fixed and apply to every cluster managed by the operator.
