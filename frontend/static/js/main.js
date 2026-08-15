/* ═══ main.js — Cold Weather EV Modeler ═══ */

// ═══ Theme Toggle ═══
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme");
  const next = current === "light" ? "dark" : "light";
  html.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = next === "light" ? "🌙" : "☀️";
}

(function () {
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = saved === "light" ? "🌙" : "☀️";
  });
})();

// ═══ Mobile Sidebar ═══
function toggleSidebar() {
  document.querySelector(".sidebar")?.classList.toggle("open");
}

// ═══ Sidebar Navigation: collapsible sections + live search ═══
// With this many feature areas, a flat always-expanded list stopped being
// usable -- sections collapse/expand (state remembered per-browser via
// localStorage), and typing in the search box filters every nav link by
// text, auto-expanding whichever sections still have a match.
(function () {
  const STORAGE_KEY = "navSectionState";

  function loadSectionState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch (e) {
      return {};
    }
  }

  function saveSectionState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* localStorage unavailable (private mode etc.) -- just don't persist */
    }
  }

  function setSectionCollapsed(section, collapsed) {
    section.classList.toggle("collapsed", collapsed);
  }

  function initSidebarNav() {
    const sections = document.querySelectorAll(".sidebar-nav .nav-section");
    if (!sections.length) return;

    const state = loadSectionState();

    sections.forEach((section) => {
      const slug = section.dataset.section;
      const defaultCollapsed = section.dataset.defaultCollapsed === "true";
      const hasActiveLink = section.querySelector(".nav-link.active") !== null;

      // Saved state wins; otherwise fall back to the section's own
      // default; either way, a section containing the current page
      // is always forced open so you never lose your place.
      let collapsed = slug in state ? state[slug] : defaultCollapsed;
      if (hasActiveLink) collapsed = false;
      setSectionCollapsed(section, collapsed);

      const title = section.querySelector(".nav-section-title");
      title?.addEventListener("click", () => {
        const nowCollapsed = !section.classList.contains("collapsed");
        setSectionCollapsed(section, nowCollapsed);
        const current = loadSectionState();
        current[slug] = nowCollapsed;
        saveSectionState(current);
      });
    });

    // --- Search ---
    const input = document.getElementById("navSearchInput");
    const clearBtn = document.getElementById("navSearchClear");
    const wrap = document.getElementById("navSearchWrap");
    const sidebarNav = document.querySelector(".sidebar-nav");
    if (!input) return;

    // Remembers each section's collapse state from just before a
    // search started, so clearing the search restores it exactly
    // rather than leaving everything expanded.
    let preSearchState = null;

    function applySearch(query) {
      const q = query.trim().toLowerCase();
      wrap.classList.toggle("has-query", q.length > 0);

      if (!q) {
        if (preSearchState) {
          sections.forEach((section) => {
            setSectionCollapsed(section, preSearchState.get(section) || false);
          });
          preSearchState = null;
        }
        sidebarNav
          .querySelectorAll(".nav-link")
          .forEach((link) => link.classList.remove("search-hidden"));
        sidebarNav.classList.remove("no-results");
        return;
      }

      if (!preSearchState) {
        preSearchState = new Map();
        sections.forEach((section) =>
          preSearchState.set(section, section.classList.contains("collapsed")),
        );
      }

      let anyMatch = false;
      sections.forEach((section) => {
        const links = section.querySelectorAll(".nav-link");
        let sectionHasMatch = false;
        links.forEach((link) => {
          const text = link.textContent.toLowerCase();
          const matches = text.includes(q);
          link.classList.toggle("search-hidden", !matches);
          if (matches) sectionHasMatch = true;
        });
        setSectionCollapsed(section, !sectionHasMatch);
        if (sectionHasMatch) anyMatch = true;
      });
      sidebarNav.classList.toggle("no-results", !anyMatch);
    }

    input.addEventListener("input", () => applySearch(input.value));
    clearBtn?.addEventListener("click", () => {
      input.value = "";
      applySearch("");
      input.focus();
    });
  }

  document.addEventListener("DOMContentLoaded", initSidebarNav);
})();

// ═══ Fetch helper ═══
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: { "Content-Type": "application/json" },
  };
  // Get CSRF token
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  if (csrfMeta) {
    defaults.headers["X-CSRFToken"] = csrfMeta.content;
  }
  const resp = await fetch(url, { ...defaults, ...options });
  if (!resp.ok) {
    let errorMsg = "Request failed";
    try {
      const err = await resp.json();
      errorMsg = err.error || err.message || errorMsg;
    } catch (e) {
      errorMsg = `Server Error: ${resp.status} ${resp.statusText}`;
    }
    console.error(`API Error [${url}]:`, errorMsg);
    throw new Error(errorMsg);
  }
  return resp.json();
}

// ═══ Flash Messages Auto-dismiss ═══
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".alert").forEach(function (alert) {
    setTimeout(function () {
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(function () {
        alert.remove();
      }, 300);
    }, 5010);
  });
});

// ═══ Dashboard Charts ═══
async function loadDashboardCharts() {
  try {
    // Stats
    const stats = await apiFetch("/dashboard/api/stats");
    setTextSafe("statPredictions", stats.total_predictions);
    setTextSafe("statVehicles", stats.total_vehicles);
    setTextSafe("statDegradation", stats.avg_degradation + "%");

    if (stats.recent_weather) {
      setTextSafe("statTemperature", stats.recent_weather.temperature_c + "°C");
    }

    // Temp vs Range chart
    const tempData = await apiFetch("/dashboard/api/charts/temp-vs-range");
    if (tempData.temperatures.length > 0) {
      renderTempRangeChart(tempData);
    }

    // Efficiency chart
    const effData = await apiFetch("/dashboard/api/charts/efficiency");
    if (effData.labels.length > 0) {
      renderEfficiencyChart(effData);
    }

    // Seasonal chart
    const seasonal = await apiFetch("/dashboard/api/charts/seasonal");
    renderSeasonalChart(seasonal);

    // Smart Alerts (Module 15)
    renderSmartAlerts(stats);
  } catch (e) {
    console.log("Dashboard data loading:", e.message);
  }
}

