import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

(async () => {
  try {
    // Fetch data from the "stars" canned query.
    // We ask for the array shape to get a clean array of objects.
    const res = await fetch("/github/stars.json?_shape=array");
    if (!res.ok) {
      const errorText = await res.text();
      console.error("Failed to fetch data:", res.status, errorText);
      const div = document.querySelector("#myplot");
      div.innerHTML = `<div class="p-4 bg-red-100 text-red-800 rounded">Failed to load plot data. See console for details.</div>`;
      return;
    }
    const data = await res.json();

    // Create the plot
    const plot = Plot.plot({
      title: "Repository Stars vs. Size",
      subtitle:
        "A scatter plot of GitHub repositories, with a linear regression trend line.",
      marginLeft: 80,
      grid: true,
      x: {
        type: "log",
        label: "Repository Size (KB) →",
        labelAnchor: "right",
        transform: (d) => d + 1, // Add 1 to avoid log(0) for repos with 0 size
      },
      y: {
        type: "log",
        label: "↑ Star Count",
        labelAnchor: "top",
        transform: (d) => d + 1, // Add 1 to avoid log(0) for repos with 0 stars
      },
      marks: [
        Plot.dot(data, {
          x: "size",
          y: "stargazers_count",
          title: "full_name", // Use full_name for the tooltip
          stroke: "steelblue",
          fill: "steelblue",
          fillOpacity: 0.3,
          r: 4,
          tip: {
            format: {
              y: (d) => `${d.toLocaleString()} stars`,
              x: (d) => `${d.toLocaleString()} KB`,
              title: (d) => d,
            },
          },
        }),
        Plot.linearRegressionY(data, {
          x: "size",
          y: "stargazers_count",
          stroke: "red",
          strokeWidth: 2,
        }),
      ],
    });

    // Append the plot to the div
    const div = document.querySelector("#myplot");
    div.innerHTML = ""; // Clear previous content
    div.append(plot);
  } catch (error) {
    console.error("Error creating plot:", error);
    const div = document.querySelector("#myplot");
    div.innerHTML = `<div class="p-4 bg-red-100 text-red-800 rounded">An error occurred while rendering the plot.</div>`;
  }
})();
