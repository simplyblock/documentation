## Discovery

The `discovery` block configures the first discovery run, rendered for the `standalone` profile as an `OperatorOps`
with the `Discover` action. The run inspects the workers and writes a `ClusterDeploymentConfig` in `Draft`. Nothing is
deployed until the draft is approved. A finished run is not repeated on upgrade, so a changed value has no effect after
the first installation. See
[Narrowing the First Discovery Run](index.md#narrowing-the-first-discovery-run).