function setTextSafe(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderTempRangeChart(data) {
  const ctx = document.getElementById("tempRangeChart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Temperature vs Predicted Range",
          data: data.temperatures.map((t, i) => ({ x: t, y: data.ranges[i] })),
          backgroundColor: "rgba(99, 140, 255, 0.6)",
          borderColor: "#638cff",
          pointRadius: 5,
          pointHoverRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#8892a8" } } },
      scales: {
        x: {
          title: { display: true, text: "Temperature (°C)", color: "#8892a8" },
          ticks: { color: "#8892a8" },
          grid: { color: "rgba(99,140,255,0.08)" },
        },
        y: {
          title: {
            display: true,
            text: "Predicted Range (km)",
            color: "#8892a8",
          },
          ticks: { color: "#8892a8" },
          grid: { color: "rgba(99,140,255,0.08)" },
        },
      },
    },
  });
}

function renderEfficiencyChart(data) {
  const ctx = document.getElementById("efficiencyChart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels.reverse(),
      datasets: [
        {
          label: "Energy (Wh/km)",
          data: data.energy.reverse(),
          borderColor: "#22d3ee",
          backgroundColor: "rgba(34, 211, 238, 0.1)",
          fill: true,
          tension: 0.4,
        },
        {
          label: "Degradation %",
          data: data.degradation.reverse(),
          borderColor: "#f87171",
          backgroundColor: "rgba(248, 113, 113, 0.1)",
          fill: true,
          tension: 0.4,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#8892a8" } } },
      scales: {
        x: {
          ticks: { color: "#8892a8", maxTicksLimit: 10 },
          grid: { color: "rgba(99,140,255,0.08)" },
        },
        y: {
          ticks: { color: "#8892a8" },
          grid: { color: "rgba(99,140,255,0.08)" },
          title: { display: true, text: "Wh/km", color: "#8892a8" },
        },
        y1: {
          position: "right",
          ticks: { color: "#f87171" },
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Degradation %", color: "#f87171" },
        },
      },
    },
  });
}

function renderSeasonalChart(data) {
  const ctx = document.getElementById("seasonalChart");
  if (!ctx) return;
  const labels = Object.keys(data);
  const values = labels.map((k) => data[k].avg_degradation);
  const colors = ["#f87171", "#fbbf24", "#22d3ee", "#34d399", "#f87171"];

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Avg Range Degradation %",
          data: values,
          backgroundColor: colors.map((c) => c + "40"),
          borderColor: colors,
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#8892a8" } } },
      scales: {
        x: {
          ticks: { color: "#8892a8", maxRotation: 45 },
          grid: { display: false },
        },
        y: {
          ticks: { color: "#8892a8" },
          grid: { color: "rgba(99,140,255,0.08)" },
          title: { display: true, text: "Degradation %", color: "#8892a8" },
        },
      },
    },
  });
}

function renderSmartAlerts(stats) {
  const container = document.getElementById("dashboardAlerts");
  if (!container) return;

  let alerts = [];
  const temp = stats.recent_weather ? stats.recent_weather.temperature_c : -10;

  if (temp < -15) {
    alerts.push({
      type: "danger",
      icon: "🥶",
      title: "Severe Cold Warning",
      desc: "Extreme range loss (>40%) expected. Battery preconditioning is critical.",
    });
  } else if (temp < 0) {
    alerts.push({
      type: "warning",
      icon: "❄️",
      title: "Freezing Conditions",
      desc: "Significant range reduction (15-25%) detected. Expect slower DC charging.",
    });
  }

  if (stats.avg_degradation > 25) {
    alerts.push({
      type: "info",
      icon: "🔋",
      title: "Efficiency Alert",
      desc: "Average range loss is higher than normal. Check tire pressure and HVAC settings.",
    });
  }

  if (alerts.length === 0) return;

  container.innerHTML = alerts
    .map(
      (a) => `
        <div class="alert alert-${a.type}" style="padding:10px;margin-bottom:0;display:flex;gap:10px;align-items:start;">
            <span style="font-size:18px">${a.icon}</span>
            <div>
                <div style="font-weight:700;font-size:13px">${a.title}</div>
                <div style="font-size:11px;opacity:0.9">${a.desc}</div>
            </div>
        </div>
    `,
    )
    .join("");
}

