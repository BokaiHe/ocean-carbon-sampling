"use strict";

const state = {
  data: null,
  strategy: "random",
  showZero: false,
  weight: "area",
  domain: "both60",
  scheme: "hidden",
  budgetIndex: 3,
  replayTimers: [],
};

const budgets = ["500", "1000", "2500", "5000"];
const strategyDescriptions = {
  random: "Random gives every candidate month-cell equal selection probability; clusters arise only from the realized draw.",
  historical: "Historical-density draws month-cells without replacement using SOCAT 1990–2004 density weights. It does not replay cruises, repeat lines or platform trajectories.",
  coverage: "Coverage prioritizes underrepresented month–space blocks; it changes allocation, not the total of 5,000 observations.",
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function signed(value, digits = 3) {
  const magnitude = Math.abs(value).toFixed(digits);
  if (value > 0) return `+${magnitude}`;
  if (value < 0) return `−${magnitude}`;
  return Number(0).toFixed(digits);
}

function pct(value) {
  if (value === null || Number.isNaN(value)) return "—";
  return `${signed(value, 2)}%`;
}

function currentEstimandKey() {
  return `${state.weight}|${state.domain}|${state.scheme}`;
}

function animateNumber(element, target, suffix = " µatm") {
  const prior = Number(element.dataset.value ?? target);
  const start = performance.now();
  const duration = 420;
  element.dataset.value = target;
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = prior + (target - prior) * eased;
    element.innerHTML = `${signed(value)} <span>${suffix.trim()}</span>`;
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function updateMap() {
  const image = $("#sampling-map");
  const variant = state.showZero ? "zero" : "base";
  const source = state.data.maps.images[state.strategy][variant];
  image.classList.add("loading");
  image.onload = () => image.classList.remove("loading");
  image.src = source;
  const strategyLabel = state.strategy === "historical" ? "historical-density" : state.strategy;
  image.alt = `${strategyLabel} sampling density${state.showZero ? " with historical structural-zero regions" : ""}`;
  $("#zero-callout").hidden = !state.showZero;
  $("#map-description").textContent = strategyDescriptions[state.strategy];
  $$("[data-strategy]").forEach((button) => {
    const active = button.dataset.strategy === state.strategy;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function syncControls() {
  $$("#estimand-controls input").forEach((input) => {
    input.checked = state[input.name] === input.value;
  });
}

function setJourneyState(key) {
  const [weight, domain, scheme] = key.split("|");
  state.weight = weight;
  state.domain = domain;
  state.scheme = scheme;
  syncControls();
  updateEstimand();
}

function updateEstimand() {
  const key = currentEstimandKey();
  const result = state.data.estimands[key];
  if (!result) throw new Error(`Missing estimand state: ${key}`);
  const { bias, mae, rmse } = result.metrics;
  animateNumber($("#bias-value"), bias.difference);
  $("#mae-value").textContent = signed(mae.difference);
  $("#mae-relative").textContent = pct(mae.relative_pct);
  $("#mae-direction").textContent = mae.direction;
  $("#rmse-value").textContent = signed(rmse.difference);
  $("#rmse-relative").textContent = pct(rmse.relative_pct);
  $("#rmse-direction").textContent = rmse.direction;
  $("#bias-direction").textContent = bias.direction.split(" ")[0];
  $("#estimand-label").textContent = result.label;

  const status = $("#estimand-status");
  status.textContent = result.status === "default" ? "Primary · hidden cells" : result.scheme === "block" ? "Stress test · whole blocks" : "Supporting sensitivity";
  status.className = `status ${result.status}`;
  $$("[data-journey]").forEach((button) => {
    button.classList.toggle("active", button.dataset.journey === key);
  });

  if (result.status === "default") {
    $("#estimand-note").textContent =
      "Historical-density raises MAE in all 3 year-level units, each averaging 20 paired seeds on one fixed hidden set. This is conditional on one ESM and one locked learner, not full-field or real-ocean validation.";
  } else if (key === "equal|global|block") {
    $("#estimand-note").textContent =
      "This is the original full-domain, equal-cell whole-block stress test. Follow the four-stage path to see how its signed offset changes; the path does not replace the primary hidden-cell comparison.";
  } else if (result.scheme === "block") {
    $("#estimand-note").textContent =
      "Whole-block stress test: entire 20° × 10° blocks are excluded before sampling. The 15 year–fold units are descriptive and share one ESM run; this is not the main test of dispersed missing cells.";
  } else {
    $("#estimand-note").textContent =
      "Supporting sensitivity state. Weighting, evaluation domain and candidate support change the quantity being estimated.";
  }
}

function replayJourney() {
  state.replayTimers.forEach(clearTimeout);
  state.replayTimers = [];
  state.data.estimand_journey.forEach((key, index) => {
    state.replayTimers.push(setTimeout(() => setJourneyState(key), index * 850));
  });
}

function budgetMessage(budget) {
  if (budget === "500") {
    return "At 500 samples, median, p99 and RMSE are all higher under coverage: the tail benefit has not emerged.";
  }
  if (budget === "1000") {
    return "At 1,000 samples, p99 and RMSE sit near zero while median error remains higher: directions are mixed.";
  }
  return "At higher counts, the extreme tail falls while median error remains higher—a redistribution, not broad improvement.";
}

function updateSampleSweep() {
  const budget = budgets[state.budgetIndex];
  const record = state.data.sample_sweep[budget];
  $("#budget-value").textContent = Number(budget).toLocaleString("en-US");
  $("#budget-interpretation").textContent = budgetMessage(budget);
  const metricRecords = Object.values(state.data.sample_sweep).flatMap((item) =>
    Object.entries(item.metrics).map(([metric, value]) => ({ metric, ...value })),
  );
  $$(".sweep-card").forEach((card) => {
    const metric = card.dataset.metric;
    const value = record.metrics[metric].difference;
    const all = metricRecords.filter((item) => item.metric === metric).map((item) => Math.abs(item.difference));
    const max = Math.max(...all, 0.001);
    const position = 50 + (value / max) * 42;
    $("strong", card).textContent = signed(value);
    const pill = $(".direction-pill", card);
    pill.textContent = value < 0 ? "Lower" : value > 0 ? "Higher" : "No change";
    pill.className = `direction-pill ${value < 0 ? "better" : "worse"}`;
    $(".zero-bar i", card).style.left = `${Math.max(8, Math.min(92, position))}%`;
  });
}

function renderAudits() {
  const month = state.data.audits.month_balance;
  const rows = ["random", "spatial_coverage", "historical_density"].map((strategy) => {
    const item = month[strategy];
    const label = strategy === "historical_density" ? "historical-density" : strategy.replaceAll("_", " ");
    return `<tr><td>${label}</td><td>${item.minimum_months_covered}/12</td><td>${item.mean_abs_equal_deviation_pp.toFixed(3)} pp</td></tr>`;
  });
  $("#month-audit").innerHTML = `
    <p>Supporting whole-block audit: every selection covers all 12 months. Random and coverage are closely balanced; historical-density retains spatial and monthly density variation, not real cruise trajectories.</p>
    <table class="mini-table"><thead><tr><th>Strategy</th><th>Months</th><th>Mean deviation</th></tr></thead><tbody>${rows.join("")}</tbody></table>`;
  const regrid = state.data.audits.regridding;
  $("#regrid-audit").innerHTML = `
    <p>Exact native-cell-area weighting preserved ${regrid.direction_checks_passed}/${regrid.direction_checks} prespecified directions. ${regrid.note}</p>
    <a href="https://github.com/BokaiHe/ocean-carbon-sampling/blob/main/docs/osse_regrid_audit_results.md">Open the full regridding audit →</a>`;
}

function bindEvents() {
  $$("[data-strategy]").forEach((button) => {
    button.addEventListener("click", () => {
      state.strategy = button.dataset.strategy;
      updateMap();
    });
  });
  $("#zero-toggle").addEventListener("change", (event) => {
    state.showZero = event.target.checked;
    updateMap();
  });
  $$("#estimand-controls input").forEach((input) => {
    input.addEventListener("change", () => {
      state[input.name] = input.value;
      updateEstimand();
    });
  });
  $$("[data-journey]").forEach((button) => {
    button.addEventListener("click", () => setJourneyState(button.dataset.journey));
  });
  $("#replay-journey").addEventListener("click", replayJourney);
  $("#budget-slider").addEventListener("input", (event) => {
    state.budgetIndex = Number(event.target.value);
    updateSampleSweep();
  });
}

async function initialize() {
  try {
    const response = await fetch("data/site-data.json");
    if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
    state.data = await response.json();
    [state.weight, state.domain, state.scheme] = state.data.metadata.default_estimand.split("|");
    syncControls();
    renderValidationComparison();
    const zero = state.data.maps;
    $(".zero-callout .callout-number").textContent = `${zero.zero_coverage_cell_pct.toFixed(1)}%`;
    $(".zero-callout small").textContent = `${zero.zero_coverage_area_pct.toFixed(1)}% after spherical-area weighting`;
    bindEvents();
    updateMap();
    updateEstimand();
    updateSampleSweep();
    renderAudits();
  } catch (error) {
    document.body.insertAdjacentHTML(
      "afterbegin",
      `<div style="padding:12px;background:#7b3028;color:white;text-align:center">Could not load frozen site data. Serve the site over HTTP. ${error.message}</div>`,
    );
    console.error(error);
  }
}

initialize();

function renderValidationComparison() {
  const records = [
    ["hidden", "Primary · scattered hidden cells", "3 years; one fixed hidden set per year"],
    ["block", "Stress test · whole blocks", "15 year–fold units"],
  ];
  $("#validation-comparison").innerHTML = records.map(([scheme, title, units]) => {
    const { mae, rmse, bias } = state.data.estimands[`area|both60|${scheme}`].metrics;
    return `<article class="validation-card"><h3>${title}</h3>
      <p class="validation-question">${scheme === "hidden" ? "Can we reconstruct dispersed missing month-cells?" : "Can we reconstruct whole areas excluded from training?"}</p>
      <p class="validation-number">${pct(mae.relative_pct)} <span>MAE</span></p>
      <p>Random ${mae.random.toFixed(3)} → historical-density ${mae.comparator.toFixed(3)} µatm<br />Difference ${signed(mae.difference)} µatm · ${mae.direction}</p>
      <p>RMSE: ${rmse.random.toFixed(3)} → ${rmse.comparator.toFixed(3)} µatm<br />Difference ${signed(rmse.difference)} µatm (${pct(rmse.relative_pct)})</p>
      <p>Signed-bias difference: ${signed(bias.difference)} µatm</p>
      <small>${units}; 20 paired seeds per unit. Descriptive consistency, not independent Earth-system replication.</small></article>`;
  }).join("");
}
