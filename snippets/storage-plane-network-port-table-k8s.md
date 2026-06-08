| Service                         | Direction         | Source / Target Network | Port(s)       | Protocol(s) |
|---------------------------------|-------------------|-------------------------|---------------|-------------|
| ICMP                            | ingress           | control                 | -             | ICMP        |
| spdk-http-proxy                 | egress            | storage, control        | 5000, 5001    | TCP         |
| spdk-firewall-proxy*            | egress            | storage, control        | 50001,50002   | TCP         |
| nvmf (internal, client-target)  | ingress, egress   | storage                 | 4420-4499     | TCP         |
| FoundationDB                    | egress            | storage                 | 4500          | TCP         |
| Control plane API               | egress            | control                 | 80            | TCP         |