// ═══ Prediction Form ═══
async function submitPrediction(event) {
  event.preventDefault();
  const form = event.target;
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.innerHTML =
    '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;"></span> Predicting...';

  const data = {
    vehicle_id: parseInt(form.vehicle_id?.value || 0),
    temperature_c: parseFloat(form.temperature_c?.value || 0),
    humidity: parseFloat(form.humidity?.value || 50),
    wind_speed_kmh: parseFloat(form.wind_speed_kmh?.value || 10),
    precipitation: form.precipitation?.value || "none",
    battery_percentage: parseFloat(form.battery_percentage?.value || 100),
    vehicle_speed_kmh: parseFloat(form.vehicle_speed_kmh?.value || 60),
    hvac_usage: form.hvac_usage?.checked ?? true,
    terrain_type: form.terrain_type?.value || "flat",
    battery_age_years: parseFloat(form.battery_age_years?.value || 0),
    ml_model: form.ml_model?.value || "random_forest",
  };

  if (!data.vehicle_id) {
    showAlert("warning", "Please select a vehicle.");
    btn.disabled = false;
    btn.innerHTML = "⚡ Predict Range Degradation";
    return;
  }

  try {
    const result = await apiFetch("/predictions/api/predict", {
      method: "POST",
      body: JSON.stringify(data),
    });
    displayPredictionResult(result);
    loadRecommendations(data);
  } catch (e) {
    showAlert("danger", e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "⚡ Predict Range Degradation";
  }
}

// Model comparison view: shows each model's individual raw prediction
// next to the ensemble result, so "confidence" isn't just a mystery
// number -- you can see WHY models agree or disagree.
// Battery Heating Requirement: mirrors
// services/battery_intelligence.py::heating_energy_estimate -- reuses
// the SHAP/rule-based explanation's HVAC contribution_pct (already in
// the response) rather than a separate backend call, and turns it into
// an actual kWh figure for a representative 100km.
function renderHeatingEstimate(explanation, energyWhKm) {
  if (!explanation || !explanation.explanations) return "";
  const hvacFactor = explanation.explanations.find(
    (f) =>
      (f.factor || "").toLowerCase().includes("heater") ||
      (f.factor || "").toLowerCase().includes("hvac"),
  );
  if (!hvacFactor || !hvacFactor.contribution_pct) return "";

  const distanceKm = 100;
  const totalEnergyKwh = (energyWhKm * distanceKm) / 1000;
  const heatingKwh = totalEnergyKwh * (hvacFactor.contribution_pct / 100);

  return `
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-color);font-size:12px;color:var(--text-secondary);">
            🔥 <strong>Estimated heating energy:</strong> ~${heatingKwh.toFixed(1)} kWh of every ${totalEnergyKwh.toFixed(1)} kWh
            used per 100km (${hvacFactor.contribution_pct}% of the predicted degradation effect is attributed to cabin heating).
        </div>`;
}

function renderModelComparison(individualPredictions, ensembleValue) {
  if (!individualPredictions || Object.keys(individualPredictions).length < 2)
    return "";
  const names = Object.keys(individualPredictions);
  const maxVal = Math.max(
    ensembleValue,
    ...Object.values(individualPredictions),
    1,
  );
  const rows = names
    .map((name) => {
      const val = individualPredictions[name];
      const displayName = name
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      const pct = (val / maxVal) * 100;
      return `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <div style="width:110px;font-size:11px;color:var(--text-muted);flex-shrink:0;">${displayName}</div>
                <div style="flex:1;height:6px;background:var(--bg-secondary);border-radius:4px;overflow:hidden;">
                    <div style="width:${pct}%;height:100%;background:var(--border-glow, #638cff);"></div>
                </div>
                <div style="width:40px;font-size:11px;text-align:right;">${val}%</div>
            </div>`;
    })
    .join("");
  return `
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-color);">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">
                What each model predicted individually (ensemble result shown above: ${ensembleValue}%):
            </div>
            ${rows}
        </div>`;
}

function displayPredictionResult(result) {
  const container = document.getElementById("predictionResult");
  if (!container) return;

  const p = result.prediction;
  const v = result.vehicle;
  const anomaly = result.anomaly;
  const details = result.model_details || {};

  // UX-1: confidence is a real, varying number since Phase 1 (ensemble
  // agreement) -- this renders it as a bar instead of leaving it
  // buried in the JSON, so it's actually visible.
  const confidence = p.prediction_confidence ?? 0;
  const confPct = Math.round(confidence * 100);
  const confColor =
    confidence >= 0.75
      ? "var(--success, #22c55e)"
      : confidence >= 0.5
        ? "var(--warning, #f59e0b)"
        : "var(--danger, #ef4444)";
  const ensembleSize = (details.models_in_ensemble || []).length;

  // UX-3: show the real-world-calibrated physics baseline (Phase 1,
  // physics.py) next to the model's actual prediction, so the "why"
  // behind the number is visible instead of just the final figure.
  const baseline = details.physics_baseline_degradation_pct;
  const baselineDiff =
    baseline !== undefined && baseline !== null
      ? p.range_degradation_pct - baseline
      : null;

  container.innerHTML = `
        <div class="animate-slide">
            ${
              anomaly && anomaly.is_anomaly
                ? `<div class="alert alert-warning" style="margin-bottom:12px">
                ⚠️ This prediction is ${Math.abs(anomaly.deviation_pct)} percentage points ${anomaly.direction === "worse_than_expected" ? "higher" : "lower"}
                than the ${anomaly.physics_baseline_pct}% typically seen at ${p.temperature_c}°C in published studies.
                <button class="btn btn-sm" onclick="loadAnomalyNote(${p.id}, this)" style="margin-left:8px">Explain why</button>
            </div>`
                : ""
            }
            <div class="card" style="margin-bottom:16px;padding:14px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-size:13px;color:var(--text-secondary);font-weight:600;">
                        Model Confidence
                        <span title="This isn't a formal probability — it's how much the different ML models (linear regression, random forest, gradient boosting) agree with each other for YOUR specific inputs. They tend to agree closely on typical conditions and disagree more on unusual combinations (e.g. extreme cold + very high speed + mountainous terrain), because each model extrapolates differently outside the range of data it's confident about. Low confidence means 'this is an unusual combination, treat it with a bit more caution' — not 'the model is broken.'" style="cursor:help;color:var(--text-muted);font-weight:400;">ⓘ</span>
                    </span>
                    <span style="font-size:13px;font-weight:700;">${confPct}%</span>
                </div>
                <div style="height:8px;background:var(--bg-secondary);border-radius:5px;overflow:hidden;">
                    <div style="width:${confPct}%;height:100%;background:${confColor};border-radius:5px;"></div>
                </div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:6px;">
                    ${ensembleSize > 0 ? `Based on agreement across ${ensembleSize} models — higher agreement means more confidence.` : details.confidence_note || ""}
                </div>
                ${
                  baseline !== null && baseline !== undefined
                    ? `
                <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-color);font-size:12px;color:var(--text-secondary);">
                    <strong>Typical for ${p.temperature_c}°C</strong> (from published cold-weather studies): ${baseline}% degradation
                    → <strong>your conditions:</strong> ${p.range_degradation_pct}%
                    ${baselineDiff !== null ? `<span style="color:${baselineDiff > 5 ? "var(--danger, #ef4444)" : baselineDiff < -5 ? "var(--success, #22c55e)" : "var(--text-muted)"}">(${baselineDiff > 0 ? "+" : ""}${baselineDiff.toFixed(1)} pts from other factors like HVAC, terrain, speed)</span>` : ""}
                </div>`
                    : ""
                }
                ${renderModelComparison(details.individual_predictions, p.range_degradation_pct)}
                ${renderHeatingEstimate(result.explanation, p.energy_consumption_wh_km)}
            </div>
            <div class="stats-grid" style="margin-bottom:16px">
                <div class="stat-card">
                    <div class="stat-icon red">📉</div>
                    <div><div class="stat-value">${p.range_degradation_pct}%</div><div class="stat-label">Range Degradation</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon blue">🛣️</div>
                    <div><div class="stat-value">${p.predicted_range_km} km</div><div class="stat-label">Predicted Range</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon amber">⚡</div>
                    <div><div class="stat-value">${p.energy_consumption_wh_km} Wh/km</div><div class="stat-label">Energy Consumption</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon cyan">🔌</div>
                    <div><div class="stat-value">${p.charging_slowdown_pct}%</div><div class="stat-label">Charging Slowdown</div></div>
                </div>
            </div>
            ${result.explanation ? renderExplanation(result.explanation) : ""}
            <div class="card" style="margin-top:16px" id="aiBriefingCard">
                <div class="card-header">
                    <h3 class="card-title">💬 AI Trip Briefing</h3>
                    <div style="display:flex;gap:6px;">
                        <button class="btn btn-sm btn-outline" onclick="shareBriefing(${p.id})">🔗 Share</button>
                        <a class="btn btn-sm btn-outline" href="/predictions/api/${p.id}/briefing/pdf">⬇️ PDF</a>
                    </div>
                </div>
                <div id="aiBriefingBody">
                    <button class="btn" onclick="loadBriefing(${p.id})">Generate briefing</button>
                </div>
                <div id="shareLinkResult_${p.id}" style="margin-top:10px;font-size:12px;"></div>
                <div style="margin-top:14px;display:flex;gap:8px;">
                    <input type="text" id="aiQuestionInput" placeholder="Ask about this prediction…" style="flex:1" />
                    <button class="btn" onclick="askAboutPrediction(${p.id})">Ask</button>
                </div>
                <div id="aiAnswerBody" style="margin-top:10px;"></div>
            </div>
            <div class="card" style="margin-top:16px">
                <div class="card-header"><h3 class="card-title">📥 Report What Actually Happened</h3></div>
                <p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">
                    Drove in these conditions? Tell us the real range you got — it directly
                    helps improve future predictions (see Community Reports).
                </p>
                <div style="display:flex;gap:8px;">
                    <input type="number" id="actualRangeInput_${p.id}" placeholder="Actual range (km)" style="flex:1" step="0.1" min="0" />
                    <button class="btn" onclick="submitActualRange(${p.id})">Submit</button>
                </div>
                <div id="actualRangeResult_${p.id}" style="margin-top:8px;font-size:13px;color:var(--text-secondary);"></div>
            </div>
        </div>
    `;
}

