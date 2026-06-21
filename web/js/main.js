let storyData = [];
let chartsData = {};

const HEATMAP_CHARTS = new Set(["top10_heatmap"]);
const MATRIX_CHARTS = new Set(["top100_golden", "top10_golden"]);
const FACET_CHARTS = new Set(["explicit_trend"]);

async function loadData() {
  const [storyRes, chartsRes] = await Promise.all([
    fetch("data/story.json?v=101"),
    fetch("data/charts.json?v=101"),
  ]);
  storyData = await storyRes.json();
  chartsData = await chartsRes.json();
}

function chartHeightClass(chartKey) {
  if (MATRIX_CHARTS.has(chartKey)) return " matrix";
  if (FACET_CHARTS.has(chartKey)) return " facet";
  if (chartKey === "genre_trend" || chartKey === "artist_scatter" || chartKey === "style_distribution")
    return " wide";
  return "";
}

function buildStorySection(chapter) {
  const section = document.createElement("section");
  section.className = "story-section";
  section.id = `story-${chapter.id}`;

  const textCol = document.createElement("div");
  textCol.className = "story-text";
  textCol.innerHTML = `
    <div class="story-meta">
      <span class="chapter-num">${chapter.id}</span>
      <span>${chapter.subtitle}</span>
    </div>
    <h2>${chapter.title}</h2>
    <p>${chapter.narrative}</p>
    ${
      chapter.bullets
        ? `<ul class="story-bullets">${chapter.bullets.slice(0, 3).map((b) => `<li>${b}</li>`).join("")}</ul>`
        : chapter.detail
          ? `<p>${chapter.detail}</p>`
          : ""
    }
  `;

  const chartCol = document.createElement("div");
  chartCol.className = "story-chart-panel";
  const chartId = `chart-${chapter.id}`;
  const hClass = chartHeightClass(chapter.chart);

  chartCol.innerHTML = `
    <div class="chart-toolbar">
      <span class="chart-toolbar-title">${chapter.subtitle}</span>
      <span class="chart-toolbar-note">Tableau 工作簿复刻 · ECharts</span>
    </div>
    <div class="chart-interactive">
      <div class="chart-container${hClass}" id="${chartId}"></div>
    </div>
  `;

  section.appendChild(textCol);
  section.appendChild(chartCol);
  return section;
}

function buildNav() {
  const nav = document.getElementById("navLinks");
  const preview = document.getElementById("previewChapters");
  const progress = document.getElementById("progressBar");

  storyData.forEach((ch, i) => {
    const link = document.createElement("li");
    link.innerHTML = `<a href="#story-${ch.id}">${ch.title}</a>`;
    nav.appendChild(link);

    const prevItem = document.createElement("li");
    prevItem.textContent = `${ch.id}. ${ch.title}`;
    prevItem.dataset.id = ch.id;
    if (i === 0) prevItem.classList.add("active");
    prevItem.addEventListener("click", () => {
      document.getElementById(`story-${ch.id}`)?.scrollIntoView({ behavior: "smooth" });
    });
    preview.appendChild(prevItem);

    const dot = document.createElement("button");
    dot.className = "progress-dot";
    dot.title = ch.title;
    dot.addEventListener("click", () => {
      document.getElementById(`story-${ch.id}`)?.scrollIntoView({ behavior: "smooth" });
    });
    progress.appendChild(dot);
  });
}

async function initCharts() {
  await TableauTheme.loadTableauPalette();
  for (const ch of storyData) {
    await ChartRenderers.renderChart(ch.chart, `chart-${ch.id}`, chartsData);
  }

  const mini = document.getElementById("heroMiniChart");
  if (mini && chartsData.genre_market) {
    mini.style.height = "220px";
    ChartRenderers.renderGenreMarket(mini, chartsData.genre_market.slice(0, 8));
  }
}

function setupScrollObserver() {
  const sections = document.querySelectorAll(".story-section");
  const dots = document.querySelectorAll(".progress-dot");
  const navLinks = document.querySelectorAll(".nav-links a");
  const previewItems = document.querySelectorAll(".chapter-list li");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          const idx = parseInt(entry.target.id.replace("story-", ""), 10) - 1;
          dots.forEach((d, i) => d.classList.toggle("active", i === idx));
          navLinks.forEach((a, i) => a.classList.toggle("active", i === idx));
          previewItems.forEach((li, i) => li.classList.toggle("active", i === idx));
          ChartRenderers.resizeAllCharts();
        }
      });
    },
    { threshold: 0.3, rootMargin: "-8% 0px" }
  );

  sections.forEach((s) => observer.observe(s));
}

async function init() {
  await loadData();
  const container = document.getElementById("storyContainer");
  storyData.forEach((ch) => container.appendChild(buildStorySection(ch)));
  buildNav();
  await initCharts();
  setupScrollObserver();
  window.addEventListener("resize", () => ChartRenderers.resizeAllCharts());
}

document.addEventListener("DOMContentLoaded", init);
