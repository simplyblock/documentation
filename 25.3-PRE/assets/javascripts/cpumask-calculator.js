document.addEventListener("DOMContentLoaded", function() {
    const elNumCores = document.getElementById("cpuc-cores");
    const elCoresWrapper = document.getElementById("cpuc-cores-wrapper");
    const elResult = document.getElementById("cpuc-result");
    if (!elNumCores) return;

    function clear_cpu_cores_wrapper() {
        elCoresWrapper.innerHtml = '';
    }

    function calculate_cpu_mask() {
        const numCores = elNumCores.value;
        const cores = [...elCoresWrapper.querySelectorAll("input[type=checkbox]")].map(checkbox => {
            return checkbox.checked ? 1 : 0
        });

        let cpumask = 0;
        for (let i = 0; i < cores.length; i++) {
            if (cores[i] === 0) continue;
            cpumask |= cores[i] << i;
        }
        const hex = long2hex(cpumask);
        elResult.innerText = `0x${hex.toUpperCase()}`;
    }

    function pad0(num, width) {
        let zeros;
        for (let i = 0; i < width; i++) {
            zeros += "0";
        }
        return (zeros + num).substr(-width);
    }

    function long2hex(num) {
        return (pad0((num >>> 24).toString(16), 2) +
            pad0((num >> 16 & 255).toString(16), 2) +
            pad0((num >> 8 & 255).toString(16), 2) +
            pad0((num & 255).toString(16), 2));
    }

    function render_checkboxes() {
        const value = parseInt(elNumCores.value);
        if (value < 0) value = 0;
        if (value > 64) value = 64;

        clear_cpu_cores_wrapper();

        const elements = [];
        for (let i = 0; i < value; i++) {
            const disabled = i === 0 ? "disabled" : "";
            elements.push(`<div style="display: flex; align-items: center;"><input ${disabled} type="checkbox" id="core-${i}" style="width: 30px;"/><label for="core-${i}">Core ${i}</label></div>`);
        }

        elCoresWrapper.innerHTML = elements.join("");
        elCoresWrapper.querySelectorAll("input[type=checkbox]").forEach(element => {
            element.addEventListener("click", function() {
                calculate_cpu_mask();
            });
        });
    }

    elNumCores.addEventListener("input", render_checkboxes);

    render_checkboxes();
});