// ═══ Phase 3: AI features (briefing / Q&A / anomaly) ═══
async function loadBriefing(predictionId) {
  const body = document.getElementById("aiBriefingBody");
  if (body)
    body.innerHTML =
      '<span class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;"></span> Generating…';
  try {
    const result = await apiFetch(`/predictions/api/${predictionId}/briefing`);
    if (body)
      body.innerHTML = `<p style="color:var(--text-secondary);font-size:14px">${result.briefing}</p>
            <div style="font-size:11px;color:var(--text-muted);margin-top:6px">source: ${result.source}</div>`;
  } catch (e) {
    if (body)
      body.innerHTML = `<p style="color:var(--text-muted);font-size:13px">Couldn't generate a briefing: ${e.message}</p>`;
  }
}

async function askAboutPrediction(predictionId) {
  const input = document.getElementById("aiQuestionInput");
  const answerBody = document.getElementById("aiAnswerBody");
  const question = input?.value?.trim();
  if (!question) return;
  if (answerBody)
    answerBody.innerHTML =
      '<span class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;"></span> Thinking…';
  try {
    const result = await apiFetch(`/predictions/api/${predictionId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    if (answerBody)
      answerBody.innerHTML = `<p style="color:var(--text-secondary);font-size:14px">${result.answer}</p>
            <div style="font-size:11px;color:var(--text-muted);margin-top:6px">source: ${result.source}</div>`;
  } catch (e) {
    if (answerBody)
      answerBody.innerHTML = `<p style="color:var(--text-muted);font-size:13px">Couldn't get an answer: ${e.message}</p>`;
  }
}

async function loadAnomalyNote(predictionId, btn) {
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Loading…";
  }
  try {
    const result = await apiFetch(`/predictions/api/${predictionId}/anomaly`);
    if (btn && result.note) {
      const p = document.createElement("div");
      p.style.marginTop = "8px";
      p.style.fontSize = "13px";
      p.textContent = result.note;
      btn.parentElement.appendChild(p);
      btn.remove();
    }
  } catch (e) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Explain why";
    }
  }
}

function renderExplanation(explanation) {
  if (!explanation || !explanation.explanations) return "";
  let html =
    '<div class="card" style="margin-top:16px"><div class="card-header"><h3 class="card-title">🧠 AI Explanation</h3></div>';
  html += `<p style="color:var(--text-secondary);font-size:14px;margin-bottom:14px">${explanation.summary}</p>`;
  explanation.explanations.forEach((e) => {
    const isPos = e.impact === "positive";
    html += `<div class="xai-card ${isPos ? "positive" : ""}">
            <div class="xai-factor">${e.factor}</div>
            <div class="xai-detail">${e.detail}</div>
        </div>`;
  });
  html += "</div>";
  return html;
}

// ═══ Recommendations ═══
async function loadRecommendations(data) {
  try {
    const result = await apiFetch("/recommendations/api/get", {
      method: "POST",
      body: JSON.stringify(data),
    });
    const container = document.getElementById("recommendationsContainer");
    if (!container || !result.recommendations) return;
    container.innerHTML = result.recommendations
      .map(
        (r) => `
            <div class="rec-card animate-slide">
                <div class="rec-icon">${r.icon}</div>
                <div>
                    <div class="rec-title">${r.title}</div>
                    <div class="rec-desc">${r.description}</div>
                    <div class="rec-impact">💡 ${r.impact}</div>
                </div>
            </div>
        `,
      )
      .join("");
  } catch (e) {
    console.log("Recommendations:", e.message);
  }
}

// ═══ Trip Simulation ═══
function toggleRouteMode() {
  const useReal = document.getElementById("useRealRoute")?.checked;
  const manualFields = document.getElementById("manualFields");
  if (manualFields) manualFields.style.display = useReal ? "none" : "grid";
}

