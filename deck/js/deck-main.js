const HEATMAP_CHARTS = new Set(["top10_heatmap"]);
const MATRIX_CHARTS = new Set(["top100_golden", "top10_golden"]);
const FACET_CHARTS = new Set(["explicit_trend"]);
const WIDE_CHARTS = new Set(["genre_trend", "artist_scatter", "style_distribution"]);

let chartsData = {};
let genreTracks = {};
let otherPlaylist = [];
const rendered = new Set();
let ch1DismissBound = false;
let ch3AsideBound = false;
let ch4AsideBound = false;
let ch5AsideBound = false;
let ch6AsideBound = false;
let ch8AsideBound = false;

function artistPoint(artist) {
  const row = chartsData.artist_scatter?.find((d) => d.artist === artist);
  if (!row) return null;
  return {
    followers: row.followers,
    popularity: row.popularity,
    tracks: row.tracks,
    genre: row.genre,
  };
}

function openArtistShowcase(artist) {
  const point = artistPoint(artist);
  if (!point) return;
  const track = window.DeckMusic?.lookupArtist?.(artist);
  window.ArtistShowcase?.show?.(artist, point, track);
}

function setupCh4Aside(slide) {
  if (ch4AsideBound || !slide?.classList.contains("ch4-golden")) return;
  ch4AsideBound = true;
  slide.querySelector(".ch4-aside")?.addEventListener("click", (e) => {
    const btn = e.target.closest(".ch4-golden-track");
    if (!btn?.dataset.trackId) return;
    e.preventDefault();
    slide.querySelectorAll(".ch4-golden-track").forEach((el) => {
      el.classList.toggle("is-active", el === btn);
    });
    void window.DeckMusic?.play?.({
      track_id: btn.dataset.trackId,
      artist: btn.dataset.artist,
      track: btn.dataset.track,
      preview_url: btn.dataset.previewUrl || null,
    });
  });
}

function setupCh8Aside(slide) {
  if (ch8AsideBound || !slide?.classList.contains("ch8-emotion")) return;
  ch8AsideBound = true;
  slide.querySelector(".ch8-aside")?.addEventListener("click", (e) => {
    const btn = e.target.closest(".ch8-track-play");
    if (!btn?.dataset.trackId) return;
    e.preventDefault();
    slide.querySelectorAll(".ch8-track-play").forEach((el) => {
      el.classList.toggle("is-active", el === btn);
    });
    void window.DeckMusic?.play?.({
      track_id: btn.dataset.trackId,
      artist: btn.dataset.artist,
      track: btn.dataset.track,
      preview_url: btn.dataset.previewUrl || null,
    });
  });
  slide.querySelector(".deck-text")?.addEventListener("click", (e) => {
    if (e.target.closest(".ch8-aside, .ch8-track-play")) return;
    document.getElementById("chart-8")?._emotionResetAnchor?.();
    window.ChartStories?.storyDrawerHide?.();
  });
}

function setupCh6Aside(slide) {
  if (ch6AsideBound || !slide?.classList.contains("ch6-heat")) return;
  ch6AsideBound = true;
  slide.querySelector(".ch6-timeline")?.addEventListener("click", (e) => {
    const item = e.target.closest("[data-ch6-year]");
    if (!item?.dataset.ch6Year) return;
    e.preventDefault();
    document.getElementById("chart-6")?._heatSortByYear?.(item.dataset.ch6Year);
  });
}

function setupCh5Aside(slide) {
  if (ch5AsideBound || !slide?.classList.contains("ch5-outlier")) return;
  ch5AsideBound = true;
  slide.querySelector(".ch5-aside")?.addEventListener("click", (e) => {
    const btn = e.target.closest(".ch5-billie-track");
    if (!btn?.dataset.trackId) return;
    e.preventDefault();
    slide.querySelectorAll(".ch5-billie-track").forEach((el) => {
      el.classList.toggle("is-active", el === btn);
    });
    void window.DeckMusic?.play?.({
      track_id: btn.dataset.trackId,
      artist: btn.dataset.artist,
      track: btn.dataset.track,
      preview_url: btn.dataset.previewUrl || null,
    });
  });
}

function setupCh3Aside(slide) {
  if (ch3AsideBound || !slide?.classList.contains("ch3-artist")) return;
  ch3AsideBound = true;
  slide.querySelector(".ch3-aside")?.addEventListener("click", (e) => {
    const btn = e.target.closest(".ch3-artist-mini");
    if (!btn?.dataset.artist) return;
    e.preventDefault();
    openArtistShowcase(btn.dataset.artist);
  });
}

function setupCh1Dismiss(slide) {
  if (ch1DismissBound || !slide?.classList.contains("ch1-genre")) return;
  ch1DismissBound = true;
  slide.addEventListener(
    "click",
    (e) => {
      if (
        e.target.closest(
          "#genre-showcase, .gs-pl-item, .gs-close, #music-bar, .deck-chart, canvas, a, button"
        )
      ) {
        return;
      }
      window.DeckMusic?.stop?.();
    },
    true
  );
}

