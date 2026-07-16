/**
 * Baseline Monitor — leaderboard + historical rate chart.
 * Chart.js via CDN. Default series: top 5 HYSA + T-Bill + VMFXX.
 */

const RATES_URL = "data/rates.json";
const HISTORY_URL = "data/history.json";

const BENCHMARK_KEYS = new Set(["tbill_4week", "vmfxx"]);
const RANGE_DAYS = { "1M": 30, "3M": 90, "6M": 180, ALL: null };

const SERIES_COLORS = [
  "#f5a623",
  "#4ade80",
  "#38bdf8",
  "#a78bfa",
  "#f472b6",
  "#94a3b8",
  "#fbbf24",
  "#34d399",
];

const EXTRA_COLOR = "#e8eaf0";

let chart = null;
let history = [];
let rates = [];
let nameByKey = {};
let baseKeys = [];
let extraKey = null;
let highlightKey = null;
let activeRange = "ALL";

function isHysa(key) {
  return !BENCHMARK_KEYS.has(key);
}

function pickBaseKeys(rateList) {
  const topHysa = rateList
    .filter((r) => isHysa(r.key))
    .slice(0, 5)
    .map((r) => r.key);

  const benchmarks = ["tbill_4week", "vmfxx"].filter((k) =>
    rateList.some((r) => r.key === k)
  );

  return [...topHysa, ...benchmarks];
}

function filterHistoryByRange(entries, range) {
  const days = RANGE_DAYS[range];
  if (!days || entries.length === 0) return entries;

  const last = new Date(entries[entries.length - 1].date + "T00:00:00");
  const cutoff = new Date(last);
  cutoff.setDate(cutoff.getDate() - days + 1);

  return entries.filter((e) => new Date(e.date + "T00:00:00") >= cutoff);
}

function seriesColor(key, index) {
  if (key === extraKey) return EXTRA_COLOR;
  if (BENCHMARK_KEYS.has(key)) {
    return key === "tbill_4week" ? "#94a3b8" : "#64748b";
  }
  return SERIES_COLORS[index % SERIES_COLORS.length];
}

function buildDatasets(filtered) {
  const keys = extraKey && !baseKeys.includes(extraKey)
    ? [...baseKeys, extraKey]
    : [...baseKeys];

  return keys.map((key, i) => {
    const color = seriesColor(key, i);
    const isHighlight = highlightKey === key;
    const isBenchmark = BENCHMARK_KEYS.has(key);
    const isExtra = key === extraKey;

    return {
      label: nameByKey[key] || key,
      key,
      data: filtered.map((e) => e.rates[key] ?? null),
      borderColor: color,
      backgroundColor: color,
      borderWidth: isHighlight ? 3 : isExtra ? 2.5 : 1.75,
      borderDash: isBenchmark ? [5, 4] : [],
      pointRadius: isHighlight ? 3 : 0,
      pointHoverRadius: 5,
      pointBackgroundColor: color,
      tension: 0.2,
      spanGaps: true,
    };
  });
}

function updateChart() {
  if (!chart) return;

  const filtered = filterHistoryByRange(history, activeRange);
  chart.data.labels = filtered.map((e) => e.date);
  chart.data.datasets = buildDatasets(filtered);
  chart.update();
  syncRowHighlight();
}

