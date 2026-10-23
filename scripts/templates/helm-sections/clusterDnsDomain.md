## Cluster Domain

The DNS domain of the Kubernetes cluster. Every in-cluster address and certificate name the chart and the operator
build, and the FoundationDB cluster file, use it. It only needs to be changed on a cluster set up with a domain other
than `cluster.local`.
