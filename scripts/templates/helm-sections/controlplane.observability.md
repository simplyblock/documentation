## Observability

The `controlplane.observability` block installs the optional logging, metrics, and dashboard stack: Graylog, Grafana,
Thanos, Fluent Bit, and the MongoDB and OpenSearch subcharts. It is intended for the `standalone` profile. See
[Observability and Alert Notifications](index.md#observability-and-alert-notifications).

!!! warning
    The observability stack ships with default passwords. They must be overridden in production.