async function submitTrip(event) {
  event.preventDefault();
  const form = event.target;
  const useRealRoute = form.use_real_route?.checked ?? true;
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = true;
  const originalBtnText = btn.innerHTML;
  btn.innerHTML =
    '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;"></span> Simulating...';

  try {
    let result, usedRealRoute;
    if (useRealRoute) {
      // Phase 2/3: real geocoding + real route + real elevation-
      // derived terrain + real weather, instead of manually typed
      // distance/temperature.
      const data = {
        vehicle_id: parseInt(form.vehicle_id.value),
        source: form.source.value,
        destination: form.destination.value,
        speed_kmh: parseFloat(form.speed_kmh.value),
        heater_usage: form.heater_usage?.checked ?? true,
        num_passengers: parseInt(form.num_passengers?.value || 1),
        battery_percentage: parseFloat(form.battery_percentage?.value || 100),
      };
      result = await apiFetch("/trip/api/route-predict", {
        method: "POST",
        body: JSON.stringify(data),
      });
      usedRealRoute = true;
    } else {
      const data = {
        vehicle_id: parseInt(form.vehicle_id.value),
        source: form.source.value,
        destination: form.destination.value,
        distance_km: parseFloat(form.distance_km.value),
        temperature_c: parseFloat(form.temperature_c.value),
        speed_kmh: parseFloat(form.speed_kmh.value),
        heater_usage: form.heater_usage?.checked ?? true,
        num_passengers: parseInt(form.num_passengers?.value || 1),
        battery_percentage: parseFloat(form.battery_percentage?.value || 100),
      };
      result = await apiFetch("/trip/api/simulate", {
        method: "POST",
        body: JSON.stringify(data),
      });
      usedRealRoute = false;
    }

    const t = result.trip;
    const container = document.getElementById("tripResult");
    if (container) {
      const routeInfo = usedRealRoute
        ? `
                <div class="alert alert-success" style="margin-bottom:12px;font-size:13px">
                    🗺️ Real route: ${result.route.distance_km} km, ~${result.route.duration_min} min &nbsp;|&nbsp;
                    ⛰️ Terrain: ${result.terrain.type} (${result.terrain.source})&nbsp;|&nbsp;
                    🌡️ Weather: ${result.weather.temperature_c}°C (${result.weather.data_source})
                </div>`
        : "";
      container.innerHTML =
        routeInfo +
        `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon amber">🔋</div>
                        <div><div class="stat-value">${t.estimated_battery_usage_pct}%</div><div class="stat-label">Battery Usage</div></div></div>
                    <div class="stat-card"><div class="stat-icon blue">🛣️</div>
                        <div><div class="stat-value">${t.predicted_remaining_range_km} km</div><div class="stat-label">Remaining Range</div></div></div>
                    <div class="stat-card"><div class="stat-icon cyan">🔌</div>
                        <div><div class="stat-value">${t.charging_stops_required}</div><div class="stat-label">Charging Stops</div></div></div>
                    <div class="stat-card"><div class="stat-icon green">✅</div>
                        <div><div class="stat-value">${t.estimated_arrival_battery_pct}%</div><div class="stat-label">Arrival Battery</div></div></div>
                </div>`;
    }
  } catch (e) {
    showAlert("danger", e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalBtnText;
  }
}

// ═══ Charging Analysis ═══
async function submitCharging(event) {
  event.preventDefault();
  const form = event.target;
  const data = {
    vehicle_id: parseInt(form.vehicle_id.value),
    temperature_c: parseFloat(form.temperature_c.value),
    current_pct: parseFloat(form.current_pct.value),
    target_pct: parseFloat(form.target_pct.value),
    fast_charging: form.fast_charging?.checked ?? true,
  };

  try {
    const result = await apiFetch("/charging/api/predict", {
      method: "POST",
      body: JSON.stringify(data),
    });
    const container = document.getElementById("chargingResult");
    if (container) {
      container.innerHTML = `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon blue">⏱️</div>
                        <div><div class="stat-value">${result.charging_time_minutes} min</div><div class="stat-label">Charging Time</div></div></div>
                    <div class="stat-card"><div class="stat-icon amber">⚡</div>
                        <div><div class="stat-value">${result.effective_power_kw} kW</div><div class="stat-label">Effective Power</div></div></div>
                    <div class="stat-card"><div class="stat-icon green">📊</div>
                        <div><div class="stat-value">${result.efficiency_pct}%</div><div class="stat-label">Charging Efficiency</div></div></div>
                    <div class="stat-card"><div class="stat-icon red">📉</div>
                        <div><div class="stat-value">${result.slowdown_pct}%</div><div class="stat-label">Cold Slowdown</div></div></div>
                </div>`;
    }
    // Load temperature comparison chart
    loadChargingComparison(data.vehicle_id, data.fast_charging);
  } catch (e) {
    showAlert("danger", e.message);
  }
}

async function loadChargingComparison(vehicleId, fastCharging) {
  try {
    const result = await apiFetch("/charging/api/compare", {
      method: "POST",
      body: JSON.stringify({
        vehicle_id: vehicleId,
        fast_charging: fastCharging,
      }),
    });
    const ctx = document.getElementById("chargingChart");
    if (!ctx) return;
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: result.comparisons.map((c) => c.label),
        datasets: [
          {
            label: "Charging Time (min)",
            data: result.comparisons.map((c) => c.charging_time_minutes),
            backgroundColor: result.comparisons.map((c) =>
              c.charging_time_minutes > 60
                ? "rgba(248,113,113,0.6)"
                : c.charging_time_minutes > 40
                  ? "rgba(251,191,36,0.6)"
                  : "rgba(52,211,153,0.6)",
            ),
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#8892a8" } } },
        scales: {
          x: { ticks: { color: "#8892a8" }, grid: { display: false } },
          y: {
            ticks: { color: "#8892a8" },
            grid: { color: "rgba(99,140,255,0.08)" },
          },
        },
      },
    });
  } catch (e) {
    console.log(e);
  }
}

// ═══ Compare Vehicles ═══
async function submitComparison(event) {
  event.preventDefault();
  const checkboxes = document.querySelectorAll(
    'input[name="vehicle_ids"]:checked',
  );
  const ids = Array.from(checkboxes).map((cb) => parseInt(cb.value));
  const temp = parseFloat(document.getElementById("compareTemp")?.value || -10);

  if (ids.length < 2) {
    showAlert("warning", "Please select at least 2 vehicles to compare.");
    return;
  }

  try {
    const result = await apiFetch("/compare/api/compare", {
      method: "POST",
      body: JSON.stringify({ vehicle_ids: ids, temperature_c: temp }),
    });
    displayComparison(result);
  } catch (e) {
    showAlert("danger", e.message);
  }
}

function displayComparison(result) {
  const container = document.getElementById("comparisonResult");
  if (!container) return;

  let html = '<div class="table-container animate-slide"><table><thead><tr>';
  html +=
    "<th>Vehicle</th><th>Battery</th><th>EPA Range</th><th>Degradation %</th><th>Predicted Range</th><th>Energy Wh/km</th><th>Charging Slow%</th>";
  html += "</tr></thead><tbody>";

  result.comparisons.forEach((c) => {
    const v = c.vehicle;
    const p = c.prediction;
    html += `<tr>
            <td><strong>${v.manufacturer}</strong> ${v.model_name}</td>
            <td>${v.battery_capacity_kwh} kWh (${v.battery_chemistry})</td>
            <td>${v.epa_range_km} km</td>
            <td><span class="badge ${p.range_degradation_pct > 20 ? "badge-red" : "badge-green"}">${p.range_degradation_pct}%</span></td>
            <td>${p.predicted_range_km} km</td>
            <td>${p.energy_consumption_wh_km}</td>
            <td>${p.charging_slowdown_pct}%</td>
        </tr>`;
  });
  html += "</tbody></table></div>";
  container.innerHTML = html;
}

