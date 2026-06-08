| Service                         | Direction         | Source / Target Network | Port(s)                                                  | Protocol(s) |
|---------------------------------|-------------------|-------------------------|----------------------------------------------------------|-------------|
| ICMP                            | ingress           | control                 | -                                                        | ICMP        |
| spdk-http-proxy                 | egress            | storage, control        | 5000                                                     | TCP         |
| spdk-firewall-proxy<sup>1<sup>  | egress            | storage, control        | 50001-50065                                              | TCP         |
| nvmf (internal, client-target)  | ingress, egress   | storage                 | 4420-4499                                                | TCP         |
| FoundationDB                    | egress            | storage                 | 4500                                                     | TCP         |
| Control plane API               | egress            | control                 | 80                                                       | TCP         |
| Control plane RPC               | egress, ingress   | control                 | 8080-9044                                                | TCP         |
| Monitoring Stack                | ingress, egress   | monitoring              | 12202, 13301, 13302, 9200, 9090                          | TCP         |

<p style="font-size: 12px; position: relative; top: -20px;"><sup>1</sup>will depricate with 26.2.3</p>
