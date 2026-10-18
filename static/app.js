const state = { example: null };

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

async function loadExample() {
  try {
    const response = await fetch("/api/example", { cache: "no-store" });
    if (!response.ok) throw new Error(`Example load failed (${response.status})`);
    const payload = await response.json();
    state.example = payload.case;
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

$("#run-button").addEventListener("click", runExample);
loadExample();
