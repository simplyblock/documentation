## Transport Security

The `tls` block is copied into the `tls` blocks of `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`. TLS
requires cert-manager or OpenShift. Mutual TLS is only allowed with cert-manager, and turning TLS off requires turning
mutual TLS off with it. See [Securing the Control Plane](../../kubernetes/installation/security.md).
