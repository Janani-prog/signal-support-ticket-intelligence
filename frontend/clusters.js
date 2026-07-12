renderNav("clusters.html");

const SVG_NS = "http://www.w3.org/2000/svg";
let allClusters = [];
let selectedId = null;

function normalizeAndDraw(clusters) {
  const svg = document.getElementById("cluster-svg");
  svg.innerHTML = "";

  const padding = 60;
  const rect = svg.getBoundingClientRect();
  const width = rect.width || 900;
  const height = rect.height || 700;

  const xs = clusters.map((c) => c.centroid.x);
  const ys = clusters.map((c) => c.centroid.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const sizeMax = Math.max(...clusters.map((c) => c.size));

  const scaleX = (x) => padding + ((x - xMin) / (xMax - xMin || 1)) * (width - 2 * padding);
  const scaleY = (y) => padding + ((y - yMin) / (yMax - yMin || 1)) * (height - 2 * padding);
  const scaleR = (size) => 6 + Math.sqrt(size / sizeMax) * 34;

  clusters.forEach((c) => {
    const cx = scaleX(c.centroid.x);
    const cy = scaleY(c.centroid.y);
    const r = scaleR(c.size);

    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", cx);
    circle.setAttribute("cy", cy);
    circle.setAttribute("r", r);
    circle.setAttribute("class", "cluster-dot");
    circle.setAttribute("fill", c.cluster_id === selectedId ? "#001736" : "#e5e2e1");
    circle.setAttribute("stroke", c.cluster_id === selectedId ? "#001736" : "#c4c6d0");
    circle.setAttribute("stroke-width", c.cluster_id === selectedId ? "2" : "1");
    circle.addEventListener("click", () => selectCluster(c.cluster_id));
    svg.appendChild(circle);

    if (r > 16) {
      const text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", cx);
      text.setAttribute("y", cy + 4);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-family", "JetBrains Mono");
      text.setAttribute("font-size", "11");
      text.setAttribute("fill", c.cluster_id === selectedId ? "#ffffff" : "#43474f");
      text.setAttribute("pointer-events", "none");
      text.textContent = c.size;
      svg.appendChild(text);
    }
  });
}

async function selectCluster(clusterId) {
  selectedId = clusterId;
  normalizeAndDraw(allClusters);

  const inspectorBody = document.getElementById("inspector-body");
  inspectorBody.innerHTML = '<p class="font-data-mono text-data-mono text-on-surface-variant">Loading&hellip;</p>';

  try {
    const detail = await SignalAPI.getCluster(clusterId);
    const rank = [...allClusters].sort((a, b) => b.size - a.size).findIndex((c) => c.cluster_id === clusterId) + 1;

    inspectorBody.innerHTML = `
      <div class="font-data-mono text-data-mono text-primary uppercase tracking-wide mb-1">Cluster #${detail.cluster_id}</div>
      <h3 class="font-headline-sm text-headline-sm text-on-surface mb-4">${detail.label}</h3>
      <div class="grid grid-cols-2 gap-4 border-t border-b border-outline-variant py-3 mb-6">
        <div>
          <div class="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Volume</div>
          <div class="font-data-mono text-data-mono text-on-surface">${detail.size} tickets</div>
        </div>
        <div>
          <div class="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Rank by Size</div>
          <div class="font-data-mono text-data-mono text-on-surface">#${rank} of ${allClusters.length}</div>
        </div>
      </div>
      <div class="mb-6">
        <div class="font-label-caps text-label-caps text-on-surface-variant mb-2">Top Terms</div>
        <div class="flex flex-wrap gap-2">
          ${detail.top_terms.map((t) => `<span class="px-2 py-0.5 border border-outline-variant bg-surface-container-low text-on-surface font-data-mono text-data-mono text-[11px]">${t}</span>`).join("")}
        </div>
      </div>
      <div>
        <div class="font-label-caps text-label-caps text-on-surface-variant mb-2">Sample Tickets</div>
        <div class="flex flex-col divide-y divide-outline-variant border-t border-outline-variant">
          ${detail.sample_tickets
            .map(
              (t) => `
            <div class="py-3">
              <div class="font-data-mono text-data-mono text-[11px] text-on-surface-variant mb-1">${t.ticket_id}</div>
              <div class="font-body-sm text-body-sm text-on-surface">"${t.ticket_text}"</div>
            </div>`
            )
            .join("")}
        </div>
      </div>
    `;
  } catch (err) {
    inspectorBody.innerHTML = `<p class="font-body-sm text-body-sm text-error">Failed to load cluster: ${err.message}</p>`;
  }
}

async function loadClusters() {
  try {
    const resp = await SignalAPI.listClusters();
    allClusters = resp.clusters;
    document.getElementById("cluster-count-label").textContent =
      `${resp.n_clusters} clusters detected · silhouette ${resp.silhouette_score?.toFixed(2) ?? "n/a"}`;
    normalizeAndDraw(allClusters);

    const params = new URLSearchParams(window.location.search);
    const preselect = params.get("cluster");
    if (preselect !== null) {
      selectCluster(parseInt(preselect, 10));
    }
  } catch (err) {
    document.getElementById("cluster-count-label").textContent = `Failed to load: ${err.message}`;
  }
}

window.addEventListener("resize", () => normalizeAndDraw(allClusters));
loadClusters();
