<div class="calculator" id="huge-pages-calculator">
<div class="title">Huge Pages Calculator</div>
<div class="table">
    <div class="row">
        <label class="column" for="hpc-num-disks">Number of disks:</label>
        <input class="column" id="hpc-num-disks" type="number" min="1" value="1"/>
    </div>
    <div class="row">
        <label class="column" for="hpc-max-prov-storage">Max provisioned storage (TB):</label>
        <input class="column" id="hpc-max-prov-storage" type="number" min="10" value="10"/>
    </div>
    <div class="row">
        <label class="column" for="hpc-num-lvols">Number of logical volumes:</label>
        <input class="column" id="hpc-num-lvols" type="number" min="1" value="1000"/>
    </div>
    <div class="row">
        <label class="column" for="hpc-num-cpus">Number of CPUs:</label>
        <input class="column" id="hpc-num-cpus" type="number" min="1" value="100"/>
    </div>
    <div class="row">
        <label class="column" for="hpc-num-dist-workers">Number of distributed worker threads:</label>
        <input class="column" id="hpc-num-dist-workers" type="number" min="1" value="2"/>
    </div>
</div>
<div class="result-title">Minimum required huge pages: <span id="hpc-calc-result" class="result">3436</span></div>
</div>
