const state = { example: null, candidate: null, disclosurePaths: [], reductionController: null, reductionRun: 0, transformReport: null };

const $ = (selector) => document.querySelector(selector);

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function showStatus(kind, title, message, icon) {
  const banner = $("#status");
  banner.className = `status-banner ${kind}`;
  $("#status-title").textContent = title;
  $("#status-message").textContent = message;
  $(".status-icon").textContent = icon;
}

function showResult(result) {
  const panel = $("#result-panel");
  panel.classList.remove("hidden");
  $("#result-badge").textContent = result.label;
  $("#result-classification").textContent = result.kind;
  $("#result-duration").textContent = `${result.duration_ms} ms`;
  $("#result-evidence").textContent = result.details.error_code || result.details.status || "classified locally";
  $("#result-message").textContent = result.message;
}

function unlockReduction() {
  const step = $("#step-reduce");
  step.classList.remove("locked");
  step.removeAttribute("aria-disabled");
  step.classList.add("active");
  $("#reduction-panel").classList.remove("hidden");
}

function unlockTransform() {
  const step = $("#step-transform");
  step.classList.remove("locked");
  step.removeAttribute("aria-disabled");
  step.classList.add("active");
  $("#transform-panel").classList.remove("hidden");
  renderSensitivePaths();
}

function renderSensitivePaths() {
  const container = $("#sensitive-paths");
  container.replaceChildren();
  state.disclosurePaths.forEach((path) => {
    const label = document.createElement("label");
    label.className = "path-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = path;
    checkbox.checked = true;
    const text = document.createElement("span");
    text.textContent = path;
    label.append(checkbox, text);
    container.appendChild(label);
  });
}

async function loadExample() {
  try {
    const response = await fetch("/api/example", { cache: "no-store" });
    if (!response.ok) throw new Error(`Example load failed (${response.status})`);
    const payload = await response.json();
    state.example = payload.case;
    state.disclosurePaths = state.example.disclosure.sensitive_paths;
    const request = { request: state.example.request, reproduction: state.example.reproduction };
    $("#request-json").textContent = pretty(request);
    $("#assertion-json").textContent = pretty({ expected: state.example.expected, observed: state.example.observed });
  } catch (error) {
    showStatus("error", "Example unavailable", error.message, "×");
    $("#run-button").disabled = true;
  }
}

async function runExample() {
  if (!state.example) return;
  const button = $("#run-button");
  button.disabled = true;
  button.innerHTML = "<span aria-hidden=\"true\">◌</span> Running locally…";
  showStatus("neutral", "Execution in progress", "The deterministic local runner is checking the target failure.", "◌");
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case: state.example })
    });
    const payload = await response.json();
    if (!response.ok && !payload.result) throw new Error(payload.error || "Execution failed");
    const result = payload.result;
    showResult(result);
    if (result.kind === "target-failure") {
      showStatus("target", "Target failure reproduced", "The expected REPROSAFE_TARGET_FAILURE marker is present. Reduction can start from this baseline.", "!");
      state.candidate = JSON.parse(JSON.stringify(state.example));
      unlockReduction();
    } else if (result.kind === "success") {
      showStatus("success", "Target failure absent", "This input completed successfully; it is not a reproduction of the reported bug.", "✓");
    } else {
      showStatus("error", result.label, result.message, "×");
    }
  } catch (error) {
    showStatus("error", "Execution error", error.message, "×");
  } finally {
    button.disabled = false;
    button.innerHTML = "<span aria-hidden=\"true\">▶</span> Run example";
  }
}

function renderCheck(check) {
  const row = document.createElement("div");
  row.className = `check-row ${check.accepted ? "accepted" : "rejected"}`;
  row.innerHTML = `<span class="check-path">${check.path}</span><span class="check-result">${check.accepted ? "✓ accepted" : "— rejected"}</span>`;
  $("#checks-list").appendChild(row);
}

function finishReduction(report) {
  $("#reduction-summary").classList.remove("hidden");
  $("#original-size").textContent = `${report.original_size.toLocaleString()} bytes`;
  $("#candidate-size").textContent = `${report.candidate_size.toLocaleString()} bytes`;
  $("#accepted-count").textContent = `${report.accepted} / ${report.attempts}`;
  $("#reduction-message").textContent = report.message;
  $("#candidate-details").classList.remove("hidden");
  $("#candidate-json").textContent = pretty(report.candidate);
  $("#checks-details").classList.remove("hidden");
  $("#reduce-button").disabled = false;
  $("#reduce-button").innerHTML = "<span aria-hidden=\"true\">⌁</span> Reduce again";
  $("#cancel-button").classList.add("hidden");
  state.reductionController = null;
  if (report.status === "completed") {
    state.candidate = report.candidate;
    unlockTransform();
    showStatus("neutral", "Candidate reduced", "Every accepted change retained the target failure. Disclosure checks have not been performed.", "→");
  }
}

