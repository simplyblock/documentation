---
title: "API / Developer SDK"
weight: 20100
---

Simplyblock offers a comprehensive API to manage and automate cluster operations. This includes all cluster-wide
operations, logical volume specific operations, health information, and 

 - Retrieve information about the cluster and its health status
 - Automatically manage a logical volume lifecycle
 - Integrate simplyblock into deployment processes and workflow automations
 - Create custom alerts and warnings

## Authentication

Any request to the simplyblock API requires authorization information to be provided. Unauthorized requests
return an HTTP status 401 (Unauthorized).

To provide authorization information, the simplyblock API uses the _Authorization_ HTTP header with a
combination of the cluster uuid and the cluster secret.

HTTP Authorization header:

```plain
Authorization: <CLUSTER_UUID> <CLUSTER_SECRET>
```

The cluster id is provided during the initial cluster installation. The cluster secret can be obtained using
the simplyblock commandline interface tool `sbcli`.

```bash
sbcli cluster get-secret CLUSTER_UUID
```

## PUT/POST Requests 

For requests that send JSON payload to the backend endpoint, it is important to set the Content-Type header
accordingly. Requests that require this header to be set are of type HTTP PUT or HTTP POST.

The expected content type is `application/json`:

```plain
Content-Type: application/json
```

## API Documentation

The full API documentation is hosted on Postman. You can find the full API collection on the
[Postman API project](https://documenter.getpostman.com/view/434798/2sA3QpCtzT#intro).
