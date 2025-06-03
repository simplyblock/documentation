---
title: "Control Plane"
weight: 30100
---

## FoundationDB Error

**Symptom:** FoundationDB error. All services that rely upon the FoundationDB key-value storage are offline or refuse to start.

1. Ensure that IPv6 is disabled. [To disable IPv6 follow these steps](../../deployments/baremetal/prerequisites.md#network-configuration).
2. Ensure sufficient disk space on the root partition on all control plane nodes. Free disk space can be checked with `df -h`.
   1. If not enough free disk space is available, start by checking the Graylog, MongoDB, and Elasticsearch containers. If those consume most of the disk space, old indices (2-3) can be deleted.
   2. Increase the root partition size.
   3. If you cannot increase the root partition size, remove any data or service not relevant to the simplyblock control plane and run a `docker system prune`.
3. Restart the Docker daemon: `systemctl restart docker`
4. Reboot the node

## Graylog Service Is Unresponsive

**Symptom:** The Graylog service cannot be reached anymore or is unresponsive.

1. Ensure enough free available memory
2. If short on available memory, stop services non-relevant to the simplyblock control plane.
3. If that doesn't help, reboot the host.

## Graylog Storage is Full 
**Symptom:** The Graylog service cannot start or is unresponsive, and the storage disk is full.

1. Identify the cause of the disk running full. Run the following commands to find the largest files on the Graylog disk.
   ```bash title="Find the largest files"
   df -h
   du -sh /var/lib/docker
   du -sh /var/lib/docker/containers
   du -sh /var/lib/docker/volumes
   ```
2. Delete the old Graylog indices via the Graylog UI.
       * Go to _System_ -> _Indices_
       * Select your index set
       * Adjust the _Max Number of Indices_ to a lower number
3. Reduce Docker disk usage by removing unused Docker volumes and images, as well as old containers.
   ```bash title="Remove old Docker entities"
   docker volume prune -f
   docker image prune -f
   docker rm $(sudo docker ps -aq --filter "status=exited")
   ```
4. Cleanup OpenSearch, Graylog, and MongoDB volume paths and restart the services.
   ```bash title="Cleaning up adjacent services"
   # Scale services down
   docker service update monitoring_graylog --replicas=0
   docker service update monitoring_opensearch --replicas=0
   docker service update monitoring_mongodb --replicas=0
   
   # Remove old data
   rm -rf /var/lib/docker/volumes/monitoring_graylog_data
   rm -rf /var/lib/docker/volumes/monitoring_os_data
   rm -rf /var/lib/docker/volumes/monitoring_mongodb_data
   
   # Restart services
   docker service update monitoring_mongodb --replicas=1
   docker service update monitoring_opensearch --replicas=1
   docker service update monitoring_graylog --replicas=1
   ```
