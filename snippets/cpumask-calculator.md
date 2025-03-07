<div class="calculator" id="cpumask-calculator">
<div class="title">CPU Mask Calculator</div>
<div style="width: 100%; padding-top: 10px;">
    <div style="display: flex; align-items: center;">
        <label style="width: 250px;" for="cpuc-cores">Number of cores:</label>
        <input id="cpuc-cores" type="number" min="1" value="8"/>
    </div>
</div>
<div id="cpuc-cores-wrapper" style="padding-top: 10px; display: grid; grid-template-columns: repeat(4, 1fr); grid-column-gap: 10px; grid-row-gap: 10px; justify-items: center;">
</div>
<div class="result-title">Calculated CPU Mask: <span id="cpuc-result" class="result">0x00000000</span></div>
</div>