// ═══ Weather ═══
async function fetchWeather() {
  const city = document.getElementById("weatherCity")?.value || "New York";
  try {
    const weather = await apiFetch(
      `/weather/api/current?city=${encodeURIComponent(city)}`,
    );
    const container = document.getElementById("weatherResult");
    if (container) {
      const isLive = weather.data_source === "live";
      const sourceBadge = `<div class="alert ${isLive ? "alert-success" : "alert-warning"}" style="margin-bottom:1rem;">
                ${isLive ? "🟢 Live data from OpenWeatherMap" : "🟡 Demo/fallback data" + (weather.note ? " — " + weather.note : " — set OPENWEATHERMAP_API_KEY in .env for real conditions")}
            </div>`;
      container.innerHTML =
        sourceBadge +
        `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon blue">🌡️</div>
                        <div><div class="stat-value">${weather.temperature_c}°C</div><div class="stat-label">Temperature (Feels ${weather.feels_like_c}°C)</div></div></div>
                    <div class="stat-card"><div class="stat-icon cyan">💧</div>
                        <div><div class="stat-value">${weather.humidity}%</div><div class="stat-label">Humidity</div></div></div>
                    <div class="stat-card"><div class="stat-icon amber">💨</div>
                        <div><div class="stat-value">${weather.wind_speed_kmh?.toFixed(1)} km/h</div><div class="stat-label">Wind Speed</div></div></div>
                    <div class="stat-card"><div class="stat-icon ${weather.severity === "extreme" ? "red" : "green"}">
                        ${weather.severity === "extreme" ? "🥶" : weather.severity === "severe" ? "❄️" : "🌤️"}</div>
                        <div><div class="stat-value">${weather.severity?.toUpperCase()}</div><div class="stat-label">Severity for EVs</div></div></div>
                </div>`;
    }
  } catch (e) {
    showAlert("danger", e.message);
  }
}

// ═══ Utility ═══
function showAlert(type, message) {
  const icons = { success: "✅", danger: "❌", warning: "⚠️", info: "ℹ️" };
  const container =
    document.getElementById("alertContainer") ||
    document.querySelector(".page-content");
  if (!container) return;
  const div = document.createElement("div");
  div.className = `alert alert-${type} animate-slide`;
  div.innerHTML = `${icons[type] || ""} ${message}`;
  container.prepend(div);
  setTimeout(() => {
    div.style.opacity = "0";
    setTimeout(() => div.remove(), 300);
  }, 5010);
}

// ═══ Dataset Upload ═══
async function uploadDataset(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);

  try {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const headers = {};
    if (csrfMeta) headers["X-CSRFToken"] = csrfMeta.content;

    const resp = await fetch("/datasets/api/upload", {
      method: "POST",
      body: formData,
      headers: headers,
    });
    const result = await resp.json();
    if (resp.ok) {
      showAlert("success", "Dataset uploaded successfully!");
      setTimeout(() => location.reload(), 1500);
    } else {
      showAlert("danger", result.error);
    }
  } catch (e) {
    showAlert("danger", e.message);
  }
}

// ═══ Phase 4: Community Range Reports (FEAT-4) ═══
async function submitCommunityReport(event) {
  event.preventDefault();
  const form = event.target;
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = true;
  const data = {
    vehicle_id: parseInt(form.vehicle_id.value),
    temperature_c: parseFloat(form.temperature_c.value),
    starting_battery_pct: parseFloat(form.starting_battery_pct.value),
    reported_range_km: parseFloat(form.reported_range_km.value),
    terrain_type: form.terrain_type.value,
    precipitation: form.precipitation.value,
    hvac_usage: form.hvac_usage.checked,
    notes: form.notes.value || null,
  };
  try {
    await apiFetch("/community/api/reports", {
      method: "POST",
      body: JSON.stringify(data),
    });
    showAlert(
      "success",
      "Thanks — your report was added and will help improve predictions.",
    );
    form.reset();
    loadCommunityStats();
    loadCommunityReports();
  } catch (e) {
    showAlert("danger", e.message);
  } finally {
    btn.disabled = false;
  }
}

async function loadCommunityStats() {
  const container = document.getElementById("communityStats");
  if (!container) return;
  try {
    const s = await apiFetch("/community/api/reports/stats");
    container.innerHTML = `
            <div class="stat-card"><div class="stat-icon blue">📥</div>
                <div><div class="stat-value">${s.total_real_samples}</div><div class="stat-label">Total real samples</div></div></div>
            <div class="stat-card"><div class="stat-icon green">🌍</div>
                <div><div class="stat-value">${s.from_community_reports}</div><div class="stat-label">Community reports</div></div></div>
            <div class="stat-card"><div class="stat-icon amber">🔁</div>
                <div><div class="stat-value">${s.from_prediction_followups}</div><div class="stat-label">Prediction follow-ups</div></div></div>
            <div class="stat-card"><div class="stat-icon cyan">🎯</div>
                <div><div class="stat-value">${s.model_accuracy_vs_real_outcomes ? s.model_accuracy_vs_real_outcomes.mae_vs_real_user_outcomes_pct + "pp" : "—"}</div><div class="stat-label">Model MAE vs real outcomes</div></div></div>`;
  } catch (e) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Couldn't load stats: ${e.message}</p>`;
  }
}

async function loadCommunityReports() {
  const container = document.getElementById("communityReportsList");
  if (!container) return;
  try {
    const result = await apiFetch("/community/api/reports?per_page=15");
    const reports = result.reports || [];
    if (reports.length === 0) {
      container.innerHTML =
        '<p style="color:var(--text-muted);font-size:13px;">No reports yet — be the first.</p>';
      return;
    }
    const rows = reports
      .map(
        (r) => `
            <tr>
                <td>${r.vehicle ? r.vehicle.manufacturer + " " + r.vehicle.model_name : "—"}</td>
                <td>${r.temperature_c}°C</td>
                <td>${r.reported_range_km} km</td>
                <td>${r.terrain_type}</td>
                <td>${new Date(r.created_at).toLocaleDateString()}</td>
            </tr>`,
      )
      .join("");
    container.innerHTML = `
            <table>
                <thead><tr><th>Vehicle</th><th>Temp</th><th>Range</th><th>Terrain</th><th>Date</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
  } catch (e) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Couldn't load reports: ${e.message}</p>`;
  }
}

