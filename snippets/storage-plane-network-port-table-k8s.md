| Service                     | Direction | Source / Target Network | Port(s)   | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control                 | -         | ICMP        |
| Storage node API            | ingress   | storage                 | 5000      | TCP         |
| spdk-firewall-proxy         | ingress   | storage                 | 5001      | TCP         |
| spdk-http-proxy             | ingress   | storage, control        | 8080-8180 | TCP         |
| hublvol-nvmf-subsys-port    | ingress   | storage, control        | 9030-9059 | TCP         |
| internal-nvmf-subsys-port   | ingress   | storage, control        | 9060-9099 | TCP         |
| lvol-nvmf-subsys-port       | ingress   | storage, control        | 9100-9200 | TCP         |
| FoundationDB                | egress    | storage                 | 4500      | TCP         |
| Control plane API           | egress    | control                 | 80        | TCP         |
