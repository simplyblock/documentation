| Service                         | Direction         | Hosts   | Network | Port(s)                          | Protocol(s) |
|---------------------------------|-------------------|---------|---------|----------------------------------|-------------|
| ICMP                            | ingress           | control | Control | -                                | ICMP        |
| spdk-http-proxy                 | egress            | control | Control | 5000                             | TCP         |
| spdk-http-proxy                 | ingress           | storage | Control | 5000                             | TCP         |
| spdk-firewall-proxy<sup>1</sup> | egress            | control | Control | 50001-50065                      | TCP         |
| spdk-firewall-proxy<sup>1</sup> | ingress           | storage | Control | 50001-50065                      | TCP         |
| nvmf (client-target)            | egress            | client  | Storage | 4420-4499                        | TCP         |
| nvmf (internal)                 | ingress, egress   | storage | Storage | 4420-4499                        | TCP         |
| FoundationDB                    | ingress           | control | Control | 4500                             | TCP         |
| Control plane API               | egress            | control | Control | 80                               | TCP         |
| Control plane RPC               | egress            | control | Control | 8080-9044                        | TCP         |
| Control plane RPC               | ingress           | storage | Control | 8080-9044                        | TCP         |
| Monitoring Stack                | ingress, egress   | control | Control | 12202, 13301, 13302, 9200, 9090  | TCP         |

<p style="font-size: 12px; position: relative; top: -20px;"><sup>1</sup>Deprecated since 26.2.3</p>
