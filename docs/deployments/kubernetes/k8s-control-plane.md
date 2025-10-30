---
title: "Install Simplyblock Control Plane on Kubernetes"
weight: 50000
---

```bash title="Install CLI"
pip install {{ cliname }} --upgrade
```

After installing the CLI, navigate to the Helm chart directory within the installed package:

```bash
cd /usr/local/lib/python3.9/site-packages/simplyblock_core/scripts/charts/
```

Then build the Helm dependencies and deploy the SimplyBlock control plane:

```bash
helm dependency build ./
helm upgrade --install sbcli --namespace simplyblock --create-namespace ./
```

Before running the Helm install, you can edit the ``values.yaml`` file to match your specific configuration —
for example, to set cluster parameters, storage options, or node selectors according to your environment.

{% include 'control-plane-network-port-table-k8s.md' %}

Find and exec into the admin control pod (replace the pod name if different):

```bash
kubectl -n simplyblock exec -it simplyblock-admin-control-<uuid> -- bash
```

```bash title="Install Control Plane"
{{ cliname }} cluster create --ifname=<IF_NAME> --ha-type=ha --mode=kubernetes
```

Additional parameters for the cluster create command can be found at [Cluster Deployment Options](../cluster-deployment-options.md).
