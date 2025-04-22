<div class="calculator" id="cpumask-calculator">
<div class="title">CPU Mask Calculator</div>
<div style="width: 100%; padding-top: 10px;">
    <div style="display: flex; align-items: center;">
        <label style="width: 350px;" for="cpuc-cores">Number of virtual cores<sup>*</sup>:</label>
        <input id="cpuc-cores" type="number" min="1" value="16"/>
    </div>
</div>
<div id="cpuc-cores-wrapper" style="padding-top: 10px; display: grid; grid-template-columns: repeat(4, 1fr); grid-column-gap: 10px; grid-row-gap: 10px; justify-items: center;">
</div>
<div class="result-title">Calculated CPU Mask: <span id="cpuc-result" class="result">0x0000</span></div>
</div>
<span style="font-size: small">* Virtual cores include physical and hyper-treading cores.</span>
