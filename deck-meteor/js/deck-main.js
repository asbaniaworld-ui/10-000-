const MATRIX_CHARTS = new Set(["top100_golden", "top10_golden"]);
const FACET_CHARTS = new Set(["explicit_trend"]);
const WIDE_CHARTS = new Set(["genre_trend", "artist_scatter", "style_distribution"]);

let chartsData = {};
let genreTracks = {};
let otherPlaylist = [];
const rendered = new Set();

function chartClass(chartKey) {
  if (MATRIX_CHARTS.has(chartKey)) return "matrix";
  if (FACET_CHARTS.has(chartKey)) return "facet";
  if (WIDE_CHARTS.has(chartKey)) return "wide";
  return "";
}

async function loadData() {
  const chartsRes = await fetch("../web/data/charts.json?v=111");
  chartsData = await chartsRes.json();
  try {
    const ft = await (await fetch("../web/data/featured_tracks.json?v=111")).json();
    genreTracks = ft.by_genre || {};
    otherPlaylist = ft.other_playlist || [];
  } catch (_) {
    genreTracks = {};
    otherPlaylist = [];
  }
}

async function renderSlideChart(slideIdx) {
  const slide = document.querySelectorAll(".slide")[slideIdx];
  if (!slide) return;
  const chartKey = slide.dataset.chart;
  const chartId = slide.dataset.chartId;
  if (!chartKey || !chartId || rendered.has(chartId)) return;
  const el = document.getElementById(chartId);
  if (!el) return;
  const cls = chartClass(chartKey);
  if (cls) el.classList.add(cls);

  if (chartKey === "genre_market" && window.GenreShowcase) {
    await window.ChartStories?.loadChartStories();
    await window.GenreShowcase.load(chartsData.genre_market, otherPlaylist);
    window.__genreMarketOpts = {
      mode: "rose",
      genreTracks,
      onGenreClick: (genre, stat, track) => {
        window.GenreShowcase.show(genre, stat, track);
        if (genre === "Other") return;
        const t = track || window.DeckMusic?.lookupGenre?.(genre);
        if (t) void window.DeckMusic.play(t);
      },
    };
  } else {
    window.__genreMarketOpts = {};
    window.GenreShowcase?.hide?.();
  }

  await window.ChartRenderers.renderChart(chartKey, chartId, chartsData);
  rendered.add(chartId);
  setTimeout(() => window.ChartRenderers.resizeAllCharts(), 80);
}

async function onSlideChange(i) {
  window.ChartStories?.storyDrawerHide();
  window.DeckMusic?.stop?.();
  window.GenreShowcase?.hide?.();
  await renderSlideChart(i);
}

async function init() {
  await loadData();
  await window.DeckMusic.load();
  window.DeckMusic.indexCharts(chartsData);

  window.__onDeckSlide = onSlideChange;
  const start = window.__currentSlideIndex ?? 0;
  await onSlideChange(start);

  window.addEventListener("resize", () => window.ChartRenderers.resizeAllCharts());
}

document.addEventListener("DOMContentLoaded", init);
