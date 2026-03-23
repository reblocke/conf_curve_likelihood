const statusCard = document.getElementById("status-card");

statusCard.dataset.state = "loading";
statusCard.textContent = "Foundation checkpoint complete. Numerical engine and plotting are loading next.";

document.getElementById("controls-toggle").addEventListener("click", () => {
  const panel = document.getElementById("controls-panel");
  const nextCollapsed = panel.dataset.collapsed !== "true";
  panel.dataset.collapsed = nextCollapsed ? "true" : "false";
  document.getElementById("controls-toggle").setAttribute("aria-expanded", String(!nextCollapsed));
});

document.getElementById("grid-points").addEventListener("input", (event) => {
  document.getElementById("grid-points-output").value = event.target.value;
});