// ═══ Phase 4: report actual range after a prediction (FEAT-6) ═══
async function submitActualRange(predictionId) {
  const input = document.getElementById("actualRangeInput_" + predictionId);
  const resultEl = document.getElementById("actualRangeResult_" + predictionId);
  const value = input?.value;
  if (!value) return;
  try {
    const result = await apiFetch(
      `/predictions/api/${predictionId}/report-actual`,
      {
        method: "POST",
        body: JSON.stringify({ actual_range_km: parseFloat(value) }),
      },
    );
    if (resultEl) {
      resultEl.innerHTML =
        `Thanks — predicted ${result.predicted_range_km} km, you got ${result.actual_range_km} km` +
        (result.error_pct !== null ? ` (${result.error_pct}% off).` : ".") +
        ` This will help improve future predictions.`;
    }
  } catch (e) {
    if (resultEl) resultEl.innerHTML = `Couldn't save: ${e.message}`;
  }
}

// ═══ Phase 4 (continued): FEAT-2 charging station finder ═══
async function findChargingStations() {
  const input = document.getElementById("stationSearchInput");
  const container = document.getElementById("stationsResult");
  const place = input?.value?.trim();
  if (!place || !container) return;
  container.innerHTML =
    '<p style="color:var(--text-muted);font-size:13px;">Searching…</p>';
  try {
    const result = await apiFetch(
      `/charging/api/stations?place=${encodeURIComponent(place)}`,
    );
    if (result.stations.length === 0) {
      container.innerHTML =
        '<p style="color:var(--text-muted);font-size:13px;">No stations found nearby.</p>';
      return;
    }
    const rows = result.stations
      .map(
        (s) => `
            <tr>
                <td>${s.name}${s.operator ? ' <span style="color:var(--text-muted);font-size:11px;">(' + s.operator + ")</span>" : ""}</td>
                <td>${s.address || "—"}</td>
                <td>${s.distance_km !== null ? s.distance_km + " km" : "—"}</td>
                <td>${s.connector_types.join(", ") || "—"}</td>
                <td>${s.max_power_kw ? s.max_power_kw + " kW" : "—"}</td>
            </tr>`,
      )
      .join("");
    container.innerHTML = `
            <table>
                <thead><tr><th>Station</th><th>Address</th><th>Distance</th><th>Connectors</th><th>Max Power</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
  } catch (e) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Couldn't find stations: ${e.message}</p>`;
  }
}