async function reduceExample() {
  if (!state.example) return;
  const runId = ++state.reductionRun;
  const controller = new AbortController();
  state.reductionController = controller;
  $("#reduce-button").disabled = true;
  $("#reduce-button").innerHTML = "<span aria-hidden=\"true\">◌</span> Checking…";
  $("#cancel-button").classList.remove("hidden");
  $("#reduction-progress").classList.remove("hidden");
  $("#reduction-summary").classList.add("hidden");
  $("#candidate-details").classList.add("hidden");
  $("#checks-details").classList.add("hidden");
  $("#checks-list").replaceChildren();
  showStatus("neutral", "Reduction in progress", "Trying smaller candidates and executing each one locally.", "◌");
  try {
    const response = await fetch("/api/reduce", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case: state.example }),
      signal: controller.signal
    });
    const payload = await response.json();
    if (!response.ok || !payload.report) throw new Error(payload.error || "Reduction failed");
    const report = payload.report;
    $("#progress-bar").max = Math.max(report.attempts, 1);
    for (let index = 0; index < report.checks.length; index += 1) {
      if (controller.signal.aborted || runId !== state.reductionRun) return;
      renderCheck(report.checks[index]);
      $("#progress-bar").value = index + 1;
      $("#progress-count").textContent = `${index + 1} / ${report.attempts}`;
      $("#progress-text").textContent = `Checked ${report.checks[index].path}`;
      await new Promise((resolve) => setTimeout(resolve, 24));
    }
    if (controller.signal.aborted || runId !== state.reductionRun) return;
    $("#progress-text").textContent = "All reduction attempts checked";
    finishReduction(report);
  } catch (error) {
    if (error.name === "AbortError") return;
    showStatus("error", "Reduction error", error.message, "×");
    $("#reduce-button").disabled = false;
    $("#cancel-button").classList.add("hidden");
  }
}

function cancelReduction() {
  state.reductionRun += 1;
  if (state.reductionController) state.reductionController.abort();
  state.reductionController = null;
  state.candidate = JSON.parse(JSON.stringify(state.example));
  $("#reduce-button").disabled = false;
  $("#reduce-button").innerHTML = "<span aria-hidden=\"true\">⌁</span> Reduce example";
  $("#cancel-button").classList.add("hidden");
  $("#progress-text").textContent = "Reduction cancelled";
  $("#reduction-message").textContent = "The original input remains intact; no candidate was accepted.";
  showStatus("neutral", "Reduction cancelled", "The original example is still the active candidate. Disclosure checks have not been performed.", "○");
}

function selectedDisclosurePaths() {
  return Array.from(document.querySelectorAll("#sensitive-paths input:checked"), (input) => input.value);
}

function renderTransformCard(report) {
  const reproductionPass = report.reproduction.kind === "target-failure";
  const disclosurePass = report.disclosure.kind === "passed";
  const card = document.createElement("article");
  card.className = `transform-card ${report.acceptable ? "acceptable" : "unacceptable"}`;
  card.innerHTML = `
    <div class="transform-card-heading">
      <div><h4>${report.label}</h4><span class="card-label">${report.strategy === "redact" ? "Replace values with [REDACTED]" : "Replace with shape-preserving demo values"}</span></div>
      <span class="result-pill ${report.acceptable ? "accepted" : "unacceptable"}">${report.acceptable ? "Acceptable candidate" : "Not acceptable"}</span>
    </div>
    <div class="check-stack">
      <div class="mini-check ${reproductionPass ? "pass" : "fail"}"><span class="mini-icon">${reproductionPass ? "✓" : "×"}</span><span><strong>Reproducibility:</strong> ${report.reproduction.label}. ${report.reproduction.message}</span></div>
      <div class="mini-check ${disclosurePass ? "pass" : "fail"}"><span class="mini-icon">${disclosurePass ? "✓" : "×"}</span><span><strong>Disclosure:</strong> ${report.disclosure.label}. ${report.disclosure.message}</span></div>
    </div>
    <p class="card-label">${report.message}</p>`;
  const details = document.createElement("details");
  details.className = "json-details";
  const summary = document.createElement("summary");
  summary.innerHTML = "<span>Inspect transformed JSON</span><span class=\"summary-hint\">proposed export</span>";
  const pre = document.createElement("pre");
  pre.className = "code-block";
  pre.tabIndex = 0;
  pre.textContent = pretty(report.case);
  details.append(summary, pre);
  card.appendChild(details);
  return card;
}

async function transformExample() {
  const paths = selectedDisclosurePaths();
  const caseToTransform = state.candidate || state.example;
  if (!caseToTransform) return;
  const button = $("#transform-button");
  button.disabled = true;
  button.innerHTML = "<span aria-hidden=\"true\">◌</span> Checking…";
  $("#transform-results").classList.add("hidden");
  try {
    const response = await fetch("/api/transform", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case: caseToTransform, paths })
    });
    const payload = await response.json();
    if (!response.ok || !payload.reports) throw new Error(payload.error || "Transformation check failed");
    state.transformReport = payload.reports;
    const results = $("#transform-results");
    results.replaceChildren(...payload.reports.map(renderTransformCard));
    results.classList.remove("hidden");
    const accepted = payload.reports.find((report) => report.acceptable);
    if (accepted) {
      showStatus("success", "Configured disclosure checks passed", "The synthetic candidate preserves the target failure and removes the configured original values. Review is still required.", "✓");
    } else {
      showStatus("error", "No acceptable candidate found", "The configured transformations did not satisfy both reproducibility and disclosure checks.", "×");
    }
  } catch (error) {
    showStatus("error", "Transformation error", error.message, "×");
  } finally {
    button.disabled = false;
    button.innerHTML = "<span aria-hidden=\"true\">◇</span> Check transformations";
  }
}

$("#run-button").addEventListener("click", runExample);
$("#reduce-button").addEventListener("click", reduceExample);
$("#cancel-button").addEventListener("click", cancelReduction);
$("#transform-button").addEventListener("click", transformExample);
loadExample();