function initChart(canvas) {
  const filtered = filterHistoryByRange(history, activeRange);
  const ctx = canvas.getContext("2d");

  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: filtered.map((e) => e.date),
      datasets: buildDatasets(filtered),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "nearest",
        intersect: false,
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: "nearest",
          intersect: false,
          backgroundColor: "#1a1d27",
          borderColor: "#2a2d3a",
          borderWidth: 1,
          titleFont: { family: "'DM Mono', monospace", size: 11 },
          bodyFont: { family: "'Inter', system-ui, sans-serif", size: 12 },
          titleColor: "#a8adc0",
          bodyColor: "#e8eaf0",
          padding: 10,
          displayColors: true,
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              if (v == null) return `${ctx.dataset.label}: —`;
              return `${ctx.dataset.label}: ${v.toFixed(2)}%`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#a8adc0",
            font: { family: "'DM Mono', monospace", size: 10 },
            maxRotation: 0,
            autoSkipPadding: 16,
            callback(_value, index, ticks) {
              const label = this.getLabelForValue(index);
              if (!label) return "";
              // Show sparse ticks: first, last, and a few in between
              const n = ticks.length;
              if (index === 0 || index === n - 1) return formatTick(label);
              if (n > 8 && index % Math.ceil(n / 5) !== 0) return "";
              return formatTick(label);
            },
          },
          grid: { color: "rgba(42,45,58,.6)" },
          border: { color: "#2a2d3a" },
        },
        y: {
          ticks: {
            color: "#a8adc0",
            font: { family: "'DM Mono', monospace", size: 10 },
            callback(value) {
              return `${Number(value).toFixed(2)}%`;
            },
          },
          grid: { color: "rgba(42,45,58,.6)" },
          border: { color: "#2a2d3a" },
        },
      },
    },
  });
}

function formatTick(isoDate) {
  const [, m, d] = isoDate.split("-");
  return `${Number(m)}/${Number(d)}`;
}

function setHighlight(key) {
  highlightKey = highlightKey === key ? null : key;
  updateChart();
}

function onRowClick(key) {
  if (baseKeys.includes(key)) {
    setHighlight(key);
    return;
  }

  if (key === extraKey) {
    extraKey = null;
    highlightKey = null;
    updateChart();
    return;
  }

  // One extra slot: replace previous extra
  extraKey = key;
  highlightKey = key;
  updateChart();
}

function syncRowHighlight() {
  document.querySelectorAll(".row[data-key]").forEach((row) => {
    const key = row.dataset.key;
    const active =
      highlightKey === key || (extraKey === key && highlightKey === key);
    row.classList.toggle("is-chart-active", active || extraKey === key);
    row.classList.toggle("is-highlighted", highlightKey === key);
  });
}

function renderLeaderboard(updated, rateList) {
  const board = document.getElementById("board");
  const maxRate = rateList[0]?.rate ?? 1;

  board.innerHTML = rateList
    .map(
      (item, i) => `
    <div class="row" data-rank="${i + 1}" data-key="${item.key}" role="button" tabindex="0" title="Show on chart">
      <span class="rank">${i + 1}</span>
      <div class="bar-track">
        <div class="bar-fill" data-target="${((item.rate / maxRate) * 100).toFixed(2)}">
          <a class="bar-label" href="${item.url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">
            ${item.name}
          </a>
        </div>
      </div>
      <span class="rate-num">${item.rate.toFixed(2)}%</span>
    </div>`
    )
    .join("");

  document.getElementById("updated").textContent = `as of ${updated}`;

  board.querySelectorAll(".row").forEach((row) => {
    row.addEventListener("click", () => onRowClick(row.dataset.key));
    row.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onRowClick(row.dataset.key);
      }
    });
  });

  requestAnimationFrame(() => {
    board.querySelectorAll(".bar-fill").forEach((el) => {
      el.style.width = el.dataset.target + "%";
    });
  });

  syncRowHighlight();
}

function wireRangeButtons() {
  document.querySelectorAll("[data-range]").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeRange = btn.dataset.range;
      document.querySelectorAll("[data-range]").forEach((b) => {
        b.classList.toggle("is-active", b.dataset.range === activeRange);
      });
      updateChart();
    });
  });
}

async function loadJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${url}`);
  return res.json();
}

async function main() {
  const page = document.getElementById("page");
  const status = document.getElementById("status");

  try {
    const [ratesData, historyData] = await Promise.all([
      loadJson(RATES_URL),
      loadJson(HISTORY_URL),
    ]);

    rates = ratesData.rates;
    history = historyData;
    nameByKey = Object.fromEntries(rates.map((r) => [r.key, r.name]));
    baseKeys = pickBaseKeys(rates);

    status.hidden = true;
    page.hidden = false;

    renderLeaderboard(ratesData.updated, rates);
    initChart(document.getElementById("history-chart"));
    wireRangeButtons();
  } catch (err) {
    status.textContent = `Could not load data. Try refreshing.\n${err.message}`;
    status.classList.add("is-error");
  }
}

main();
