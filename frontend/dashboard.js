renderNav("dashboard.html");

const COLORS = ["bg-primary", "bg-surface-tint", "bg-on-primary-fixed-variant", "bg-outline", "bg-secondary", "bg-error", "bg-tertiary", "bg-on-tertiary-container"];

function metricTile(label, value, icon, borderRight) {
  return `
    <div class="p-6 ${borderRight ? "md:border-r border-outline-variant" : ""} flex flex-col justify-between hover:bg-surface-container-low transition-colors">
      <div class="flex justify-between items-start mb-4">
        <span class="font-label-caps text-label-caps uppercase text-on-surface-variant">${label}</span>
        <span class="material-symbols-outlined text-on-surface-variant text-[18px]">${icon}</span>
      </div>
      <div class="font-data-mono text-[28px] leading-tight text-primary font-medium">${value}</div>
    </div>`;
}

async function loadDashboard() {
  try {
    const [stats, clustersResp] = await Promise.all([SignalAPI.stats(), SignalAPI.listClusters()]);

    document.getElementById("last-updated").innerHTML =
      `Live from API &middot; ${stats.total_tickets.toLocaleString()} tickets across banking77 + Twitter corpora`;

    document.getElementById("metrics-grid").innerHTML = [
      metricTile("Total Tickets", stats.total_tickets.toLocaleString(), "receipt_long", true),
      metricTile("Classifier Accuracy", (stats.classifier_accuracy * 100).toFixed(1) + "%", "task_alt", true),
      metricTile("Clusters Detected", stats.n_clusters, "bubble_chart", true),
      metricTile("Retrieval Hit Rate", stats.retrieval_hit_rate != null ? (stats.retrieval_hit_rate * 100).toFixed(0) + "%" : "—", "search", false),
    ].join("");

    const maxCount = Math.max(...stats.category_breakdown.map((c) => c.count));
    document.getElementById("category-chart").innerHTML = stats.category_breakdown
      .map(
        (c, i) => `
      <div class="flex items-center gap-3 py-1.5">
        <div class="w-48 font-data-mono text-data-mono text-on-surface text-[12px] truncate">${c.category}</div>
        <div class="flex-1 bg-surface-container-high h-4">
          <div class="${COLORS[i % COLORS.length]} h-4" style="width: ${(c.count / maxCount) * 100}%"></div>
        </div>
        <div class="w-16 text-right font-data-mono text-data-mono text-[12px] text-on-surface-variant">${c.count}</div>
      </div>`
      )
      .join("");

    document.getElementById("category-table-body").innerHTML = stats.category_breakdown
      .map(
        (c, i) => `
      <tr class="border-b border-outline-variant hover:bg-surface-container-low transition-colors">
        <td class="p-3 border-r border-outline-variant flex items-center gap-2">
          <div class="w-2 h-2 ${COLORS[i % COLORS.length]}"></div>${c.category}
        </td>
        <td class="p-3 border-r border-outline-variant">
          <div class="w-full bg-surface-container-high h-2"><div class="${COLORS[i % COLORS.length]} h-2" style="width: ${(c.count / maxCount) * 100}%"></div></div>
        </td>
        <td class="p-3 text-right">${c.count}</td>
        <td class="p-3 text-right text-secondary">${c.pct}%</td>
      </tr>`
      )
      .join("");

    const topClusters = [...clustersResp.clusters].sort((a, b) => b.size - a.size).slice(0, 3);
    const flagColors = ["border-l-error text-error", "border-l-surface-tint text-surface-tint", "border-l-outline text-outline"];
    document.getElementById("flagged-clusters").innerHTML = topClusters
      .map(
        (c, i) => `
      <a href="clusters.html?cluster=${c.cluster_id}" class="block hairline-border bg-surface-container-lowest p-5 border-l-4 ${flagColors[i]} hover:bg-surface-container-low transition-colors">
        <div class="flex justify-between items-start mb-3">
          <div class="font-data-mono text-data-mono font-medium uppercase tracking-wide ${flagColors[i].split(" ")[1]}">Cluster #${c.cluster_id}</div>
          <span class="material-symbols-outlined text-outline-variant text-[16px]">open_in_new</span>
        </div>
        <h4 class="font-headline-sm text-body-lg font-semibold text-on-surface mb-4">${c.label}</h4>
        <div class="grid grid-cols-2 gap-4 border-t border-outline-variant pt-3">
          <div>
            <div class="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Volume</div>
            <div class="font-data-mono text-data-mono text-on-surface">${c.size} tickets</div>
          </div>
          <div>
            <div class="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Top Terms</div>
            <div class="font-data-mono text-data-mono text-on-surface text-[11px]">${c.top_terms.slice(0, 3).join(", ")}</div>
          </div>
        </div>
      </a>`
      )
      .join("");
  } catch (err) {
    document.getElementById("last-updated").textContent = `Could not load data from API: ${err.message}`;
    console.error(err);
  }
}

loadDashboard();
