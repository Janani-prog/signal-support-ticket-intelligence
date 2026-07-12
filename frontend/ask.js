renderNav("ask.html");

document.querySelectorAll(".ask-suggestion").forEach((el) => {
  el.addEventListener("click", () => {
    document.getElementById("ask-input").value = el.dataset.q;
    submitQuestion();
  });
});

function sourceCard(source, index) {
  return `
    <div class="hairline-border bg-surface-container-lowest p-4">
      <div class="flex justify-between items-center mb-2">
        <span class="font-data-mono text-data-mono text-primary font-medium">[${index + 1}] ${source.ticket_id}</span>
        <span class="font-data-mono text-data-mono text-[11px] text-on-surface-variant">score ${source.score.toFixed(3)}</span>
      </div>
      <p class="font-body-sm text-body-sm text-on-surface">"${source.snippet}"</p>
    </div>`;
}

async function submitQuestion() {
  const question = document.getElementById("ask-input").value.trim();
  const errorEl = document.getElementById("ask-error");
  const resultEl = document.getElementById("ask-result");
  errorEl.textContent = "";

  if (!question) {
    errorEl.textContent = "Type a question first.";
    return;
  }

  document.getElementById("ask-heading").textContent = question;
  resultEl.innerHTML = `
    <div class="hairline-border bg-surface-container-lowest p-6 flex items-center gap-3">
      <span class="material-symbols-outlined animate-spin text-primary">progress_activity</span>
      <span class="font-data-mono text-data-mono text-on-surface-variant">Retrieving tickets and synthesizing an answer&hellip;</span>
    </div>`;

  const submitBtn = document.getElementById("ask-submit");
  submitBtn.disabled = true;

  try {
    const result = await SignalAPI.ask(question);
    resultEl.innerHTML = `
      <div class="hairline-border border-t-2 border-t-primary bg-surface-container-lowest p-6 mb-8">
        <div class="flex items-center gap-2 mb-3 font-label-caps text-label-caps text-on-surface-variant uppercase">
          <span class="material-symbols-outlined text-[16px] text-primary">auto_awesome</span>
          Synthesized Answer
        </div>
        <p class="font-body-lg text-body-lg text-on-surface leading-relaxed">${result.answer}</p>
      </div>
      <div class="font-label-caps text-label-caps text-on-surface-variant uppercase mb-3">Sources (${result.sources.length})</div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        ${result.sources.map((s, i) => sourceCard(s, i)).join("")}
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = "";
    errorEl.textContent = `Request failed: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
  }
}

document.getElementById("ask-submit").addEventListener("click", submitQuestion);
document.getElementById("ask-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitQuestion();
});