// ═══ Phase 4 (continued): FEAT-1 battery health tracking ═══
async function submitBatteryHealth(event, vehicleId) {
  event.preventDefault();
  const form = event.target;
  const data = {
    soh_pct: parseFloat(form.soh_pct.value),
    odometer_km: form.odometer_km.value
      ? parseFloat(form.odometer_km.value)
      : null,
    notes: form.notes.value || null,
  };
  try {
    await apiFetch(`/vehicles/api/${vehicleId}/battery-health`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    form.reset();
    showAlert("success", "Reading saved.");
    loadBatteryHealth(vehicleId);
  } catch (e) {
    showAlert("danger", e.message);
  }
}

async function loadBatteryHealth(vehicleId) {
  const summary = document.getElementById("batteryTrendSummary");
  const table = document.getElementById("batteryHistoryTable");
  try {
    const result = await apiFetch(`/vehicles/api/${vehicleId}/battery-health`);
    if (summary) {
      if (result.trend) {
        const t = result.trend;
        const sign = t.slope_pct_per_year >= 0 ? "+" : "";
        summary.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card"><div class="stat-icon ${t.slope_pct_per_year < 0 ? "red" : "green"}">📉</div>
                            <div><div class="stat-value">${sign}${t.slope_pct_per_year}%/yr</div><div class="stat-label">Degradation rate</div></div></div>
                        <div class="stat-card"><div class="stat-icon blue">🔋</div>
                            <div><div class="stat-value">${t.latest_soh_pct}%</div><div class="stat-label">Latest SOH</div></div></div>
                        <div class="stat-card"><div class="stat-icon amber">🔮</div>
                            <div><div class="stat-value">${t.projections["3_year"]}%</div><div class="stat-label">Projected in 3 yrs</div></div></div>
                    </div>
                    <p style="font-size:11px;color:var(--text-muted);margin-top:10px;">
                        Linear projection from ${t.num_records} reading(s) — treat as a rough trend, not a guarantee.
                    </p>`;
      } else {
        summary.innerHTML =
          '<p style="color:var(--text-muted);font-size:13px;">Log at least 2 readings to see a trend.</p>';
      }
    }
    if (table) {
      if (result.records.length === 0) {
        table.innerHTML =
          '<p style="color:var(--text-muted);font-size:13px;">No readings yet.</p>';
      } else {
        const rows = result.records
          .slice()
          .reverse()
          .map(
            (r) => `
                    <tr><td>${new Date(r.recorded_at).toLocaleDateString()}</td><td>${r.soh_pct}%</td><td>${r.odometer_km ?? "—"}</td></tr>
                `,
          )
          .join("");
        table.innerHTML = `<table><thead><tr><th>Date</th><th>SOH</th><th>Odometer</th></tr></thead><tbody>${rows}</tbody></table>`;
      }
    }
  } catch (e) {
    if (summary)
      summary.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Couldn't load: ${e.message}</p>`;
  }
}

// ═══ Phase 4 (continued): FEAT-3 cold snap alerts ═══
async function submitAlertSubscription(event) {
  event.preventDefault();
  const form = event.target;
  const data = {
    location: form.location.value,
    temperature_threshold_c: parseFloat(form.temperature_threshold_c.value),
  };
  try {
    await apiFetch("/alerts/api/subscriptions", {
      method: "POST",
      body: JSON.stringify(data),
    });
    form.reset();
    form.temperature_threshold_c.value = -10;
    showAlert("success", "Alert created.");
    loadAlertSubscriptions();
  } catch (e) {
    showAlert("danger", e.message);
  }
}

async function loadAlertSubscriptions() {
  const container = document.getElementById("alertSubscriptionsList");
  if (!container) return;
  try {
    const result = await apiFetch("/alerts/api/subscriptions");
    const subs = result.subscriptions || [];
    if (subs.length === 0) {
      container.innerHTML =
        '<p style="color:var(--text-muted);font-size:13px;">No alerts yet.</p>';
      return;
    }
    container.innerHTML = subs
      .map(
        (s) => `
            <div class="card" style="margin-bottom:10px;padding:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong>${s.location}</strong> — alert at ≤ ${s.temperature_threshold_c}°C
                        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
                            ${s.enabled ? "🟢 Active" : "⚪ Paused"}
                            ${s.last_checked_temperature_c !== null ? " · Last checked: " + s.last_checked_temperature_c + "°C" : ""}
                            ${s.last_alert_sent_at ? " · Last alerted: " + new Date(s.last_alert_sent_at).toLocaleString() : ""}
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;">
                        <button class="btn btn-sm btn-outline" onclick="toggleAlertSubscription(${s.id})">${s.enabled ? "Pause" : "Resume"}</button>
                        <button class="btn btn-sm btn-outline" onclick="deleteAlertSubscription(${s.id})">Delete</button>
                    </div>
                </div>
            </div>`,
      )
      .join("");
  } catch (e) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Couldn't load alerts: ${e.message}</p>`;
  }
}

async function toggleAlertSubscription(id) {
  try {
    await apiFetch(`/alerts/api/subscriptions/${id}/toggle`, {
      method: "POST",
    });
    loadAlertSubscriptions();
  } catch (e) {
    showAlert("danger", e.message);
  }
}

async function deleteAlertSubscription(id) {
  if (!confirm("Delete this alert?")) return;
  try {
    await apiFetch(`/alerts/api/subscriptions/${id}`, { method: "DELETE" });
    loadAlertSubscriptions();
  } catch (e) {
    showAlert("danger", e.message);
  }
}

async function checkAlertsNow() {
  const el = document.getElementById("checkNowResult");
  if (el) el.textContent = "Checking…";
  try {
    const r = await apiFetch("/alerts/api/check-now", { method: "POST" });
    if (el)
      el.textContent = `Checked ${r.checked}, triggered ${r.triggered}, sent ${r.sent}, skipped (cooldown) ${r.skipped_cooldown}.`;
    loadAlertSubscriptions();
  } catch (e) {
    if (el) el.textContent = `Failed: ${e.message}`;
  }
}

// ═══ Forecast-based predictions: "plan for a future date" ═══
async function loadForecastOptions() {
  const cityInput = document.getElementById("forecastCityInput");
  const listEl = document.getElementById("forecastOptionsList");
  const city = cityInput?.value?.trim();
  if (!city || !listEl) return;
  listEl.innerHTML =
    '<span style="font-size:12px;color:var(--text-muted);">Loading forecast…</span>';
  try {
    const result = await apiFetch(
      `/weather/api/forecast?city=${encodeURIComponent(city)}`,
    );
    const forecasts = (result.forecasts || []).slice(0, 12); // next ~36 hours at 3hr steps, or demo's 24 slots trimmed
    if (forecasts.length === 0) {
      listEl.innerHTML =
        '<span style="font-size:12px;color:var(--text-muted);">No forecast available.</span>';
      return;
    }
    const badge =
      result.data_source === "live"
        ? '<span style="color:#22c55e;">🟢 live forecast</span>'
        : '<span style="color:#f59e0b;">🟡 demo forecast</span>';
    const options = forecasts
      .map(
        (f, i) =>
          `<option value="${i}">${new Date(f.datetime).toLocaleString([], { weekday: "short", month: "short", day: "numeric", hour: "2-digit" })} — ${f.temperature_c}°C, ${f.weather}</option>`,
      )
      .join("");
    listEl.innerHTML = `
            <div style="font-size:11px;margin-bottom:4px;">${badge}</div>
            <select id="forecastSlotSelect" class="form-control" style="margin-bottom:6px;">
                <option value="">-- Pick a time --</option>
                ${options}
            </select>
            <button type="button" class="btn btn-sm" onclick="applyForecastSelection(${JSON.stringify(forecasts).replace(/"/g, "&quot;")})">Use this forecast</button>
        `;
  } catch (e) {
    listEl.innerHTML = `<span style="font-size:12px;color:var(--text-muted);">Couldn't load forecast: ${e.message}</span>`;
  }
}

function applyForecastSelection(forecasts) {
  const select = document.getElementById("forecastSlotSelect");
  const idx = select?.value;
  if (idx === "" || idx === undefined) return;
  const f = forecasts[parseInt(idx)];
  if (!f) return;
  const tempInput = document.getElementById("tempInput");
  const humidityInput = document.getElementById("humidityInput");
  const windInput = document.getElementById("windInput");
  const precipInput = document.getElementById("precipInput");
  if (tempInput) tempInput.value = f.temperature_c;
  if (humidityInput && f.humidity !== undefined)
    humidityInput.value = Math.round(f.humidity);
  if (windInput && f.wind_speed_kmh !== undefined)
    windInput.value = Math.round(f.wind_speed_kmh);
  if (precipInput && f.precipitation) precipInput.value = f.precipitation;
  showAlert(
    "success",
    `Loaded forecast for ${new Date(f.datetime).toLocaleString()} — you can still adjust any field before predicting.`,
  );
}

// ═══ Share a briefing as a public read-only link ═══
async function shareBriefing(predictionId) {
  const el = document.getElementById("shareLinkResult_" + predictionId);
  if (el) el.textContent = "Generating link…";
  try {
    const result = await apiFetch(`/predictions/api/${predictionId}/share`, {
      method: "POST",
    });
    if (el) {
      el.innerHTML =
        `<input type="text" readonly value="${result.share_url}" style="width:70%;font-size:11px;" onclick="this.select()"> ` +
        `<button class="btn btn-sm btn-outline" onclick="navigator.clipboard.writeText('${result.share_url}')">Copy</button> ` +
        `<button class="btn btn-sm btn-outline" onclick="revokeShareLink(${predictionId}, this)">Revoke</button>`;
    }
  } catch (e) {
    if (el) el.textContent = `Couldn't create link: ${e.message}`;
  }
}

async function revokeShareLink(predictionId, btn) {
  try {
    await apiFetch(`/predictions/api/${predictionId}/unshare`, {
      method: "POST",
    });
    const el = document.getElementById("shareLinkResult_" + predictionId);
    if (el) el.textContent = "Link revoked.";
  } catch (e) {
    showAlert("danger", e.message);
  }
}
