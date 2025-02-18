import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

(() => {
  function createPlot() {
    const plot = Plot.rectY(
      { length: 10000 },
      Plot.binX({ y: "count" }, { x: Math.random })
    ).plot();

    const div = document.querySelector("#myplot");
    div.append(plot);

    return plot;
  }

  // Execute the function immediately
  createPlot();
})();
