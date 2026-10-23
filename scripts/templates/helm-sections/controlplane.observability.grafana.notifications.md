## Alert Notifications

The `controlplane.observability.grafana.notifications` block provisions receivers into the `grafana-alerts` contact
point. Every enabled channel is notified for every simplyblock alert. With none enabled, no contact point and no
notification policy are provisioned. The credentials are rendered into the `simplyblock-grafana-alerting` ConfigMap, so
read access to the release namespace is read access to them.
