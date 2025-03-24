---
title: "DataDog"
weight: 40000
---

Simplyblock uses Prometheus to collect storage and cluster metrics. Hence, it can easily be integrated with
external monitoring and observability solutions.

DataDog provides an extensive documentation on how to access Prometheus instances in the
[documentation](https://docs.datadoghq.com/integrations/prometheus/){:target="_blank" rel="noopener"}.

On Kubernetes-based deployments, the Prometheus (OpenMetrics) data can be collected by the DataDog agent
directly. The necessary configuration is available from their
[documentation](https://docs.datadoghq.com/containers/kubernetes/prometheus/?tab=kubernetesadv2){:target="_blank" rel="noopener"}.
