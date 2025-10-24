The following options can be set when creating a cluster. This applies to both plain linux and kubernetes deployments.
Most cannot be changed later on, so careful planning is recommended.

### ```--enable-node-affinity```

As long as a node is not full (out of capacity), the first chunk 
of data is always stored on the local node (the node to which the volume is attached). 
This reduces network traffic and latency - accelerating particularly the read - but may lead to an
inequal distribution of capacity within the cluster. Generally, using node affinity accelerates
reads, but leads to higher variability in performance across nodes in the cluster.
It is recommended on shared networks and networks below 100gb/s. 

### ```--data-chunks-per-stripe, --parity-chunks-per-stripe```

Those two parameters together make up the default erasure coding schema of the node (e.g. 1+1, 2+2, 4+2). Starting from R25.10, it is also
possible to set individual schemas per volume, but this feature is still in alpha-stage.

### ```--cap-warn, --cap-crit```

Warning and critical limits for overall cluster utilization. The warning 
limit will just cause issuance of warnings in the event log if exceeded, the "critical" limit will 
place the cluster into read-only mode. For large clusters, 99% of "critical" limit is ok, for small
clusters (less than 50TB) better use 97%. 

### ```--prov-cap-warn, --prov-cap-crit```

Warning and critical limits for over-provisioning. Exceeding
these limits will cause entries in the cluster log. If the critical limit is exceeded, 
new volumes cannot be provisioned and volumes cannot be enlarged. A limit of 500% is typical.

### ```--log-del-interval```

Number of days by which logs are retained. Log storage can grow significantly and it is recommended to keep logs for not longer than one week.

### ```--metrics-retention-period```

Number of days by which the io statistics and other metrics are retained. The amount of data per day is significant, typically limit to a few days or a week.

### ```--contact-point```

This is a webhook endpoint for alerting (critical events such as storage nodes becoming unreachable)

### ```--fabric```

Choose tcp, rdma or both. If both fabrics are chosen, volumes can connect to the cluster
using both options (defined per volume or storage class), but the cluster internally uses rdma.

### ```--qpair-count```

The default amount of queue pairs (sockets) per volume for an initiator (host) to connect to the 
target (server). More queue pairs per volume increase concurrency and volume performance, but require more
server resources (ram, cpu) and thus limit the total amount of volumes per storage node. The default is 3. 
If you need few, very performant volumes, increase the amount, if you need a large amount of less performant 
volumes decrease it. More than 12 parallel connections have limited impact on overall performance. Also, the 
host requires at least one core per queue pair.

### ```--name```

A human-readable name for the cluster