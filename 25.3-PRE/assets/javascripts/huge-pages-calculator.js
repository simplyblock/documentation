document.addEventListener("DOMContentLoaded", function() {
  const elNumDisks = document.getElementById("hpc-num-disks");
  const elMaxProvStorage = document.getElementById("hpc-max-prov-storage");
  const elNumLVols = document.getElementById("hpc-num-lvols");
  const elNumCPUs = document.getElementById("hpc-num-cpus");
  const elCalcResult = document.getElementById("hpc-calc-result");

  if (!elNumDisks) return;

  function calculate_huge_pages() {
    const numDisks = parseInt(elNumDisks.value);
    const maxProvStorage = parseInt(elMaxProvStorage.value);
    const numLVols = parseInt(elNumLVols.value);
    const numCPUs = parseInt(elNumCPUs.value);
    const numDistWorkers = 4;

    const baseVal1 = 8;
    const baseVal2 = 128;

    const val1 = Math.max(numCPUs, numDistWorkers + numDisks + 4);
    const val2 = val1 + 384;

    const jm = 256 * baseVal1 + 32 * baseVal2 * 3;
    const raid = 256 * baseVal1 + 32 * baseVal2 * 2;
    const alceml = 256 * baseVal1 + 32 * baseVal2 * numDisks;
    const distrib = 256 * baseVal1 + 32 * baseVal2 * numDistWorkers;
    const scm = 256 * baseVal1 + 32 * baseVal2 * 1;
    const subsys = 127 * val2 * baseVal1 + 15 * val2 * baseVal2 * 1;
    const target = 128 * val1 * baseVal1 + 16 * val1 * baseVal2 * 1;
    const crypto = 384 * baseVal1 + 48 * baseVal2 * numCPUs;
    const other_cpu = 1024 * numCPUs * 4;
    const max_prov = 250000 * maxProvStorage * 1.1;
    const lvol = 1024 * numLVols * 7;
    const sum = jm + raid + alceml + distrib + scm + subsys + target + crypto + other_cpu + max_prov + lvol;

    const huge_pages_mem = sum * 1.5;
    const huge_pages_num = Math.floor(huge_pages_mem / 2000) + (huge_pages_mem % 2000 === 0 ? 0 : 1);

    elCalcResult.innerText = huge_pages_num;
  }

  elNumDisks.addEventListener("input", function() {
    calculate_huge_pages();
  });

  elMaxProvStorage.addEventListener("input", function() {
    calculate_huge_pages();
  });

  elNumLVols.addEventListener("input", function() {
    calculate_huge_pages();
  });

  elNumCPUs.addEventListener("input", function() {
    calculate_huge_pages();
  });

  elNumDistWorkers.addEventListener("input", function() {
    calculate_huge_pages();
  });

  calculate_huge_pages();
});