function chartClass(chartKey) {
  if (MATRIX_CHARTS.has(chartKey)) return "matrix";
  if (HEATMAP_CHARTS.has(chartKey)) return "heatmap";
  if (FACET_CHARTS.has(chartKey)) return "facet";
  if (WIDE_CHARTS.has(chartKey)) return "wide";
  return "";
}

async function loadData() {
  const chartsRes = await fetch("../web/data/charts.json?v=119");
  chartsData = await chartsRes.json();
  try {
    const ft = await (await fetch("../web/data/featured_tracks.json?v=120")).json();
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
    setupCh1Dismiss(slide);
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
      onBlankClick: () => {
        window.DeckMusic?.stop?.();
      },
    };
    window.__artistScatterOpts = {};
  } else if (chartKey === "top100_golden") {
    window.__genreMarketOpts = {};
    window.__artistScatterOpts = {};
    window.GenreShowcase?.hide?.();
    window.ArtistShowcase?.hide?.();
    setupCh4Aside(slide);
  } else if (chartKey === "top10_golden") {
    window.__genreMarketOpts = {};
    window.__artistScatterOpts = {};
    window.GenreShowcase?.hide?.();
    window.ArtistShowcase?.hide?.();
    setupCh5Aside(slide);
  } else if (chartKey === "top10_heatmap") {
    window.__genreMarketOpts = {};
    window.__artistScatterOpts = {};
    window.GenreShowcase?.hide?.();
    window.ArtistShowcase?.hide?.();
    setupCh6Aside(slide);
  } else if (chartKey === "emotion_quadrant") {
    window.__genreMarketOpts = {};
    window.__artistScatterOpts = {};
    window.GenreShowcase?.hide?.();
    window.ArtistShowcase?.hide?.();
    setupCh8Aside(slide);
  } else if (chartKey === "artist_scatter") {
    window.__genreMarketOpts = {};
    window.GenreShowcase?.hide?.();
    setupCh3Aside(slide);
    await window.ArtistShowcase?.load?.();
    window.ArtistShowcase?.bind?.();
    window.__artistScatterOpts = {
      featured: ["Taylor Swift", "Bad Bunny", "Drake", "Playboi Carti"],
      onArtistClick: (artist, point) => {
        const track = window.DeckMusic?.lookupArtist?.(artist);
        window.ArtistShowcase?.show?.(artist, point, track);
      },
    };
  } else {
    window.__genreMarketOpts = {};
    window.__artistScatterOpts = {};
    window.GenreShowcase?.hide?.();
    window.ArtistShowcase?.hide?.();
  }

  await window.ChartRenderers.renderChart(chartKey, chartId, chartsData);
  if (chartKey === "top10_golden") {
    const radarId = "chart-5-radar";
    if (!rendered.has(radarId)) {
      const radarEl = document.getElementById(radarId);
      if (radarEl) {
        await window.TableauTheme.loadTableauPalette();
        window.ChartRenderers.renderBillieRadarCompare(
          radarEl,
          chartsData.top10_golden,
          chartsData.top100_golden
        );
        rendered.add(radarId);
        setTimeout(() => window.ChartRenderers.resizeAllCharts(), 150);
      }
    }
  }
  rendered.add(chartId);
  setTimeout(() => window.ChartRenderers.resizeAllCharts(), 80);
}

async function onSlideChange(i) {
  const prev = window.__currentSlideIndex;
  if (prev === 6 && i !== 6) {
    document.getElementById("chart-6")?._heatSortReset?.();
  }
  if (prev === 8 && i !== 8) {
    document.getElementById("chart-8")?._emotionResetAnchor?.();
    window.ChartStories?.storyDrawerHide();
  }
  if (prev === 9 && i !== 9) {
    document.getElementById("chart-9")?._explicitTrendReset?.();
    window.ChartStories?.storyDrawerHide();
  }
  if (prev === 10 && i !== 10) {
    document.getElementById("chart-10")?._explicitRatioReset?.();
    window.ChartStories?.storyDrawerHide();
  }
  window.ChartStories?.storyDrawerHide();
  window.DeckMusic?.stop?.();
  window.GenreShowcase?.hide?.();
  window.ArtistShowcase?.hide?.();
  const wasRendered = rendered.has(`chart-${i}`);
  await renderSlideChart(i);
  if (i === 8) document.getElementById("chart-8")?._emotionResetAnchor?.();
  if (i === 9) document.getElementById("chart-9")?._explicitTrendReset?.();
  if (i === 10) document.getElementById("chart-10")?._explicitRatioReset?.();
  if (i === 2 && wasRendered) {
    document.getElementById("chart-2")?._genreTrendReplayIntro?.();
  }
}

async function init() {
  await loadData();
  await window.DeckMusic.load();
  window.DeckMusic.indexCharts(chartsData);
  await window.ArtistShowcase?.load?.();
  window.ArtistShowcase?.bind?.();

  window.__onDeckSlide = onSlideChange;
  const start = window.__currentSlideIndex ?? 0;
  await onSlideChange(start);

  window.addEventListener("resize", () => window.ChartRenderers.resizeAllCharts());
}

document.addEventListener("DOMContentLoaded", init);
