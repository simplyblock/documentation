---
title: "Install Simplyblock Control Plane on Kubernetes"
weight: 50000
---

Deployment of the control plane into a Kubernetes cluster requires an administrative host or container
based on Rocky, RHEL or Alma Linux Version 9. It is necessary to install the {{ cliname }} 
to this container and open necessary ports:

```plain title="install cli"
pip install sbctl --upgrade
```

{% include 'control-plane-network-port-table.md' %}

```plain title="install control plane"
{{ cliname }} cluster create --ifname=<IF_NAME> --ha-type=ha --mode=kubernetes
```

Additional parameters for the cluster create command can be found [here](../install-on-linux/install-sp.md)
