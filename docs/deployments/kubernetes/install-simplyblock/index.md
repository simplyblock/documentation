---
title: "Install Simplyblock"
weight: 30140
---

Simplyblock is a highly flexible solution when it comes to Kubernetes related deployment strategies. Each of the
deployment methods have their own pros and cons. 


<div class="grid cards" markdown>

-   :material-kubernetes:{ .lg .middle } __Hyper-Converged__

    ---

    <p>A hyper-converged storage cluster provides the best resource usage by combining storage and compute into shared
    hardware. Running hyper-converged enables data affinity (data locality) for ultra-low latency.</p><p>
    [:octicons-arrow-right-24: Learn about Hyper-Converged](../../../architecture/concepts/hyper-converged.md)<br/>
    [:octicons-arrow-right-24: Hyper-Converged Installation](hyper-converged.md)</p>

-   :material-kubernetes:{ .lg .middle } __Disaggregated__

    ---

    <p>A disaggregated storage cluster provides the best independent scalability between storage and compute. Running a
    separate storage cluster enables resource efficiency and simplified management.</p><p>
    [:octicons-arrow-right-24: Learn about Disaggregated](../../../architecture/concepts/disaggregated.md)<br/>
    [:octicons-arrow-right-24: Disaggregated Installation](disaggregated.md)</p>

-   :material-kubernetes:{ .lg .middle } __Hybrid__

    ---

    <p>A hybrid storage cluster combines the best of both worlds. Using a disaggregated storage cluster for infinite
    scalability and joining it with a hyper-converged part for lowest latency and highest throughput workloads.</p><p>
    [:octicons-arrow-right-24: Hybrid Installation](hybrid.md)</p>
</div>


