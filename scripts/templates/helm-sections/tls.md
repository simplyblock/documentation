## Transport Security

The `tls` block is copied into the `tls` blocks of `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`. TLS
requires cert-manager or OpenShift. Mutual TLS is only allowed with cert-manager, so both the `openshift` provider and
turning TLS off require `tls.mutual_enabled: false`. See
[Securing the Control Plane](../../kubernetes/installation/security.md).
