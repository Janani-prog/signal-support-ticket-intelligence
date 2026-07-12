renderNav("classifier.html");

// Real banking77 test-set examples (see notebooks/01_eda.ipynb) — a static convenience list so
// the demo has one-click examples; not fetched from the API since there's no "sample tickets"
// endpoint in the contract (see TECHNICAL_ARCHITECTURE.md §2.3).
const SAMPLE_TICKETS = [
  { text: "To add money to my account, what currencies can I use?", trueLabel: "supported_cards_and_currencies" },
  { text: "dont understand why transfer failed", trueLabel: "failed_transfer" },
  { text: "The app denied my topped up.", trueLabel: "top_up_failed" },
  { text: "I have a strange payment in my statement", trueLabel: "card_payment_not_recognised" },
  { text: "Where can I obtain my virtual card?", trueLabel: "getting_virtual_card" },
  { text: "How do I locate my card?", trueLabel: "card_arrival" },
];

document.getElementById("sample-tickets").innerHTML = SAMPLE_TICKETS.map(
  (t, i) => `
  <li class="px-4 py-3 hover:bg-surface-container-low transition-colors cursor-pointer" data-idx="${i}">
    <div class="font-body-sm text-body-sm text-on-surface line-clamp-1 mb-1">"${t.text}"</div>
    <span class="font-data-mono text-data-mono text-[11px] text-on-surface-variant bg-surface-container-high px-1 border border-outline-variant">${t.trueLabel}</span>
  </li>`
).join("");

document.querySelectorAll("#sample-tickets li").forEach((li) => {
  li.addEventListener("click", () => {
    document.getElementById("ticket-input").value = SAMPLE_TICKETS[li.dataset.idx].text;
  });
});

function termBar(t, maxAbs) {
  const positive = t.weight >= 0;
  const widthPct = Math.min(100, (Math.abs(t.weight) / maxAbs) * 100);
  return `
    <div class="flex items-center gap-4 py-1.5 ${positive ? "" : "opacity-70"}">
      <div class="w-16 text-right text-on-surface-variant text-[11px] font-data-mono">${t.weight >= 0 ? "+" : ""}${t.weight.toFixed(3)}</div>
      <div class="flex-1 flex items-center ${positive ? "" : "justify-end flex-row-reverse"}">
        <div class="h-4 ${positive ? "bg-primary/20 border-l-2 border-primary" : "bg-secondary/10 border-r-2 border-secondary"} min-w-[2px]" style="width: ${widthPct}%;"></div>
      </div>
      <div class="w-28 px-2 py-0.5 border border-outline-variant bg-surface-container-low text-on-surface text-center font-data-mono text-data-mono text-[11px] truncate" title="${t.term}">"${t.term}"</div>
    </div>`;
}

async function runAnalysis() {
  const text = document.getElementById("ticket-input").value.trim();
  const errorEl = document.getElementById("classify-error");
  errorEl.textContent = "";
  if (!text) {
    errorEl.textContent = "Enter or select a ticket first.";
    return;
  }

  const button = document.getElementById("run-analysis");
  button.disabled = true;
  button.textContent = "Analyzing...";

  try {
    const result = await SignalAPI.classify(text);
    const maxAbs = Math.max(...result.top_terms.map((t) => Math.abs(t.weight)), 0.01);

    document.getElementById("output-panel").innerHTML = `
      <div>
        <div class="flex items-center gap-2 mb-3">
          <h3 class="font-label-caps text-label-caps text-on-surface-variant">Primary Classification</h3>
          <div class="h-px flex-1 bg-outline-variant/50"></div>
        </div>
        <div class="font-display-lg text-display-lg text-on-background tracking-tight leading-none">${result.category}</div>
      </div>
      <div>
        <div class="flex items-center gap-2 mb-3">
          <h3 class="font-label-caps text-label-caps text-on-surface-variant">Confidence Score</h3>
          <div class="h-px flex-1 bg-outline-variant/50"></div>
        </div>
        <div class="flex items-end gap-4 mb-2">
          <span class="font-data-mono text-[32px] font-bold leading-none tracking-tight text-primary">${(result.confidence * 100).toFixed(1)}%</span>
          <span class="font-data-mono text-data-mono text-on-surface-variant mb-1">of 77 possible categories</span>
        </div>
        <div class="h-2 w-full bg-surface-container-highest border border-outline-variant overflow-hidden relative">
          <div class="absolute left-0 top-0 bottom-0 bg-primary" style="width: ${(result.confidence * 100).toFixed(1)}%"></div>
        </div>
      </div>
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-4">
          <h3 class="font-label-caps text-label-caps text-on-surface-variant">Model Interpretability (Top Features)</h3>
          <div class="h-px flex-1 bg-outline-variant/50"></div>
        </div>
        <div class="flex flex-col gap-1">
          ${result.top_terms.length ? result.top_terms.map((t) => termBar(t, maxAbs)).join("") : '<p class="font-data-mono text-data-mono text-on-surface-variant text-[12px]">No indexed terms matched this input.</p>'}
        </div>
      </div>
    `;
  } catch (err) {
    errorEl.textContent = `Request failed: ${err.message}`;
  } finally {
    button.disabled = false;
    button.innerHTML = '<span class="material-symbols-outlined text-[16px]">model_training</span> Run Analysis';
  }
}

document.getElementById("run-analysis").addEventListener("click", runAnalysis);
