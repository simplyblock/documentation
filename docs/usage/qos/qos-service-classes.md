---
title: "QoS Service Classes"
weight: 10400
---

QoS Service Classes are managing cluster QUOTAS and ensure that all volumes within a class
achieve their respective quota. It is possible to use up to seven user classes. 
In total there are eight service classes, but one class is defined for cluster-internal traffic such as 
rebalancing.

Service class 0 is the default service class, and classes 1 to 7 are optional classes.
Classes are defined when creating a cluster, not all classes must be defined. It is, for example, 
perfectly fine to use just one extra class.

Classes receive weights. The absolute number of the weight is irrelevant. It only matters how they are set
proportionally. For example, if you create one extra class and assign a weight of 100 to the default
class and a weight of 100 to the extra class, both classes will receive exactly identical QUOTAS.

If you, however, add two extra classes and add one with weight 100 and the second one with weight 200,
the second class will receive double the quota of class 1. For example, if all three classes receive IO of 
the same IOPS pattern (e.g., all predominantly receive 64K IO sizes), and the total output of the
cluster is 100,000 IOPS (at 64K), the default class and class 1 will receive 25,000 IOPS and class 2 
will receive 50,000 IOPS. If the total IOPS output of the cluster drops by 25%, so does the absolute amount
in each class, but the relative amount stays the same. 

!!! Info
    If service classes do not use their quotas, they are not "wasted" but can be consumed by other
    service classes.


```bash title="Managing QoS Service Classes with the CLI"
{{ cliname }} cluster qos add db-ultra  10000
{{ cliname }} cluster qos add db-std    5000
{{ cliname }} cluster qos add test-load 5000
{{ cliname }} cluster qos list 
{{ cliname }} cluster qos delete test-load
```
