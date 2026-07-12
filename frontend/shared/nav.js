// Shared sidebar + top app bar, injected into any page with <div id="app-nav"></div> and
// <div id="app-topbar"></div>. Avoids duplicating the same markup across 4 static HTML files.

const NAV_ITEMS = [
  { href: "dashboard.html", icon: "dashboard", label: "Dashboard" },
  { href: "classifier.html", icon: "category", label: "Classifier" },
  { href: "clusters.html", icon: "bubble_chart", label: "Clusters" },
  { href: "ask.html", icon: "contact_support", label: "Ask" },
];

function renderNav(activeHref) {
  const navEl = document.getElementById("app-nav");
  if (navEl) {
    navEl.innerHTML = `
      <div class="px-6 mb-8">
        <h1 class="font-headline-sm text-headline-sm font-bold text-on-surface">Signal</h1>
        <p class="font-data-mono text-data-mono text-on-surface-variant mt-1">Support Ticket Intelligence</p>
      </div>
      <div class="flex-1 overflow-y-auto">
        <ul class="space-y-1">
          ${NAV_ITEMS.map(
            (item) => `
            <li>
              <a href="${item.href}" class="flex items-center gap-3 px-4 py-2 font-label-caps text-label-caps uppercase transition-colors duration-150 ${
                item.href === activeHref
                  ? "text-primary border-r-2 border-primary bg-secondary-container/30"
                  : "text-on-surface-variant hover:bg-surface-container-high"
              }">
                <span class="material-symbols-outlined text-[18px]">${item.icon}</span>
                ${item.label}
              </a>
            </li>`
          ).join("")}
        </ul>
      </div>
      <div class="mt-auto px-4 border-t border-outline-variant pt-4">
        <p class="px-4 font-data-mono text-[11px] text-on-surface-variant/70 leading-relaxed">
          Portfolio project — public/synthetic data only.<br/>See README for evaluation results.
        </p>
      </div>
    `;
  }

  const topbarEl = document.getElementById("app-topbar");
  if (topbarEl) {
    topbarEl.innerHTML = `
      <div class="flex items-center gap-8">
        <div class="font-label-caps text-label-caps uppercase text-on-surface-variant tracking-wider">
          Support Ticket Intelligence
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span id="api-status-dot" class="w-2 h-2 rounded-full bg-outline-variant" title="Checking API..."></span>
        <span id="api-status-text" class="font-data-mono text-data-mono text-[11px] text-on-surface-variant">API: checking...</span>
      </div>
    `;
  }

  SignalAPI.health()
    .then(() => setApiStatus(true))
    .catch(() => setApiStatus(false));
}

function setApiStatus(ok) {
  const dot = document.getElementById("api-status-dot");
  const text = document.getElementById("api-status-text");
  if (!dot || !text) return;
  dot.className = `w-2 h-2 rounded-full ${ok ? "bg-primary" : "bg-error"}`;
  text.textContent = ok ? "API: online" : "API: unreachable";
}
