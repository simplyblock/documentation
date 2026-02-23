---
title: "Install Simplyblock Control Plane on Kubernetes"
weight: 30000
---

```bash title="Install CLI"
pip install {{ cliname }} --upgrade
```

After installing the CLI, navigate to the Helm chart directory within the installed package:

```bash
cd /usr/local/lib/python3.9/site-packages/simplyblock_core/scripts/charts/
```

Then build the Helm dependencies and deploy the simplyblock control plane:

```bash
helm dependency build ./
helm upgrade --install sbcli --namespace simplyblock --create-namespace ./
```

Before running the `helm install`, you can edit the `values.yaml` file to match your specific configuration.
For example, to set cluster parameters, storage options, monitoring secret or node selectors according to your environment.

{% include 'control-plane-network-port-table-k8s.md' %}

Find and exec into the admin control pod (replace the pod name if different):

```bash
kubectl -n simplyblock exec -it simplyblock-admin-control-<uuid> -- bash
```

```bash title="Install Control Plane"
{{ cliname }} cluster create --mgmt-ip <WORKER_IP> --ha-type ha --mode kubernetes
```

!!! info
    You need to add additional parameter when using a Loadbalancer `--ingress-host-source loadbalancer` and `--dns-name <LB_INGRESS_DNS>`

Additional parameters for the cluster create command can be found at [Cluster Deployment Options](../cluster-deployment-options.md).
