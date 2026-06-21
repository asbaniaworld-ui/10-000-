const chartInstances = new Map();

function bindMusic(chart, resolver) {
  if (!window.DeckMusic) return;
  chart.on("click", (params) => {
    if (params.componentType !== "series") return;
    const track = resolver(params);
    if (track) void window.DeckMusic.play(track);
  });
}

function stories() {
  return window.ChartStories?.get() || {};
}

function bindStory(chart, resolver) {
  if (!window.ChartStories) return;
  chart.on("click", (params) => {
    const html = resolver(params);
    if (html) window.ChartStories.storyDrawerPush(html);
  });
}

function initChart(el, option) {
  const prev = chartInstances.get(el.id);
  if (prev) prev.dispose();
  const chart = echarts.init(el, null, {
    renderer: "canvas",
    devicePixelRatio: Math.min(window.devicePixelRatio || 2, 3),
  });
  chart.setOption(option, true);
  chartInstances.set(el.id, chart);
  return chart;
}

function resizeAllCharts() {
  chartInstances.forEach((c) => c.resize());
}

const T = () => window.TableauTheme;

const axis = {
  axisLine: { lineStyle: { color: "#999" } },
  axisTick: { show: false },
  splitLine: { show: false },
  axisLabel: { color: "#444", fontSize: 11, fontFamily: "Arial, sans-serif" },
};

const tip = {
  backgroundColor: "rgba(255,255,255,.96)",
  borderColor: "#ccc",
  borderWidth: 1,
  textStyle: { color: "#222", fontSize: 12 },
  extraCssText: "box-shadow:0 4px 16px rgba(0,0,0,.08);",
};

const GOLDEN_UNITS = {
  danceability: "0–1",
  energy: "0–1",
  loudness: "dB",
  tempo: "BPM",
};

function fmtGoldenLabel(key, val, withUnit = false) {
  let s;
  if (key === "loudness") s = val.toFixed(1);
  else if (key === "tempo") s = String(Math.round(val));
  else s = val.toFixed(2);
  if (withUnit) {
    const u = GOLDEN_UNITS[key];
    if (u) s = `${s} ${u}`;
  }
  return s;
}

/** 1. 各音乐流派市场占有率 — 条形图（web 滚动页） */
function renderGenreMarket(el, data, opts = {}) {
  if (opts.mode === "rose") return renderGenreMarketRose(el, data, opts);
  const items = [...data].sort((a, b) => a.count - b.count);
  const total = items.reduce((s, d) => s + d.count, 0);
  const byGenre = Object.fromEntries(items.map((d) => [d.genre, d]));
  const chart = initChart(el, {
    backgroundColor: "#fff",
    title: {
      text: `曲目计数 · 共 ${T().fmtNum(total)} 条（COUNT track_id）`,
      left: 0,
      top: 0,
      textStyle: { fontSize: 11, fontWeight: "normal", color: "#666" },
    },
    grid: { left: 130, right: 56, top: 28, bottom: 28 },
    tooltip: {
      ...tip,
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (ps) => {
        const p = ps[0];
        const pct = ((p.value / total) * 100).toFixed(1);
        const st = stories().genre_market?.[p.name];
        const extra = st ? `<br/><span style="opacity:.75">${st.headline}：${st.story}</span>` : "";
        return `<b>${p.name}</b><br/>曲目数：${T().fmtNum(p.value)}<br/>占比：${pct}%${extra}`;
      },
    },
    xAxis: { type: "value", splitLine: { lineStyle: { color: "#eee" } }, ...axis },
    yAxis: {
      type: "category",
      data: items.map((d) => d.genre),
      axisLabel: { fontSize: 12, color: "#333" },
      axisLine: { show: true, lineStyle: { color: "#ccc" } },
    },
    series: [
      {
        type: "bar",
        data: items.map((d) => ({
          value: d.count,
          itemStyle: { color: T().genreColor(d.genre) },
          label: {
            show: true,
            position: "right",
            formatter: "{c}",
            color: "#333",
            fontSize: 11,
          },
        })),
        barWidth: 22,
        emphasis: { focus: "series", itemStyle: { shadowBlur: 12, shadowColor: "rgba(0,0,0,.15)" } },
      },
    ],
  });
  if (opts.onGenreHover) {
    chart.on("mouseover", (p) => {
      if (p.componentType === "series" && p.name) opts.onGenreHover(p.name, byGenre[p.name]);
    });
    chart.on("mouseout", () => opts.onGenreHover(null));
  }
  bindStory(chart, (p) => {
    if (p.componentType !== "series") return null;
    const st = stories().genre_market?.[p.name];
    return st
      ? `<div class="sp-title">${p.name}</div><div class="sp-head">${st.headline}</div><p>${st.story}</p><p class="sp-num">${T().fmtNum(p.value)} 首 · ${((p.value / total) * 100).toFixed(1)}%</p>`
      : null;
  });
  return chart;
}

/** 前五流派 + Other 聚合 */
function buildGenreTop5Other(data) {
  const sorted = [...data].sort((a, b) => b.count - a.count);
  const total = sorted.reduce((s, d) => s + d.count, 0);
  const top5 = sorted.slice(0, 5);
  const rest = sorted.slice(5);
  const otherCount = rest.reduce((s, d) => s + d.count, 0);
  const slices = [
    ...top5.map((d) => ({ name: d.genre, value: d.count, genre: d.genre })),
    { name: "Other", value: otherCount, genre: "Other" },
  ].sort((a, b) => b.value - a.value);
  const byGenre = Object.fromEntries(top5.map((d) => [d.genre, d]));
  byGenre.Other = { genre: "Other", count: otherCount, rest };
  return { total, slices, byGenre };
}

/** 1a. 南丁格尔玫瑰图 — Top5 + Other */
function renderGenreMarketRose(el, data, opts = {}) {
  const { total, slices, byGenre } = buildGenreTop5Other(data);

  const chart = initChart(el, {
    backgroundColor: "#fff",
    title: {
      text: `前五流派市场占有率 · 共 ${T().fmtNum(total)} 首`,
      left: "center",
      top: 4,
      textStyle: { fontSize: 12, fontWeight: "normal", color: "#666" },
    },
    tooltip: { show: false },
    series: [
      {
        type: "pie",
        roseType: "area",
        radius: ["14%", "80%"],
        center: ["50%", "54%"],
        startAngle: 90,
        minAngle: 8,
        itemStyle: { borderColor: "#fff", borderWidth: 2 },
        label: {
          show: true,
          minMargin: 8,
          formatter: (p) => {
            const pct = ((p.value / total) * 100).toFixed(1);
            return `{n|${p.name}}\n{p|${pct}%}`;
          },
          rich: {
            n: { fontSize: 12, fontWeight: "bold", color: "#333", lineHeight: 16 },
            p: { fontSize: 10, color: "#666", lineHeight: 14 },
          },
        },
        labelLine: { show: true, length: 12, length2: 16, smooth: true },
        emphasis: { scale: true, scaleSize: 8 },
        data: slices.map((d) => ({
          name: d.name,
          value: d.value,
          itemStyle: {
            color: d.name === "Other" ? "#bab0ac" : T().genreColor(d.genre),
          },
        })),
      },
    ],
  });

  chart.on("click", (p) => {
    if (p.componentType !== "series" || !p.name) return;
    const track = opts.genreTracks?.[p.name] || null;
    if (opts.onGenreClick) opts.onGenreClick(p.name, byGenre[p.name], track);
  });

  chart.getZr().on("click", (e) => {
    if (!e.target && opts.onBlankClick) opts.onBlankClick();
  });

  return chart;
}

/** 2. 流派受欢迎程度变化趋势 — 17 流派折线 */
function genreTrendOrder(data, meta) {
  return (meta?.genre_trend_order || Object.keys(data)).filter((g) => data[g]?.years?.length);
}

function genreTrendNotesFor(genre) {
  if (!genre) return [];
  const st = stories().genre_trend || {};
  const chapter = st.chapter_notes?.[genre];
  if (chapter?.length) return chapter;
  const configured = st.genre_milestones?.[genre] || [];
  return configured.filter((m) => m.kind !== "peak" && !/峰值/.test(m.label || ""));
}

function genreTrendNoteActive(m, genre, highlightYear, highlightKind, displayGenre) {
  if (highlightYear !== m.year) return false;
  if (m.kind === "era") return highlightKind === "era";
  if (m.kind === "peak") return highlightKind === "peak" && genre === displayGenre;
  return highlightKind === "turn" && genre === displayGenre;
}

function renderGenreTrendNotes(notesEl, genre, highlightYear, { interactive = true, highlightKind = null } = {}) {
  if (!notesEl) return;
  const displayGenre = genre || "Pop";
  const items = genreTrendNotesFor(displayGenre);
  if (!items.length) {
    notesEl.innerHTML = "";
    notesEl.style.display = "none";
    return;
  }
  notesEl.style.display = "flex";
  notesEl.innerHTML = items
    .map((m) => {
      const active = genreTrendNoteActive(m, genre, highlightYear, highlightKind, displayGenre);
      const kindCls =
        m.kind === "turn" ? " gt-note--key" : m.kind === "era" ? " gt-note--era" : m.kind === "peak" ? " gt-note--peak" : "";
      return `
    <button type="button" class="gt-note gt-note--y${m.year}${kindCls}${active ? " is-active" : ""}"
      data-genre="${displayGenre}" data-year="${m.year}" data-kind="${m.kind || "turn"}" ${interactive ? "" : "disabled tabindex='-1'"}>
      <span class="gt-note-year">${m.year} 年</span>
      <span class="gt-note-label">${m.label}</span>
      <span class="gt-note-story">${m.story}</span>
    </button>`;
    })
    .join("");
}

function genreTrendHighlightTheme(year, kind) {
  const themes = {
    2005: {
      area: "rgba(201, 162, 39, 0.17)",
      areaWide: "rgba(201, 162, 39, 0.11)",
      line: "rgba(201, 162, 39, 0.62)",
      label: "#a8841a",
    },
    2016: {
      area: "rgba(73, 152, 148, 0.14)",
      areaWide: "rgba(73, 152, 148, 0.09)",
      line: "rgba(73, 152, 148, 0.55)",
      label: "#499894",
    },
    2020: {
      area: "rgba(201, 123, 109, 0.15)",
      areaWide: "rgba(201, 123, 109, 0.11)",
      line: "rgba(201, 123, 109, 0.58)",
      label: "#b85c4f",
    },
    2024: {
      area: "rgba(78, 121, 167, 0.18)",
      areaWide: "rgba(78, 121, 167, 0.12)",
      line: "rgba(78, 121, 167, 0.62)",
      label: "#4e79a7",
    },
  };
  return themes[year] || themes[2016];
}

function fmtAxisK(v) {
  const n = Math.round(Number(v));
  if (n === 0) return "0";
  if (n >= 1000) return `${Math.round(n / 1000)}K`;
  return String(n);
}

function fmtAxisFollowers(v) {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return "";
  if (n >= 1e9) return `${(n / 1e9).toFixed(n >= 1e10 ? 0 : 1)}B`;
  if (n >= 1e6) return `${Math.round(n / 1e6)}M`;
  if (n >= 1e3) return `${Math.round(n / 1e3)}K`;
  return String(Math.round(n));
}

function fmtPopK(v) {
  return `${(Number(v) / 1000).toFixed(2)}K`;
}

function fmtAxisYear(v) {
  return String(Math.round(Number(v)));
}

function fmtPopularityPeak(val) {
  return Number(val).toLocaleString("en-US");
}

function genreTrendPopMax(data, order, sliceYear) {
  let max = 0;
  order.forEach((genre) => {
    const years = data[genre]?.years || [];
    const pops = data[genre]?.popularity || [];
    years.forEach((y, i) => {
      if (y <= sliceYear) max = Math.max(max, pops[i] || 0);
    });
  });
  return max;
}

function genreTrendYAxisMax(dataMax, highlightKind) {
  if (!dataMax) return 65000;
  const headroom = highlightKind === "peak" ? 1.14 : 1.08;
  const padded = dataMax * headroom;
  const step = padded >= 50000 ? 5000 : 1000;
  return Math.ceil(padded / step) * step;
}

function buildGenreTrendOption(data, meta, opts = {}) {
  const normalized =
    typeof opts === "string" || opts === null
      ? { selectedGenre: opts || null }
      : opts;
  const {
    selectedGenre = null,
    highlightYear = null,
    highlightKind = null,
    xMax = 2024,
    throughYear = null,
    introPlaying = false,
    animDurationUpdate = introPlaying ? 140 : 360,
  } = normalized;

  const isEraHighlight = highlightKind === "era" && highlightYear != null;
  const eraEnd = 2024;
  const hlTheme = highlightYear != null ? genreTrendHighlightTheme(highlightYear, highlightKind) : null;
  const sliceYear = throughYear ?? xMax;

  const order = genreTrendOrder(data, meta);
  const popMax = genreTrendPopMax(data, order, sliceYear);
  const yAxisMax = genreTrendYAxisMax(popMax, highlightKind);
  const focusW = (genre) => {
    if (introPlaying || !selectedGenre) return genre === "Pop" || genre === "Rock" ? 2.2 : 1.3;
    if (selectedGenre === "Pop" && genre === "Rock") return 2;
    if (selectedGenre === "Rock" && genre === "Pop") return 2.5;
    return selectedGenre === genre ? 3.2 : 1;
  };

  const series = order.map((genre, idx) => {
    let dimmed = !introPlaying && selectedGenre && selectedGenre !== genre;
    if (selectedGenre === "Pop" && genre === "Rock") dimmed = false;
    if (selectedGenre === "Rock" && genre === "Pop") dimmed = false;
    const opacity = introPlaying
      ? 0.92
      : dimmed
        ? 0.14
        : selectedGenre === "Pop" && genre === "Rock"
          ? 0.75
          : selectedGenre === "Rock" && genre === "Pop"
            ? 0.75
            : 1;

    const s = {
      name: genre,
      type: "line",
      smooth: false,
      symbol: "none",
      showSymbol: false,
      lineStyle: { width: focusW(genre), opacity },
      itemStyle: { color: T().genreColor(genre) },
      emphasis: { focus: "series", lineStyle: { width: 3.5 } },
      data: data[genre].years
        .map((y, i) => [y, data[genre].popularity[i]])
        .filter(([y]) => y <= sliceYear),
      z: selectedGenre === genre ? 3 : 1,
    };

    if (idx === 0 && highlightYear != null && hlTheme) {
      if (isEraHighlight) {
        s.markArea = {
          silent: true,
          itemStyle: { color: hlTheme.areaWide },
          data: [[{ xAxis: highlightYear - 0.35 }, { xAxis: eraEnd + 0.35 }]],
        };
        s.markLine = {
          silent: true,
          symbol: "none",
          lineStyle: { color: hlTheme.line, type: "dashed", width: 1.5 },
          label: {
            show: true,
            formatter: `${highlightYear}`,
            position: "insideEndTop",
            fontSize: 10,
            color: hlTheme.label,
            fontFamily: "IBM Plex Mono, monospace",
          },
          data: [{ xAxis: highlightYear }],
        };
      } else if (selectedGenre) {
        s.markArea = {
          silent: true,
          itemStyle: { color: hlTheme.area },
          data: [[{ xAxis: highlightYear - 0.55 }, { xAxis: highlightYear + 0.55 }]],
        };
      }
    }

    if (!isEraHighlight && selectedGenre === genre && highlightYear && hlTheme) {
      const yi = data[genre].years.indexOf(highlightYear);
      if (yi >= 0) {
        const val = data[genre].popularity[yi];
        const isPeak = highlightKind === "peak";
        s.markPoint = {
          symbol: "circle",
          symbolSize: isPeak ? 14 : 11,
          clip: false,
          itemStyle: {
            color: T().genreColor(genre),
            borderColor: "#fff",
            borderWidth: 2,
            shadowBlur: isPeak ? 8 : 0,
            shadowColor: "rgba(78,121,167,.35)",
          },
          label: {
            show: true,
            formatter: isPeak ? fmtPopularityPeak(val) : String(highlightYear),
            position: isPeak ? "top" : "top",
            distance: isPeak ? 10 : 8,
            fontSize: isPeak ? 11 : 10,
            fontWeight: "bold",
            color: isPeak ? hlTheme.label : "#333",
          },
          data: [{ coord: [highlightYear, val], name: String(highlightYear) }],
        };
        s.clip = false;
        s.markLine = {
          silent: true,
          symbol: "none",
          lineStyle: { color: hlTheme.line, type: "dashed", width: 1 },
          label: { show: false },
          data: [{ xAxis: highlightYear }],
        };
      }
    }

    return s;
  });

  return {
    backgroundColor: "#fff",
    animationDuration: introPlaying && throughYear === 2000 ? 0 : 320,
    animationDurationUpdate: animDurationUpdate,
    animationEasing: "linear",
    animationEasingUpdate: "cubicOut",
    tooltip: {
      ...tip,
      trigger: "axis",
      formatter: (ps) => {
        const lines = ps
          .filter((p) => p.seriesName && !p.seriesName.startsWith("_") && p.value?.[1] != null)
          .sort((a, b) => b.value[1] - a.value[1])
          .slice(0, 8)
          .map((p) => `${p.marker}${p.seriesName}: ${T().fmtNum(p.value[1])}`);
        const year = Math.round(ps[0]?.value?.[0] ?? 0);
        return `<b>${year} 年</b><br/>${lines.join("<br/>")}`;
      },
    },
    legend: { show: false },
    grid: { left: 12, right: 16, top: 40, bottom: 54, containLabel: true },
    dataZoom: introPlaying
      ? [{ type: "inside", xAxisIndex: 0, filterMode: "none", disabled: true }]
      : [
          { type: "inside", xAxisIndex: 0, filterMode: "none" },
          { type: "slider", height: 16, bottom: 6, xAxisIndex: 0 },
        ],
    xAxis: {
      type: "value",
      name: "年份",
      nameLocation: "middle",
      nameGap: 26,
      nameTextStyle: { fontSize: 11, color: "#666", fontFamily: "Arial, sans-serif" },
      min: 2000,
      max: 2024,
      interval: 4,
      splitLine: { show: false },
      axisLine: axis.axisLine,
      axisTick: axis.axisTick,
      axisLabel: {
        ...axis.axisLabel,
        formatter: fmtAxisYear,
        margin: 10,
      },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: yAxisMax,
      name: "Popularity 年度合计（分）",
      nameLocation: "middle",
      nameRotate: 90,
      nameGap: 48,
      nameTextStyle: { fontSize: 11, color: "#666", fontFamily: "Arial, sans-serif" },
      splitLine: { lineStyle: { color: "#eee" } },
      axisLine: axis.axisLine,
      axisTick: axis.axisTick,
      axisLabel: {
        ...axis.axisLabel,
        formatter: fmtAxisK,
        margin: 8,
      },
    },
    series,
  };
}

function setupGenreTrendDeckUI(el, data, meta, chart) {
  const slide = el.closest(".ch2-trend");
  const sidebar = slide?.querySelector(".genre-trend-sidebar");
  const notesEl = slide?.querySelector("#genre-trend-notes");
  const narrativeEl = slide?.querySelector(".gt-narrative");
  if (!slide || !notesEl) return;

  const state = { selected: null, highlightYear: null, highlightKind: null, introDone: false, introPlaying: false };

  const setGtNarrative = (year) => {
    if (!narrativeEl) return;
    const narr = stories().genre_trend?.chapter_narratives || {};
    const html =
      year != null
        ? narr[String(year)] || narr.initial || "在 2000 年代初，Rock 依然是最受欢迎的流派。"
        : narr.initial || "在 2000 年代初，Rock 依然是最受欢迎的流派。";
    narrativeEl.classList.remove("is-enter");
    narrativeEl.classList.add("is-changing");
    window.setTimeout(() => {
      narrativeEl.innerHTML = html;
      narrativeEl.classList.remove("is-changing");
      void narrativeEl.offsetWidth;
      narrativeEl.classList.add("is-enter");
    }, 200);
  };

  const refreshUI = () => {
    renderGenreTrendNotes(notesEl, state.selected, state.highlightYear, {
      interactive: state.introDone,
      highlightKind: state.highlightKind,
    });
  };

  const setIntroLock = (locked) => {
    state.introPlaying = locked;
    sidebar?.classList.toggle("is-intro-disabled", locked);
    if (notesEl) notesEl.style.pointerEvents = locked ? "none" : "";
  };

  const apply = (genre, highlightYear = null, highlightKind = null) => {
    if (state.introPlaying) return;
    state.selected = genre || null;
    state.highlightYear = highlightYear;
    state.highlightKind = highlightYear ? highlightKind : null;
    chart.setOption(
      buildGenreTrendOption(data, meta, {
        selectedGenre: state.selected,
        highlightYear: state.highlightYear,
        highlightKind: state.highlightKind,
        xMax: 2024,
      }),
      { notMerge: true }
    );
    if (state.highlightYear != null) setGtNarrative(state.highlightYear);
    else setGtNarrative(null);
    refreshUI();
  };

  const finishIntro = () => {
    if (state.introDone) return;
    state.introDone = true;
    setIntroLock(false);
    apply(null, null, null);
  };

  const runIntro = () => {
    state.introDone = false;
    state.selected = null;
    state.highlightYear = null;
    state.highlightKind = null;
    setIntroLock(true);
    renderGenreTrendNotes(notesEl, null, null, { interactive: false });

    const introYears = [];
    for (let y = 2000; y <= 2024; y++) introYears.push(y);

    chart.setOption(
      buildGenreTrendOption(data, meta, { throughYear: 2000, introPlaying: true, animDurationUpdate: 0 }),
      { notMerge: true }
    );

    let step = 1;
    const tick = () => {
      if (step >= introYears.length) {
        finishIntro();
        return;
      }
      chart.setOption(
        buildGenreTrendOption(data, meta, {
          throughYear: introYears[step],
          introPlaying: true,
          animDurationUpdate: 130,
        }),
        { notMerge: false }
      );
      step += 1;
      window.setTimeout(tick, 130);
    };
    window.setTimeout(tick, 280);
  };

  if (!slide.dataset.gtBound) {
    slide.dataset.gtBound = "1";

    slide.addEventListener("click", (e) => {
      if (state.introPlaying) return;
      const noteBtn = e.target.closest(".gt-note");
      if (noteBtn && !noteBtn.disabled) {
        e.preventDefault();
        const g = noteBtn.dataset.genre;
        const y = Number(noteBtn.dataset.year);
        const kind = noteBtn.dataset.kind || "turn";
        if (kind === "era") {
          const sameEra = state.highlightKind === "era" && state.highlightYear === y;
          apply(null, sameEra ? null : y, sameEra ? null : "era");
        } else if (kind === "peak") {
          const samePeak = state.selected === g && state.highlightYear === y && state.highlightKind === "peak";
          apply(samePeak ? null : g, samePeak ? null : y, samePeak ? null : "peak");
        } else {
          const sameTurn = state.selected === g && state.highlightYear === y && state.highlightKind === "turn";
          apply(sameTurn ? null : g, sameTurn ? null : y, sameTurn ? null : "turn");
        }
      }
    });
  }

  el._genreTrendApply = apply;
  el._genreTrendReplayIntro = runIntro;
  runIntro();
}

function renderGenreTrend(el, data, meta) {
  const isDeck = !!document.querySelector(".ch2-trend #genre-trend-notes");
  const chart = initChart(
    el,
    buildGenreTrendOption(data, meta, isDeck ? { throughYear: 2000, introPlaying: true } : null)
  );

  if (isDeck) setupGenreTrendDeckUI(el, data, meta, chart);

  bindStory(chart, (p) => {
    if (!p.seriesName || p.seriesName.startsWith("_")) return null;
    const year = Math.round(p.value?.[0] ?? 0);
    const val = p.value?.[1];
    const ms = genreTrendNotesFor(p.seriesName).find((m) => m.year === year);
    if (ms)
      return `<div class="sp-title">${p.seriesName} · ${year}</div><p><strong>${ms.label}</strong> — ${ms.story}</p><p class="sp-num">Popularity 合计：${T().fmtNum(val)} 分</p>`;
    return `<div class="sp-title">${p.seriesName} · ${year}</div><p class="sp-num">Popularity 合计：${T().fmtNum(val)} 分</p>`;
  });
}

/** 3. 粉丝量与艺人热度 */
const ARTIST_SCATTER_FEATURED = ["Taylor Swift", "Bad Bunny", "Drake", "Playboi Carti"];

const FEATURED_LABEL_LAYOUT = {
  "Taylor Swift": { position: "top", distance: 16 },
  "Bad Bunny": { position: "right", distance: 22, offset: [12, -8] },
  "Drake": { position: "left", distance: 22, offset: [-12, 10] },
  "Playboi Carti": { position: "bottom", distance: 16, offset: [0, 10] },
};

const GENRE_LEGEND_SHORT = {
  EasyListening: "Easy",
  TraditionalMusic: "Trad.",
  Electronic: "Electro.",
  Christian: "Christ.",
  Classical: "Class.",
};

function genreRepresentatives(data) {
  const byGenre = {};
  for (const d of data) {
    const g = d.genre;
    if (!byGenre[g] || d.popularity > byGenre[g].popularity) byGenre[g] = d;
  }
  return Object.values(byGenre);
}

function artistScatterBgStyle(isDeck) {
  return {
    size: isDeck ? 2.2 : 2.8,
    opacity: isDeck ? 0.14 : 0.22,
  };
}

function renderArtistScatter(el, data, opts = {}) {
  const featured = new Set(opts.featured || ARTIST_SCATTER_FEATURED);
  const isDeck = typeof opts.onArtistClick === "function";
  const genres = [...new Set(data.map((d) => d.genre))].sort();
  const maxTracks = Math.max(...data.map((d) => d.tracks), 1);
  const reps = genreRepresentatives(data);
  const repSet = new Set(reps.map((d) => d.artist));
  const bgStyle = artistScatterBgStyle(isDeck);
  const xMax = Math.max(...data.map((d) => d.followers), 1e6);
  const xLogMax = Math.pow(10, Math.ceil(Math.log10(xMax * 1.25)));

  const pointSize = (tracks, tier = "bg") => {
    if (tier === "bg") return bgStyle.size;
    const t = Math.sqrt(tracks || 1);
    if (tier === "rep") return Math.max(6, Math.min(14, t * 1.2));
    return Math.max(9, Math.min(22, t * 1.9));
  };

  const series = genres.map((genre) => ({
    name: genre,
    type: "scatter",
    symbolSize: (v) => pointSize(v[2], "bg"),
    itemStyle: { color: T().genreColor(genre), opacity: bgStyle.opacity },
    data: data
      .filter((d) => d.genre === genre && !featured.has(d.artist) && !repSet.has(d.artist))
      .map((d) => [d.followers, d.popularity, d.tracks, d.artist]),
  }));

  const genreRepPoints = reps.filter((d) => !featured.has(d.artist));
  if (genreRepPoints.length) {
    series.push({
      name: "_genreReps",
      type: "scatter",
      symbolSize: (v) => pointSize(v[2], "rep"),
      itemStyle: { opacity: 0.95 },
      data: genreRepPoints.map((d) => ({
        value: [d.followers, d.popularity, d.tracks, d.artist],
        itemStyle: {
          color: T().genreColor(d.genre),
          borderColor: "#fff",
          borderWidth: 1.5,
        },
      })),
      z: 8,
      legendHoverLink: false,
    });
  }

  const featuredPoints = data.filter((d) => featured.has(d.artist));
  if (featuredPoints.length) {
    series.push({
      name: "_featured",
      type: "scatter",
      symbolSize: (v) => pointSize(v[2], "feat"),
      itemStyle: { opacity: 1 },
      data: featuredPoints.map((d) => {
        const layout = FEATURED_LABEL_LAYOUT[d.artist] || { position: "top", distance: 10 };
        return {
          value: [d.followers, d.popularity, d.tracks, d.artist],
          itemStyle: {
            color: T().genreColor(d.genre),
            borderColor: "#1a1a1a",
            borderWidth: 2,
            shadowBlur: 12,
            shadowColor: "rgba(0,0,0,.2)",
          },
          label: {
            show: true,
            position: layout.position,
            distance: layout.distance,
            offset: layout.offset || [0, 0],
            formatter: `{n|${d.artist}}\n{p|${fmtPopK(d.popularity)}}`,
            rich: {
              n: { fontWeight: "bold", fontSize: 10, color: "#222", lineHeight: 15 },
              p: { fontSize: 9, color: T().genreColor(d.genre), lineHeight: 13, fontWeight: 600 },
            },
            backgroundColor: "rgba(255,255,255,.94)",
            padding: [4, 6],
            borderRadius: 4,
            borderColor: "#ccc",
            borderWidth: 1,
          },
        };
      }),
      labelLayout: { moveOverlap: "shiftY", hideOverlap: true },
      z: 10,
      silent: false,
      legendHoverLink: false,
      tooltip: { show: false },
    });
  }

  const yMax = Math.max(...data.map((d) => d.popularity), 1200);
  const yCeil = Math.min(12000, Math.ceil((yMax * 1.06) / 1000) * 1000);

  const sizeMarks = [1, 20, 40, 60, 80, maxTracks].filter((v, i, a) => a.indexOf(v) === i).slice(-4);

  const chart = initChart(el, {
    backgroundColor: "#fff",
    tooltip: {
      ...tip,
      formatter: (p) => {
        if (p.seriesName === "_featured") return "";
        const artist = p.data?.value?.[3] ?? p.data?.[3];
        if (!artist) return "";
        const genre =
          p.seriesName === "_genreReps"
            ? data.find((d) => d.artist === artist)?.genre
            : p.seriesName;
        const val = p.data?.value ?? p.data;
        const st = stories().artist_scatter?.[artist];
        const extra = st ? `<br/><span style="opacity:.75">${st.event || ""} · ${st.story}</span>` : "";
        const hint = isDeck ? "点击查看艺人详情" : "点击播放代表曲";
        const tag = p.seriesName === "_genreReps" ? " · 流派代表" : "";
        return `<b>${artist}</b> (${genre})${tag}<br/>粉丝量：${T().fmtNum(val[0])}<br/>热度：${fmtPopK(val[1])}<br/>曲目：${val[2]} 首${extra}<br/><span style="opacity:.55">${hint}</span>`;
      },
    },
    legend: {
      type: "scroll",
      orient: "horizontal",
      top: 2,
      left: 56,
      right: 12,
      height: 22,
      itemWidth: 7,
      itemHeight: 7,
      itemGap: 10,
      textStyle: { fontSize: 7.5, color: "#555" },
      pageIconSize: 8,
      pageTextStyle: { fontSize: 7 },
      formatter: (name) => GENRE_LEGEND_SHORT[name] || name,
      data: genres,
    },
    grid: { left: 54, right: 18, top: 46, bottom: 50, containLabel: true },
    xAxis: {
      ...axis,
      type: "log",
      logBase: 10,
      min: 100,
      max: xLogMax,
      name: "Total Artist Followers",
      nameLocation: "middle",
      nameGap: 28,
      nameTextStyle: { fontSize: 10, color: "#666" },
      splitLine: { lineStyle: { color: "#eee" } },
      axisLabel: { ...axis.axisLabel, margin: 10, formatter: fmtAxisFollowers },
    },
    yAxis: {
      ...axis,
      type: "value",
      name: "Avg Artist Popularity (K)",
      nameTextStyle: { fontSize: 10, color: "#666" },
      nameGap: 8,
      splitNumber: 4,
      min: 0,
      max: yCeil,
      splitLine: { lineStyle: { color: "#eee" } },
      axisLabel: { ...axis.axisLabel, margin: 8, formatter: fmtAxisK },
    },
    graphic: isDeck
      ? [
          {
            type: "group",
            right: 16,
            bottom: 14,
            children: [
              {
                type: "text",
                style: {
                  text: "气泡大小 · 曲目数",
                  fontSize: 7.5,
                  fill: "#888",
                  fontFamily: "Arial",
                },
                top: 0,
                left: 0,
              },
              ...sizeMarks.map((n, i) => ({
                type: "circle",
                shape: { r: Math.max(2, Math.min(6, Math.sqrt(n) * 0.5)) },
                left: i * 22,
                top: 12,
                style: { fill: "#aaa", opacity: 0.55 },
              })),
              ...sizeMarks.map((n, i) => ({
                type: "text",
                left: i * 22 + 8,
                top: 9,
                style: { text: String(n), fontSize: 7, fill: "#666", fontFamily: "Arial" },
              })),
            ],
          },
        ]
      : [
          {
            type: "group",
            left: 56,
            bottom: 48,
            children: [
              {
                type: "text",
                style: { text: "CNT(Track Id)", fontSize: 8, fill: "#888", fontFamily: "Arial" },
                top: 0,
                left: 0,
              },
              ...sizeMarks.map((n, i) => ({
                type: "circle",
                shape: { r: Math.max(2, Math.min(7, Math.sqrt(n) * 0.55)) },
                left: 3,
                top: 14 + i * 14,
                style: { fill: "#bbb", opacity: 0.5 },
              })),
              ...sizeMarks.map((n, i) => ({
                type: "text",
                left: 16,
                top: 10 + i * 14,
                style: { text: String(n), fontSize: 7, fill: "#666", fontFamily: "Arial" },
              })),
            ],
          },
        ],
    series,
  });

  const readPoint = (params) => {
    const raw = params.data?.value ?? params.data;
    if (!raw?.[3]) return null;
    const genreRow = data.find((d) => d.artist === raw[3]);
    return {
      artist: raw[3],
      point: {
        followers: raw[0],
        popularity: raw[1],
        tracks: raw[2],
        genre: genreRow?.genre || params.seriesName,
      },
    };
  };

  if (isDeck) {
    chart.on("click", (params) => {
      if (params.componentType !== "series") return;
      const hit = readPoint(params);
      if (!hit) return;
      opts.onArtistClick(hit.artist, hit.point);
    });
  } else {
    bindMusic(chart, (p) => {
      const artist = p.data?.value?.[3] ?? p.data?.[3];
      if (!artist) return null;
      return window.DeckMusic?.lookupArtist(artist);
    });
    bindStory(chart, (p) => {
      const name = p.data?.value?.[3] ?? p.data?.[3];
      if (!name) return null;
      const val = p.data?.value ?? p.data;
      const st = stories().artist_scatter?.[name];
      return st
        ? `<div class="sp-title">${name}</div><p>${st.story}</p><p class="sp-num">${st.event || ""}</p>`
        : `<div class="sp-title">${name}</div><p class="sp-num">粉丝 ${T().fmtNum(val[0])} · 热度 ${fmtPopK(val[1])}</p>`;
    });
  }

  return chart;
}

/** 小倍数矩阵：统一网格 + 参考带 + 圆点 */
const ROW_SHORT = {
  danceability: "Danceability",
  energy: "Energy",
  loudness: "Loud",
  tempo: "Tempo",
};

function goldenRowTitleText(row, compact) {
  const name =
    compact && row.key === "danceability" ? "Dance" : ROW_SHORT[row.key] || row.label;
  const unit = GOLDEN_UNITS[row.key] || "";
  return unit ? `{n|${name}}\n{u|${unit}}` : name;
}

function goldenRowTitleStyle(compact) {
  return {
    rich: {
      n: {
        fontSize: compact ? 8 : 9,
        color: "#666",
        fontWeight: "normal",
        fontFamily: "var(--mono, monospace)",
        lineHeight: compact ? 12 : 13,
      },
      u: {
        fontSize: compact ? 6 : 7,
        color: "#999",
        fontWeight: "normal",
        fontFamily: "var(--mono, monospace)",
        lineHeight: compact ? 10 : 11,
      },
    },
  };
}

function goldenCellRect(layout, ci, ri) {
  const { plotLeft, plotTop, cellW, cellH, colGap, rowGap } = layout;
  return {
    left: plotLeft + ci * (cellW + colGap),
    top: plotTop + ri * (cellH + rowGap),
    w: cellW,
    h: cellH,
  };
}

function buildGoldenMatrixGraphic(layout, colCount, rowCount, width, height) {
  if (!width || !height) return [];
  const pxX = (pct) => (pct / 100) * width;
  const pxY = (pct) => (pct / 100) * height;
  const { plotLeft, plotTop, plotW, plotH, colGap, rowGap } = layout;
  const elements = [];

  for (let ci = 1; ci < colCount; ci += 1) {
    const prev = goldenCellRect(layout, ci - 1, 0);
    const x = pxX(prev.left + prev.w + colGap / 2);
    elements.push({
      type: "line",
      shape: { x1: x, y1: pxY(plotTop), x2: x, y2: pxY(plotTop + plotH) },
      style: { stroke: "#e4e4e4", lineWidth: 1 },
      silent: true,
      z: 0,
    });
  }

  for (let ri = 1; ri < rowCount; ri += 1) {
    const prev = goldenCellRect(layout, 0, ri - 1);
    const y = pxY(prev.top + prev.h + rowGap / 2);
    elements.push({
      type: "line",
      shape: { x1: pxX(plotLeft), y1: y, x2: pxX(plotLeft + plotW), y2: y },
      style: { stroke: "#ececec", lineWidth: 1 },
      silent: true,
      z: 0,
    });
  }

  return elements;
}

function buildGoldenMatrixOption({
  cols,
  rows,
  colLabels,
  colSubLabels,
  getValue,
  getColor,
  bandLabels = false,
  isHighlight,
  highlightStyle,
  compact = false,
  hostWidth,
  hostHeight,
}) {
  const colCount = cols.length;
  const rowCount = rows.length;

  const labelColPct = compact ? 10 : 14.5;
  const headerPct = compact ? 7.5 : 9;
  const padRightPct = compact ? 1.2 : 1;
  const padBottomPct = 1.2;
  const colGap = compact ? 0.35 : 0.45;
  const rowGap = compact ? 0.85 : 1.0;

  const plotLeft = labelColPct + 0.6;
  const plotTop = headerPct + (colSubLabels?.length ? 1.2 : 0);
  const plotW = 100 - plotLeft - padRightPct;
  const plotH = 100 - plotTop - padBottomPct;
  const cellW = (plotW - colGap * (colCount - 1)) / colCount;
  const cellH = (plotH - rowGap * (rowCount - 1)) / rowCount;

  const layout = { plotLeft, plotTop, plotW, plotH, cellW, cellH, colGap, rowGap, labelColPct, headerPct };

  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];
  const dotSize = compact ? (colCount > 5 ? 10 : 12) : 14;
  const hiDotSize = compact ? 13 : 16;

  cols.forEach((col, ci) => {
    rows.forEach((row, ri) => {
      const idx = ci * rowCount + ri;
      const box = goldenCellRect(layout, ci, ri);

      grids.push({
        left: `${box.left}%`,
        top: `${box.top}%`,
        width: `${box.w}%`,
        height: `${box.h}%`,
        show: false,
      });

      xAxes.push({
        gridIndex: idx,
        type: "value",
        min: row.min,
        max: row.max,
        show: false,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      });

      yAxes.push({
        gridIndex: idx,
        type: "value",
        min: 0,
        max: 1,
        show: false,
      });

      const val = getValue(col, row);
      const color = getColor(col, row, val);
      const hi = isHighlight?.(col, row, val);
      const hiTheme = highlightStyle || {
        color: "#e15759",
        label: "#b40426",
        border: "#e15759",
        labelBg: "rgba(255,235,235,0.96)",
        shadow: "rgba(225,87,89,0.4)",
      };

      series.push({
        type: "scatter",
        xAxisIndex: idx,
        yAxisIndex: idx,
        symbolSize: hi ? hiDotSize : dotSize,
        z: hi ? 20 : 10,
        itemStyle: {
          color,
          borderColor: hi ? hiTheme.border : "#fff",
          borderWidth: hi ? 2.5 : 1.5,
          shadowBlur: hi ? 6 : 0,
          shadowColor: hi ? hiTheme.shadow : "transparent",
        },
        label: {
          show: true,
          formatter: () => fmtGoldenLabel(row.key, val, true),
          position: "top",
          fontSize: hi ? 9 : compact ? 7 : 8,
          color: hi ? hiTheme.label : "#333",
          fontWeight: "bold",
          distance: 5,
          align: "center",
          backgroundColor: hi ? hiTheme.labelBg : "rgba(255,255,255,0.92)",
          padding: [1, 4],
          borderRadius: 2,
          borderColor: hi ? hiTheme.border : "transparent",
          borderWidth: hi ? 1 : 0,
        },
        markArea: T().buildMarkAreaBands(row.key, row.min, row.max, bandLabels && ci === 0),
        markLine: T().buildRefLines(row.key),
        data: [[val, 0.5]],
      });
    });
  });

  const titleFs = compact ? (colCount > 5 ? 8 : 9) : 10;
  const colTitles = colLabels.map((label, ci) => {
    const box = goldenCellRect(layout, ci, 0);
    return {
      text: label,
      left: `${box.left + box.w / 2}%`,
      top: `${headerPct * 0.42}%`,
      textAlign: "center",
      textVerticalAlign: "middle",
      textStyle: { fontSize: titleFs, fontWeight: "bold", color: "#333" },
    };
  });

  const subTitles = (colSubLabels || []).map((label, ci) => {
    if (!label) return null;
    const box = goldenCellRect(layout, ci, 0);
    return {
      text: label,
      left: `${box.left + box.w / 2}%`,
      top: `${headerPct * 0.78}%`,
      textAlign: "center",
      textVerticalAlign: "middle",
      textStyle: { fontSize: 7, color: "#aaa", fontWeight: "normal" },
    };
  }).filter(Boolean);

  const rowTitles = rows.map((row, ri) => {
    const box = goldenCellRect(layout, 0, ri);
    return {
      text: goldenRowTitleText(row, compact),
      left: "0.4%",
      width: labelColPct,
      top: `${box.top + box.h / 2}%`,
      textAlign: "right",
      textVerticalAlign: "middle",
      textStyle: goldenRowTitleStyle(compact),
    };
  });

  return {
    grids,
    xAxes,
    yAxes,
    series,
    title: [...colTitles, ...subTitles, ...rowTitles],
    graphic: buildGoldenMatrixGraphic(layout, colCount, rowCount, hostWidth, hostHeight),
    layout,
    rowCount,
    colCount,
  };
}

/** 4. Top100 黄金配比 — 4 行 × 3 列（对齐 Tableau 小倍数） */
function renderTop100Golden(el, data, meta) {
  const groups = meta?.golden_groups || Object.keys(data.groups);
  const rows = meta?.golden_rows || [];
  const shortGroups = groups.map((g) =>
    g === "Middle(101-9000)" ? "Middle" : g === "Edge (9000-10000)" ? "Edge" : g
  );
  const built = buildGoldenMatrixOption({
    cols: groups,
    rows,
    colLabels: shortGroups,
    getValue: (grp, row) => data.groups[grp][row.key],
    getColor: () => T().getPalette()?.top100_mark || "#75a1c7",
    bandLabels: false,
    compact: false,
    hostWidth: el.clientWidth,
    hostHeight: el.clientHeight,
  });

  const chart = initChart(el, {
    backgroundColor: "#fff",
    title: built.title,
    graphic: built.graphic,
    tooltip: {
      ...tip,
      formatter: (p) => {
        const ci = Math.floor(p.seriesIndex / built.rowCount);
        const ri = p.seriesIndex % built.rowCount;
        const grp = groups[ci];
        const row = rows[ri];
        const val = data.groups[grp][row.key];
        const st = stories().top100_golden?.[grp];
        const extra = st && grp === "Top 100" ? `<br/><span style="opacity:.75">${st.story}</span>` : "";
        return `<b>${grp}</b><br/>${row.label}: <b>${fmtGoldenLabel(row.key, val, true)}</b>${extra}`;
      },
    },
    grid: built.grids,
    xAxis: built.xAxes,
    yAxis: built.yAxes,
    series: built.series,
  });
  bindStory(chart, (p) => {
    const ci = Math.floor(p.seriesIndex / built.rowCount);
    const ri = p.seriesIndex % built.rowCount;
    const grp = groups[ci];
    const row = rows[ri];
    const st = stories().top100_golden?.[grp];
    if (st && grp === "Top 100")
      return `<div class="sp-title">Top 100 · ${row.label}</div><p>${st.story}</p>`;
    return `<div class="sp-title">${grp}</div><p>${row.label}：${fmtGoldenLabel(row.key, data.groups[grp][row.key], true)}</p>`;
  });
}

/** 5. Top10 歌手黄金配比 — 4 行 × 7 列 */
const BILLIE_ARTIST = "Billie Eilish";
const BILLIE_HIGHLIGHT_KEYS = new Set(["loudness", "energy", "tempo"]);
const CH5_BILLIE_COLOR = "#4e79a7";
const CH5_TOP100_COLOR = "#e15759";
const CH5_BILLIE_HI = {
  color: CH5_BILLIE_COLOR,
  label: "#2166ac",
  border: CH5_BILLIE_COLOR,
  labelBg: "rgba(230,240,250,0.92)",
  shadow: "rgba(78,121,167,0.32)",
};

function renderTop10Golden(el, data, meta, top100Golden) {
  const sorted = [...data].sort((a, b) => b.followers - a.followers);
  const artists = sorted.map((d) => d.artist);
  const shortName = {
    "Taylor Swift": "Taylor",
    "The Weeknd": "Weeknd",
    "Billie Eilish": "Billie",
    "Bad Bunny": "Bad Bunny",
    Drake: "Drake",
    Coldplay: "Coldplay",
    "Imagine Dragons": "Imagine",
  };
  const rows = meta?.top10_golden_rows || meta?.golden_rows || [];
  const built = buildGoldenMatrixOption({
    cols: artists,
    rows,
    colLabels: artists.map((a) => shortName[a] || a.split(" ").pop()),
    getValue: (artist, row) => sorted.find((d) => d.artist === artist)?.[row.key] ?? 0,
    getColor: (artist, row, val) => {
      if (artist === BILLIE_ARTIST && BILLIE_HIGHLIGHT_KEYS.has(row.key)) {
        return CH5_BILLIE_COLOR;
      }
      return T().blueMeasureColor(val, row.min, row.max);
    },
    isHighlight: (artist, row) =>
      artist === BILLIE_ARTIST && BILLIE_HIGHLIGHT_KEYS.has(row.key),
    highlightStyle: CH5_BILLIE_HI,
    compact: true,
    hostWidth: el.clientWidth,
    hostHeight: el.clientHeight,
  });

  const chart = initChart(el, {
    backgroundColor: "#fff",
    title: built.title,
    graphic: built.graphic,
    tooltip: {
      ...tip,
      formatter: (p) => {
        const ci = Math.floor(p.seriesIndex / built.rowCount);
        const ri = p.seriesIndex % built.rowCount;
        const d = sorted[ci];
        const row = rows[ri];
        const val = d[row.key];
        const st = stories().top10_golden?.[d.artist];
        const genre = sorted.find((x) => x.artist === d.artist)?.genre;
        const isHi = d.artist === BILLIE_ARTIST && BILLIE_HIGHLIGHT_KEYS.has(row.key);
        const top100 = top100Golden?.groups?.["Top 100"];
        const ref =
          top100 && isHi
            ? `<br/><span style="color:${CH5_TOP100_COLOR};opacity:.85">Top 100：${fmtGoldenLabel(row.key, top100[row.key], true)}</span>`
            : "";
        const outlier =
          isHi
            ? `<br/><span style="color:${CH5_BILLIE_COLOR}">⚠ 偏离黄金公式</span>`
            : st?.outlier === row.key
              ? `<br/><span style="color:${CH5_TOP100_COLOR}">⚠ ${st.story}</span>`
              : st
                ? `<br/><span style="opacity:.75">${st.story}</span>`
                : "";
        return `<b>${d.artist}</b>${genre ? ` · ${genre}` : ""}<br/>${row.label}: <b>${fmtGoldenLabel(row.key, val, true)}</b>${ref}${outlier}`;
      },
    },
    grid: built.grids,
    xAxis: built.xAxes,
    yAxis: built.yAxes,
    series: built.series,
  });
  bindStory(chart, (p) => {
    const ci = Math.floor(p.seriesIndex / built.rowCount);
    const d = sorted[ci];
    const st = stories().top10_golden?.[d.artist];
    return st
      ? `<div class="sp-title">${d.artist}</div><p>${st.story}</p>`
      : null;
  });
  bindMusic(chart, (p) => {
    if (p.componentType !== "series" || !p.data) return null;
    const ci = Math.floor(p.seriesIndex / built.rowCount);
    const d = sorted[ci];
    return d ? window.DeckMusic?.lookupArtist(d.artist) : null;
  });
  return chart;
}

/** 5 章侧栏：Billie vs Top 100 物理指标雷达 */
function renderBillieRadarCompare(el, top10Data, top100Golden) {
  const billie = top10Data.find((d) => d.artist === BILLIE_ARTIST);
  const top100 = top100Golden?.groups?.["Top 100"];
  if (!billie || !top100) return null;

  const axes = [
    { key: "loudness", name: "响度 Loud" },
    { key: "danceability", name: "Danceability" },
    { key: "energy", name: "能量 Energy" },
    { key: "tempo", name: "速度 Tempo" },
  ];
  const billieVals = axes.map((a) => T().normGoldenMetric(a.key, billie[a.key]));
  const top100Vals = axes.map((a) => T().normGoldenMetric(a.key, top100[a.key]));

  return initChart(el, {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,.96)",
      borderWidth: 1,
      borderColor: "#ddd",
      textStyle: { color: "#222", fontSize: 11 },
      formatter: (p) => {
        const src = p.seriesName === "Billie" ? billie : top100;
        const lines = axes
          .map((a) => `${a.name}：${fmtGoldenLabel(a.key, src[a.key])}`)
          .join("<br/>");
        return `<b>${p.seriesName}</b><br/>${lines}`;
      },
    },
    legend: {
      bottom: 0,
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 12,
      textStyle: { fontSize: 9, color: "#555" },
      data: ["Top 100", "Billie"],
    },
    radar: {
      center: ["50%", "46%"],
      radius: "70%",
      splitNumber: 4,
      axisName: {
        color: "#555",
        fontSize: 9,
        lineHeight: 14,
        padding: [2, 6],
        formatter: (name) => {
          const key = axes.find((a) => a.name === name)?.key;
          if (key && BILLIE_HIGHLIGHT_KEYS.has(key)) {
            return `{hi|${name}}`;
          }
          return name;
        },
        rich: { hi: { color: CH5_BILLIE_COLOR, fontWeight: "bold" } },
      },
      axisNameGap: 10,
      splitLine: { lineStyle: { color: "rgba(0,0,0,.06)" } },
      splitArea: { show: true, areaStyle: { color: ["rgba(255,255,255,.4)", "rgba(0,0,0,.015)"] } },
      axisLine: { lineStyle: { color: "rgba(0,0,0,.1)" } },
      indicator: axes.map((a) => ({
        name: a.name,
        max: 100,
        axisLabel: { show: false },
      })),
    },
    series: [
      {
        type: "radar",
        symbol: "circle",
        symbolSize: 5,
        data: [
          {
            name: "Top 100",
            value: top100Vals,
            lineStyle: { color: CH5_TOP100_COLOR, width: 2 },
            areaStyle: { color: "rgba(225,87,89,0.07)" },
            itemStyle: { color: CH5_TOP100_COLOR },
          },
          {
            name: "Billie",
            value: billieVals,
            lineStyle: { color: CH5_BILLIE_COLOR, width: 2.5 },
            areaStyle: { color: "rgba(78,121,167,0.07)" },
            itemStyle: { color: CH5_BILLIE_COLOR, borderColor: "#fff", borderWidth: 1 },
            emphasis: {
              lineStyle: { width: 3 },
            },
          },
        ],
      },
    ],
  });
}

/** 热力图格内：当年新发 X 首 · Popularity 均值 Y 分（与色块颜色一致） */
function fmtHeatCell(c) {
  return `${c.track_count}首\n${Math.round(c.popularity)}分`;
}

function fmtHeatFollowers(n) {
  if (n >= 1e6) {
    const m = n / 1e6;
    if (m >= 100) return `${Math.round(m)}M`;
    if (m >= 10) return `${m.toFixed(1)}M`;
    return `${m.toFixed(2)}M`;
  }
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
  return String(Math.round(n));
}

function heatLabelColor(popularity, popMin, popMax) {
  const t = (popularity - popMin) / (popMax - popMin || 1);
  return t >= 0.52 ? "#fff" : "#1a1a1a";
}

const BILLIE_DEBUT_YEAR = 2016;

function sortHeatRowsByYear(rows, cellMap, year) {
  return [...rows].sort((a, b) => {
    const ca = cellMap.get(`${a.artist}|${year}`);
    const cb = cellMap.get(`${b.artist}|${year}`);
    const sa = ca?.popularity ?? -1;
    const sb = cb?.popularity ?? -1;
    if (sb !== sa) return sb - sa;
    return (cb?.track_count ?? 0) - (ca?.track_count ?? 0);
  });
}

function heatYAxisLabelFormatter(rows) {
  return (name, idx) => {
    const row = rows[idx];
    if (!row) return name;
    const showGenre = idx === 0 || rows[idx - 1].genre !== row.genre;
    const artistStyle = row.artist === BILLIE_ARTIST ? "billie" : "artist";
    if (showGenre) {
      return `{genre|${row.genre}}\n{${artistStyle}|${name}}`;
    }
    return `{${artistStyle}|${name}}`;
  };
}

function buildHeatmapSeriesData(rows, years, cellMap, popMin, popMax, opts = {}) {
  const { sortYear = null, billieFocusYear = null } = opts;
  const heatData = [];
  rows.forEach((row, yi) => {
    years.forEach((year, xi) => {
      const c = cellMap.get(`${row.artist}|${year}`);
      if (!c) return;
      const billieSelected =
        row.artist === BILLIE_ARTIST &&
        billieFocusYear != null &&
        year === billieFocusYear;
      const billieDefault =
        row.artist === BILLIE_ARTIST &&
        billieFocusYear == null &&
        year === BILLIE_DEBUT_YEAR;
      const highlight = billieSelected || billieDefault;
      const colActive = sortYear != null && year === sortYear;
      heatData.push({
        id: `${row.artist}|${year}`,
        value: [xi, yi, c.popularity, c.pop_sum],
        genre: row.genre,
        artist: row.artist,
        year,
        followers: c.followers,
        popularity: c.popularity,
        pop_sum: c.pop_sum,
        track_count: c.track_count,
        itemStyle: {
          borderColor: highlight ? CH5_BILLIE_COLOR : colActive ? "#bbb" : "#f0f0f0",
          borderWidth: highlight ? 2.5 : colActive ? 1.2 : 0.5,
          shadowBlur: highlight ? 8 : 0,
          shadowColor: highlight ? "rgba(78,121,167,0.35)" : "transparent",
        },
        label: {
          show: true,
          formatter: fmtHeatCell(c),
          fontSize: highlight ? 8 : 7,
          fontWeight: "bold",
          lineHeight: 11,
          color: heatLabelColor(c.popularity, popMin, popMax),
        },
      });
    });
  });
  return heatData;
}

function heatmapSortNote(sortYear) {
  if (sortYear == null) return "";
  return `${sortYear} 年 · 按 Popularity 均值(分)降序 · 双击空白恢复`;
}

function billieHeatStoryHtml(year, cell, opts = {}) {
  const y = Number(year);
  const st = stories().top10_heatmap?.[BILLIE_ARTIST];
  const yearSt = st?.by_year?.[String(y)];
  const storyText = yearSt?.story || st?.story || "";
  const tag = yearSt?.title ? ` · ${yearSt.title}` : "";
  const stats =
    cell?.track_count != null
      ? `<p class="sp-num">${y} 年 · 新发 ${cell.track_count} 首 · Popularity 均值 ${Math.round(cell.popularity)} 分</p>`
      : "";
  const rank =
    opts.sortYear === y && opts.rank != null
      ? `<p class="sp-num">${y} 年排序：第 ${opts.rank} / ${opts.totalRows}</p>`
      : "";
  return `<div class="sp-title">${BILLIE_ARTIST}${tag} · ${y}</div><p>${storyText}</p>${stats}${rank}`;
}

/** 6. Top10 歌手热度变化 — 按发行年：色=Popularity 均值，字=新发曲数+热度分 */
function renderTop10Heatmap(el, data) {
  const baseRows = [...data.rows];
  const { years, cells } = data;
  const cellMap = new Map(cells.map((c) => [`${c.artist}|${c.year}`, c]));
  const popValues = cells.map((c) => c.popularity);
  const popMin = popValues.length ? Math.min(...popValues) : 87;
  const popMax = popValues.length ? Math.max(...popValues) : 100;

  const heatState = { sortYear: null, billieFocusYear: null };

  const getRows = () =>
    heatState.sortYear != null
      ? sortHeatRowsByYear(baseRows, cellMap, heatState.sortYear)
      : baseRows;

  const getHeatData = () =>
    buildHeatmapSeriesData(getRows(), years, cellMap, popMin, popMax, {
      sortYear: heatState.sortYear,
      billieFocusYear: heatState.billieFocusYear,
    });

  const xAxisLabelFormatter = (val) => {
    if (heatState.sortYear != null && val === String(heatState.sortYear)) {
      return `{yr|${val}}`;
    }
    return val;
  };

  const chart = initChart(el, {
    backgroundColor: "#fff",
    animationDurationUpdate: 650,
    animationEasingUpdate: "cubicInOut",
    title: {
      text: "",
      right: 52,
      top: 2,
      textAlign: "right",
      textStyle: { fontSize: 8, color: "#888", fontWeight: "normal" },
    },
    tooltip: {
      ...tip,
      formatter: (p) => {
        const d = p.data;
        const hi =
          d.artist === BILLIE_ARTIST
            ? `<br/><span style="color:${CH5_BILLIE_COLOR}">点击 Billie 色块 · 按该年重排行</span>`
            : "";
        const folM = (d.followers / 1e6).toFixed(0);
        return `<b>${d.artist}</b> · ${d.genre}<br/>${d.year} 年 · 新发 <b>${d.track_count}</b> 首<br/>Popularity 均值：<b>${Math.round(d.popularity)}</b> 分（0–100）<br/>Popularity 合计：<b>${d.pop_sum}</b> 分 · 曲目加总<br/>艺人粉丝量：${folM}M${hi}`;
      },
    },
    grid: { left: 96, right: 56, top: 28, bottom: 38, containLabel: false },
    xAxis: {
      type: "category",
      data: years.map((y) => `${y}`),
      name: "Release Date 年",
      nameLocation: "middle",
      nameGap: 26,
      nameTextStyle: { fontSize: 9, color: "#666" },
      axisLabel: {
        fontSize: 8,
        color: "#666",
        interval: 0,
        hideOverlap: true,
        formatter: xAxisLabelFormatter,
        rich: {
          yr: { color: CH5_BILLIE_COLOR, fontWeight: "bold" },
        },
      },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: "#ccc" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      data: baseRows.map((r) => r.artist),
      inverse: true,
      axisLabel: {
        width: 88,
        overflow: "truncate",
        fontSize: 9,
        formatter: heatYAxisLabelFormatter(baseRows),
        rich: {
          genre: { fontSize: 7, color: "#999", fontWeight: "bold", lineHeight: 12 },
          artist: { fontSize: 9, color: "#333", lineHeight: 14 },
          billie: { fontSize: 9, color: CH5_BILLIE_COLOR, fontWeight: "bold", lineHeight: 14 },
        },
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitArea: { show: true, areaStyle: { color: ["#fafafa", "#fff"] } },
    },
    visualMap: {
      type: "continuous",
      dimension: 2,
      seriesIndex: 0,
      min: popMin,
      max: popMax,
      calculable: false,
      orient: "vertical",
      right: 4,
      top: "middle",
      itemWidth: 12,
      itemHeight: 110,
      name: "Popularity",
      nameLocation: "end",
      nameGap: 8,
      nameTextStyle: { fontSize: 8, color: "#888" },
      text: ["高 100", "低 0"],
      textStyle: { fontSize: 8, color: "#666" },
      inRange: {
        color: ["#fff5eb", "#fee6ce", "#fdae6b", "#e6550d", "#a63603"],
      },
    },
    series: [
      {
        type: "heatmap",
        id: "top10-heat",
        universalTransition: true,
        data: getHeatData(),
        animationDurationUpdate: 650,
        animationEasingUpdate: "cubicInOut",
        emphasis: {
          itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,.25)" },
          label: { fontSize: 9 },
        },
      },
    ],
  });

  const applyHeatSort = () => {
    const rows = getRows();
    chart.setOption({
      title: { text: heatmapSortNote(heatState.sortYear) },
      yAxis: {
        data: rows.map((r) => r.artist),
        axisLabel: { formatter: heatYAxisLabelFormatter(rows) },
      },
      xAxis: {
        axisLabel: { formatter: xAxisLabelFormatter },
      },
      series: [
        {
          data: getHeatData(),
          animationDurationUpdate: 650,
          animationEasingUpdate: "cubicInOut",
        },
      ],
    });
  };

  const slide = el.closest(".ch6-heat");

  const syncTimeline = (year) => {
    if (!slide || year == null) return;
    slide.querySelectorAll("[data-ch6-year]").forEach((item) => {
      item.classList.toggle("is-tl-active", item.dataset.ch6Year === String(year));
    });
  };

  const pushBillieHeatStory = (year) => {
    const y = Number(year);
    const cell = cellMap.get(`${BILLIE_ARTIST}|${y}`);
    const rank =
      heatState.sortYear === y
        ? getRows().findIndex((r) => r.artist === BILLIE_ARTIST) + 1
        : null;
    const html = billieHeatStoryHtml(y, cell, {
      sortYear: heatState.sortYear,
      rank,
      totalRows: baseRows.length,
    });
    if (html) window.ChartStories?.storyDrawerPush(html);
  };

  const heatSortByYear = (year) => {
    const y = Number(year);
    const hasCell = years.includes(y) && cellMap.has(`${BILLIE_ARTIST}|${y}`);
    if (hasCell) {
      heatState.sortYear = y;
      heatState.billieFocusYear = y;
      applyHeatSort();
    }
    syncTimeline(y);
    pushBillieHeatStory(y);
  };

  const heatSortReset = () => {
    heatState.sortYear = null;
    heatState.billieFocusYear = null;
    applyHeatSort();
    syncTimeline(BILLIE_DEBUT_YEAR);
  };

  chart.on("click", (params) => {
    if (params.componentType !== "series" || !params.data) return;
    if (params.data.artist !== BILLIE_ARTIST) return;
    heatSortByYear(params.data.year);
  });

  chart.getZr().on("dblclick", (e) => {
    if (e.target) return;
    heatSortReset();
  });

  el._heatSortByYear = heatSortByYear;
  el._heatSortReset = heatSortReset;
  syncTimeline(BILLIE_DEBUT_YEAR);

  return chart;
}

/** 6. 五种风格 — 4 指标列，Y=Popularity，五色叠加 */
function styleLegendLabel(artist, styleLabels) {
  const tag = styleLabels?.[artist];
  if (!tag) return artist;
  const short = {
    "Billie Eilish": "Billie",
    "Linkin Park": "Linkin Park",
    "Mrs. GREEN APPLE": "Mrs. GA",
    "Taylor Swift": "Taylor",
    "The Weeknd": "Weeknd",
  };
  const name = short[artist] || artist;
  return `${name} · ${tag}`;
}

function renderStyleDistribution(el, data, meta) {
  const artists = meta?.style_artists || Object.keys(data);
  const styleLabels = meta?.style_labels || {};
  const metrics = meta?.style_metrics || [
    { key: "danceability", label: "Danceability", min: 0, max: 1 },
    { key: "energy", label: "Energy", min: 0, max: 1 },
    { key: "tempo", label: "Tempo", min: 40, max: 220 },
    { key: "loudness", label: "Loudness", min: -20, max: 0 },
  ];
  const cols = metrics.length;
  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];

  metrics.forEach((m, ci) => {
    const idx = ci;
    grids.push({
      left: `${(ci / cols) * 100 + 2}%`,
      top: "14%",
      width: `${100 / cols - 3}%`,
      height: "76%",
      containLabel: true,
    });
    xAxes.push({
      gridIndex: idx,
      type: "value",
      min: m.min,
      max: m.max,
      name: m.label,
      nameLocation: "middle",
      nameGap: 24,
      nameTextStyle: { fontSize: 11, fontWeight: "bold" },
      axisLabel: { fontSize: 9 },
      splitLine: { lineStyle: { color: "#eee" } },
      axisLine: { lineStyle: { color: "#999" } },
    });
    yAxes.push({
      gridIndex: idx,
      type: "value",
      min: 65,
      max: 105,
      show: ci === 0,
      name: ci === 0 ? "Popularity" : "",
      nameGap: 8,
      nameTextStyle: { fontSize: 10 },
      axisLabel: { fontSize: 9 },
      splitLine: { lineStyle: { color: "#eee" } },
    });

    artists.forEach((artist, ai) => {
      const tracks = data[artist] || [];
      const s = {
        name: artist,
        type: "scatter",
        xAxisIndex: idx,
        yAxisIndex: idx,
        symbolSize: 7,
        itemStyle: { color: T().artistColor(artist), opacity: 0.72 },
        data: tracks.map((t) => [t[m.key], t.popularity, t.track]),
      };
      if (ai === 0) {
        s.markArea = T().buildMarkAreaBands(m.key, m.min, m.max);
        s.markLine = T().buildRefLines(m.key);
      }
      series.push(s);
    });
  });

  const chart = initChart(el, {
    backgroundColor: "#fff",
    legend: {
      top: 4,
      left: "center",
      itemGap: 14,
      itemWidth: 10,
      itemHeight: 10,
      data: artists,
      formatter: (name) => styleLegendLabel(name, styleLabels),
      textStyle: { fontSize: 9, color: "#444" },
    },
    tooltip: {
      ...tip,
      trigger: "item",
      formatter: (p) => {
        const tag = styleLabels[p.seriesName];
        const genreLine = tag ? `<br/>流派：${tag}` : "";
        return `<b>${p.seriesName}</b>${genreLine}<br/>${p.data[2] || ""}<br/>Popularity: ${p.data[1]}<br/><span style="opacity:.55">点击播放</span>`;
      },
    },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    series,
  });
  bindMusic(chart, (p) => {
    if (p.componentType !== "series" || !p.data?.[2]) return null;
    const artist = p.seriesName;
    const hit = (data[artist] || []).find((t) => t.track === p.data[2]);
    return hit
      ? { track: hit.track, artist, track_id: hit.track_id, preview_url: hit.preview_url }
      : null;
  });
}

/** 8. 情绪象限 */
const EMOTION_ANCHOR_ID = "0tMSssfxAL2oV8Vri0mFHE";

function findEmotionAnchor(data) {
  const billie = data.filter((d) => d.artist === BILLIE_ARTIST);
  if (!billie.length) return null;
  return billie.reduce((best, d) => {
    const score = d.energy + d.valence;
    const bestScore = best.energy + best.valence;
    return score < bestScore ? d : best;
  }, billie[0]);
}

function emotionAnchorStoryHtml(anchor) {
  const st = stories().emotion_quadrant?.[BILLIE_ARTIST];
  return `<div class="sp-title">${anchor.track}</div><p>${st?.quadrant || "左下"} · ${st?.story || ""}</p><p class="sp-num">Energy ${anchor.energy} · Valence ${anchor.valence}</p>`;
}

function emotionQuadrantExtents(data) {
  let maxEnergy = 0;
  let maxValence = 0;
  data.forEach((d) => {
    if (d.energy > maxEnergy) maxEnergy = d.energy;
    if (d.valence > maxValence) maxValence = d.valence;
  });
  const ceilStep = (v) => Math.ceil(v / 0.05) * 0.05;
  return {
    energyMax: Math.max(0.5, ceilStep(maxEnergy)),
    valenceMax: Math.max(0.5, ceilStep(maxValence)),
  };
}

const emotionAxisLabel = {
  fontSize: 9,
  color: "#666",
  fontFamily: "Arial, sans-serif",
  margin: 8,
  formatter: (v) => Number(v).toFixed(2),
};

const emotionAxisTick = {
  show: true,
  length: 4,
  lineStyle: { color: "#bbb" },
};

const emotionSplitLine = {
  show: true,
  lineStyle: { color: "#efefef", width: 1 },
};

function renderEmotionQuadrant(el, data) {
  const artists = ["Taylor Swift", "Billie Eilish"];
  const anchor = findEmotionAnchor(data);
  const anchorId = anchor?.track_id || EMOTION_ANCHOR_ID;
  const slide = el.closest(".ch8-emotion");
  const aside = slide?.querySelector(".ch8-aside");
  const emotionState = { anchorActive: false };

  aside?.classList.remove("is-visible");
  aside?.setAttribute("aria-hidden", "true");

  const mapPoint = (d) => ({
    value: [d.valence, d.energy],
    track: d.track,
    track_id: d.track_id,
    artist: d.artist,
    isAnchor: d.track_id === anchorId,
  });

  const buildArtistSeries = () =>
    artists.map((a) => ({
      name: a,
      type: "scatter",
      symbolSize: a === BILLIE_ARTIST ? 6 : 7,
      itemStyle: {
        color: T().artistColor(a),
        opacity: a === BILLIE_ARTIST ? 0.48 : 0.55,
      },
      emphasis: {
        focus: "self",
        scale: 1.5,
        itemStyle: { opacity: 0.95, shadowBlur: 6, shadowColor: "rgba(0,0,0,.2)" },
      },
      data: data.filter((d) => d.artist === a).map(mapPoint),
    }));

  const buildAnchorSeries = (active) => ({
    name: "Billie · 左下锚点",
    type: "effectScatter",
    symbolSize: active ? 20 : 0,
    showLegendSymbol: false,
    legendHoverLink: false,
    z: 10,
    rippleEffect: active
      ? { brushType: "stroke", scale: 2.6, period: 4 }
      : { brushType: "stroke", scale: 0, period: 0 },
    itemStyle: {
      color: CH5_BILLIE_COLOR,
      borderColor: "#fff",
      borderWidth: 2,
      shadowBlur: active ? 14 : 0,
      shadowColor: "rgba(78,121,167,0.5)",
    },
    label: {
      show: active,
      formatter: anchor?.track || "",
      position: "right",
      distance: 8,
      fontSize: 9,
      fontWeight: "bold",
      color: CH5_BILLIE_COLOR,
      fontStyle: "italic",
    },
    data: active && anchor
      ? [
          {
            value: [anchor.valence, anchor.energy],
            track: anchor.track,
            track_id: anchor.track_id,
            artist: anchor.artist,
            isAnchor: true,
          },
        ]
      : [],
  });

  const markLineSeries = {
    type: "line",
    markLine: {
      silent: true,
      symbol: "none",
      lineStyle: { color: "#e15759", type: "dashed", width: 1.5 },
      label: { show: false },
      data: [{ xAxis: 0.5 }, { yAxis: 0.5 }],
    },
    data: [],
  };
  const markAreaSeries = {
    type: "scatter",
    silent: true,
    symbol: "rect",
    symbolSize: 0,
    markArea: {
      silent: true,
      itemStyle: { color: "rgba(78,121,167,0.04)" },
      data: [[{ xAxis: 0, yAxis: 0 }, { xAxis: 0.5, yAxis: 0.5 }]],
    },
    data: [],
  };

  const { energyMax, valenceMax } = emotionQuadrantExtents(data);

  let chart;
  const setAnchorActive = (active) => {
    emotionState.anchorActive = active;
    aside?.classList.toggle("is-visible", active);
    aside?.setAttribute("aria-hidden", active ? "false" : "true");
    chart.setOption({
      series: [
        ...buildArtistSeries(),
        buildAnchorSeries(active),
        markLineSeries,
        markAreaSeries,
      ],
    });
  };

  chart = initChart(el, {
    backgroundColor: "#fff",
    animationDurationUpdate: 480,
    tooltip: {
      ...tip,
      confine: true,
      formatter: (p) => {
        if (!p.data?.value) return "";
        const [v, e] = p.data.value;
        const anchorTag = p.data.isAnchor
          ? `<br/><span style="color:${CH5_BILLIE_COLOR}">左下锚点 · 点击高亮</span>`
          : "";
        return `${p.seriesName}<br/>Valence ${(+v).toFixed(3)} · Energy ${(+e).toFixed(3)}<br/>${p.data.track || ""}${anchorTag}<br/><span style="opacity:.55">点击播放</span>`;
      },
    },
    legend: { top: 4, data: artists, textStyle: { fontSize: 11 } },
    grid: { left: 62, right: 18, top: 44, bottom: 58, containLabel: true },
    xAxis: {
      type: "value",
      min: 0,
      max: valenceMax,
      interval: 0.05,
      name: "最大值 Valence",
      nameLocation: "middle",
      nameGap: 34,
      nameTextStyle: { fontSize: 11, color: "#555", fontWeight: 600 },
      axisLine: { lineStyle: { color: "#999" } },
      axisTick: emotionAxisTick,
      axisLabel: emotionAxisLabel,
      splitLine: emotionSplitLine,
    },
    yAxis: {
      type: "value",
      min: 0,
      max: energyMax,
      interval: 0.05,
      name: "最大值 Energy",
      nameLocation: "middle",
      nameGap: 46,
      nameTextStyle: { fontSize: 11, color: "#555", fontWeight: 600 },
      axisLine: { lineStyle: { color: "#999" } },
      axisTick: emotionAxisTick,
      axisLabel: emotionAxisLabel,
      splitLine: emotionSplitLine,
    },
    series: [
      ...buildArtistSeries(),
      buildAnchorSeries(false),
      markLineSeries,
      markAreaSeries,
    ],
  });

  chart.on("click", (params) => {
    if (params.componentType !== "series" || !params.data?.track_id) return;
    if (params.data.track_id === anchorId) {
      setAnchorActive(true);
    }
  });

  chart.getZr().on("click", (e) => {
    if (!e.target && emotionState.anchorActive) {
      setAnchorActive(false);
      window.ChartStories?.storyDrawerHide?.();
    }
  });

  bindMusic(chart, (p) => {
    if (p.componentType !== "series" || !p.data?.track) return null;
    return {
      track: p.data.track,
      track_id: p.data.track_id,
      artist: p.data.artist || p.seriesName,
    };
  });

  el._emotionAnchorId = anchorId;
  el._emotionResetAnchor = () => setAnchorActive(false);
  return chart;
}

/** 8. 文化叛逆 — 分面气泡（Circle + size by explicit） */
function explicitBubbleSize(count, maxCount) {
  if (!count) return 6;
  return Math.max(7, Math.min(34, (count / maxCount) * 32 + 7));
}

function explicitTrendPeaks(data, genres) {
  const peaks = {};
  genres.forEach((g) => {
    const counts = data[g]?.counts || [];
    peaks[g] = counts.length ? Math.max(...counts) : 0;
  });
  return peaks;
}

function normalizeFocusGenres(opts = {}) {
  if (opts.focusGenres instanceof Set) return opts.focusGenres;
  if (opts.focusGenre) return new Set([opts.focusGenre]);
  return new Set();
}

function buildExplicitTrendOption(data, meta, opts = {}) {
  const focusGenres = normalizeFocusGenres(opts);
  const hasFocus = focusGenres.size > 0;
  const genres = meta?.explicit_trend_genres || Object.keys(data);
  const rowCount = genres.length;
  const peaks = explicitTrendPeaks(data, genres);
  let maxCount = 1;
  genres.forEach((g) => {
    if (peaks[g] > maxCount) maxCount = peaks[g];
  });
  const yMax = Math.max(300, Math.ceil(maxCount / 100) * 100);
  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];
  const topReserve = 14;
  const bottomReserve = 14;
  const facetGap = 0.9;
  const facetH = (100 - topReserve - bottomReserve - facetGap * (rowCount - 1)) / rowCount;

  genres.forEach((genre, ri) => {
    const idx = ri;
    const isLit = hasFocus && focusGenres.has(genre);
    const focused = !hasFocus || isLit;
    const isLast = ri === rowCount - 1;
    grids.push({
      left: 122,
      right: 18,
      top: `${topReserve + ri * (facetH + facetGap)}%`,
      height: `${facetH}%`,
      containLabel: isLast,
    });
    xAxes.push({
      gridIndex: idx,
      type: "value",
      min: 1999.5,
      max: 2025.8,
      interval: 4,
      name: isLast ? "发行年份" : "",
      nameLocation: "middle",
      nameGap: 32,
      nameTextStyle: { fontSize: 10, color: "#555" },
      axisLabel: {
        show: isLast,
        fontSize: 10,
        color: "#555",
        margin: 10,
        formatter: (v) => String(Math.round(v)),
      },
      axisLine: { show: true, lineStyle: { color: "#ccc" } },
      axisTick: { show: isLast, length: 4 },
      splitLine: { show: false },
    });
    yAxes.push({
      gridIndex: idx,
      type: "value",
      min: 0,
      max: yMax,
      interval: 100,
      name: genre,
      nameLocation: "middle",
      nameGap: 56,
      nameTextStyle: {
        fontSize: 10,
        fontWeight: hasFocus ? (focused ? 700 : 500) : 600,
        color: T().genreColor(genre),
        opacity: hasFocus ? (focused ? 1 : 0.35) : 1,
      },
      axisLabel: {
        show: ri === 0,
        fontSize: 9,
        color: "#666",
        margin: 8,
        formatter: (v) => (v > 0 && v <= yMax ? `${v}` : v === 0 ? "0" : ""),
      },
      splitLine: { lineStyle: { color: "#f0f0f0", type: "dashed" } },
      axisLine: { show: ri === 0, lineStyle: { color: "#ddd" } },
      axisTick: { show: ri === 0 },
    });

    const years = data[genre]?.years || [];
    const counts = data[genre]?.counts || [];
    const peak = peaks[genre];
    const baseOpacity = hasFocus ? (isLit ? 0.95 : 0.12) : 0.92;
    series.push({
      name: genre,
      type: "scatter",
      xAxisIndex: idx,
      yAxisIndex: idx,
      clip: true,
      z: isLit ? 4 : 1,
      symbolSize: (val) => explicitBubbleSize(val[1], maxCount),
      itemStyle: {
        color: T().genreColor(genre),
        opacity: baseOpacity,
        borderColor: isLit ? "#fff" : "transparent",
        borderWidth: isLit ? 1.5 : 0,
      },
      emphasis: {
        scale: 1.12,
        focus: hasFocus ? "none" : "self",
        itemStyle: { opacity: 1, shadowBlur: 8, shadowColor: "rgba(0,0,0,.15)" },
      },
      label: {
        show: true,
        formatter: (p) =>
          p.data[1] === peak && (!hasFocus || focusGenres.has(genre)) ? String(p.data[1]) : "",
        fontSize: 10,
        fontWeight: "600",
        color: T().genreColor(genre),
        position: "top",
        distance: 8,
      },
      labelLayout: { hideOverlap: true, moveOverlap: "shiftY" },
      data: years.map((y, i) => [y, counts[i]]),
    });
  });

  return {
    backgroundColor: "#fff",
    animationDurationUpdate: 320,
    tooltip: {
      ...tip,
      trigger: "item",
      formatter: (p) => {
        const storyPeaks = stories().explicit_trend?.peaks || [];
        const hit = storyPeaks.find((x) => x.genre === p.seriesName && x.year === p.data[0]);
        const extra = hit ? `<br/><span style="opacity:.75">${hit.story}</span>` : "";
        return `<b>${p.seriesName}</b><br/>${p.data[0]} 年 · <b>${p.data[1]}</b> 首 Explicit${extra}`;
      },
    },
    legend: { show: false },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    series,
  };
}

function setupExplicitTrendDeckUI(el, chart, data, meta) {
  const slide = el.closest(".ch9-explicit");
  if (!slide || slide.dataset.ch9Bound) return;
  slide.dataset.ch9Bound = "1";
  const activeGenres = new Set();
  let chartFocusGenre = null;

  const syncCards = () => {
    slide.classList.toggle("has-genre-focus", activeGenres.size > 0);
    slide.querySelectorAll(".ch9-peak-card").forEach((card) => {
      card.classList.toggle("is-active", activeGenres.has(card.dataset.genre));
    });
  };

  const applyChart = () => {
    chart.setOption(buildExplicitTrendOption(data, meta, { focusGenre: chartFocusGenre }), {
      replaceMerge: ["series", "yAxis"],
    });
  };

  const addFocus = (genre) => {
    if (!genre) return;
    activeGenres.add(genre);
    chartFocusGenre = genre;
    syncCards();
    applyChart();
  };

  const resetFocus = () => {
    activeGenres.clear();
    chartFocusGenre = null;
    syncCards();
    applyChart();
  };

  slide.querySelectorAll(".ch9-peak-card[data-genre]").forEach((card) => {
    card.addEventListener("click", () => addFocus(card.dataset.genre));
  });

  chart.on("click", (params) => {
    if (params.componentType !== "series" || !params.seriesName) return;
    addFocus(params.seriesName);
  });

  chart.getZr().on("click", (e) => {
    if (!e.target) resetFocus();
  });

  slide.querySelector(".deck-text")?.addEventListener("click", (e) => {
    if (e.target.closest(".ch9-peak-card")) return;
    resetFocus();
  });

  el._explicitTrendFocus = addFocus;
  el._explicitTrendReset = resetFocus;
}

function renderExplicitTrend(el, data, meta) {
  const isDeck = !!el.closest(".ch9-explicit");
  const chart = initChart(el, buildExplicitTrendOption(data, meta));
  if (isDeck) setupExplicitTrendDeckUI(el, chart, data, meta);
  bindStory(chart, (p) => {
    const storyPeaks = stories().explicit_trend?.peaks || [];
    const hit = storyPeaks.find((x) => x.genre === p.seriesName && x.year === p.data[0]);
    return hit
      ? `<div class="sp-title">${hit.genre} · ${hit.year}</div><p>${hit.story}</p><p class="sp-num">${hit.value} 首 Explicit</p>`
      : `<div class="sp-title">${p.seriesName} · ${p.data[0]}</div><p class="sp-num">${p.data[1]} 首 Explicit</p>`;
  });
  return chart;
}

/** 9. Explicit 占比 — 叛逆悖论 */
const EXPLICIT_PARADOX_GENRE = "Rock";
const EXPLICIT_RATIO_FOCUS = new Set(["Rock", "R&B", "Metal", "Latin", "HipHop"]);

function explicitRatioGenreLabel(genre) {
  if (genre === "TraditionalMusic") return "Traditional";
  return genre.replace(/([a-z])([A-Z])/g, "$1 $2");
}

function buildExplicitRatioOption(data, opts = {}) {
  const focusGenre = opts.focusGenre ?? null;
  const hasFocus = !!focusGenre;
  const barFromZero = !!opts.barFromZero;
  const animateIn = !!opts.animateIn;
  const animateInstant = !!opts.animateInstant;
  const items = [...data].sort((a, b) => a.ratio - b.ratio);
  const rockItem = items.find((d) => d.genre === EXPLICIT_PARADOX_GENRE);
  const rbItem = items.find((d) => d.genre === "R&B");
  const showParadox = focusGenre === EXPLICIT_PARADOX_GENRE && !barFromZero;

  return {
    backgroundColor: "#fff",
    animation: animateIn,
    animationDuration: animateIn ? 720 : 0,
    animationDurationUpdate: animateInstant ? 0 : animateIn ? 720 : 160,
    animationEasing: animateIn ? "cubicOut" : "linear",
    grid: { left: 132, right: 58, top: 32, bottom: 40, containLabel: false },
    title: {
      text: "SUM(explicit) / COUNT(track_id) · 按 Main Genres",
      left: 0,
      top: 0,
      textStyle: { fontSize: 10, fontWeight: "normal", color: "#888" },
    },
    tooltip: {
      ...tip,
      formatter: (p) => {
        const st = stories().explicit_ratio?.[p.name];
        const extra = st ? `<br/><span style="opacity:.75">${st.story}</span>` : "";
        const tag =
          showParadox && p.name === EXPLICIT_PARADOX_GENRE
            ? `<br/><span style="color:#e15759">★ 行业悖论</span>`
            : "";
        return `<b>${explicitRatioGenreLabel(p.name)}</b>${tag}<br/>${p.data.explicit} / ${p.data.total} 首 Explicit<br/>占比：<b>${p.value.toFixed(2)}%</b>${extra}`;
      },
    },
    xAxis: {
      type: "value",
      min: 0,
      max: 72,
      name: "Explicit 占比（%）",
      nameLocation: "middle",
      nameGap: 28,
      nameTextStyle: { fontSize: 10, color: "#666" },
      axisLabel: { formatter: "{value}%", fontSize: 10, color: "#555" },
      splitLine: { lineStyle: { color: "#eee", type: "dashed" } },
      ...axis,
    },
    yAxis: {
      type: "category",
      data: items.map((d) => d.genre),
      axisLabel: {
        fontSize: 11,
        color: "#333",
        formatter: (g) => {
          const label = explicitRatioGenreLabel(g);
          if (hasFocus && focusGenre === g) {
            if (g === EXPLICIT_PARADOX_GENRE) return `{rock|${label}}`;
            return `{focus|${label}}`;
          }
          return hasFocus ? `{muted|${label}}` : label;
        },
        rich: {
          rock: { fontWeight: "bold", color: "#e15759" },
          focus: { fontWeight: "700", color: "#222" },
          muted: { fontWeight: "normal", color: "#666", opacity: 0.85 },
        },
      },
      axisLine: { lineStyle: { color: "#ddd" } },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        barWidth: 15,
        barCategoryGap: "32%",
        data: items.map((d) => {
          const isRock = d.genre === EXPLICIT_PARADOX_GENRE;
          const isLit = hasFocus && focusGenre === d.genre;
          const baseOpacity = hasFocus ? (isLit ? 1 : 0.16) : 1;
          return {
            value: barFromZero ? 0 : d.ratio,
            explicit: d.explicit,
            total: d.total,
            itemStyle: {
              color: T().genreColor(d.genre),
              opacity: baseOpacity,
              borderColor: showParadox && isRock ? "#e15759" : isLit ? "#fff" : "transparent",
              borderWidth: showParadox && isRock ? 2 : isLit ? 1 : 0,
              shadowBlur: showParadox && isRock ? 6 : isLit ? 8 : 0,
              shadowColor:
                showParadox && isRock
                  ? "rgba(225,87,89,.25)"
                  : isLit
                    ? "rgba(0,0,0,.12)"
                    : "transparent",
            },
            label: {
              show: !barFromZero,
              position: d.ratio >= 18 ? "insideRight" : "right",
              distance: d.ratio >= 18 ? 6 : 4,
              formatter: () => {
                const pct = `${d.ratio.toFixed(2)}%`;
                return showParadox && isRock ? `${pct}  悖论` : pct;
              },
              fontSize: showParadox && isRock ? 11 : 10,
              fontWeight: showParadox && isRock ? "bold" : isLit ? "600" : hasFocus ? "normal" : "500",
              color: d.ratio >= 18 ? "#fff" : "#333",
              opacity: hasFocus && !isLit ? 0.35 : 1,
            },
          };
        }),
        emphasis: {
          focus: hasFocus ? "none" : "series",
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,.12)" },
        },
        markLine:
          showParadox && rockItem
            ? {
                silent: true,
                symbol: "none",
                lineStyle: { color: "#ff9d9a", type: "dashed", width: 1.5, opacity: 0.85 },
                label: {
                  formatter: `Rock ${rockItem.ratio.toFixed(2)}%`,
                  fontSize: 9,
                  color: "#e15759",
                  position: "insideEndTop",
                },
                data: [{ xAxis: rockItem.ratio }],
              }
            : undefined,
      },
    ],
    graphic:
      showParadox && rbItem && rockItem
        ? [
            {
              type: "text",
              right: 8,
              bottom: 6,
              style: {
                text: `Rock 仅为 R&B 的 ${((rockItem.ratio / rbItem.ratio) * 100).toFixed(0)}%`,
                font: "9px monospace",
                fill: "#666",
                textAlign: "right",
              },
            },
          ]
        : [],
  };
}

function setupExplicitRatioDeckUI(el, chart, data) {
  const slide = el.closest(".ch10-paradox");
  if (!slide || slide.dataset.ch10Bound) return;
  slide.dataset.ch10Bound = "1";
  const activeGenres = new Set();
  let chartFocusGenre = null;
  let barsAnimatedIn = false;

  const syncCards = () => {
    slide.classList.toggle("has-genre-focus", activeGenres.size > 0);
    slide.querySelectorAll(".ch10-paradox-card").forEach((card) => {
      card.classList.toggle("is-active", activeGenres.has(card.dataset.genre));
    });
  };

  const applyChart = (chartOpts = {}) => {
    chart.setOption(
      buildExplicitRatioOption(data, {
        focusGenre: chartFocusGenre,
        ...chartOpts,
      }),
      { replaceMerge: ["series", "yAxis", "graphic"] }
    );
  };

  const addFocus = (genre) => {
    if (!genre) return;
    activeGenres.add(genre);
    chartFocusGenre = genre;
    syncCards();

    if (!barsAnimatedIn) {
      barsAnimatedIn = true;
      applyChart({ barFromZero: true, animateInstant: true });
      requestAnimationFrame(() => {
        requestAnimationFrame(() => applyChart({ animateIn: true }));
      });
    } else {
      applyChart({ animateInstant: true });
    }
  };

  const resetFocus = () => {
    activeGenres.clear();
    chartFocusGenre = null;
    barsAnimatedIn = false;
    syncCards();
    applyChart({ animateInstant: true });
  };

  slide.querySelectorAll(".ch10-paradox-card[data-genre]").forEach((card) => {
    card.addEventListener("click", () => addFocus(card.dataset.genre));
  });

  chart.on("click", (p) => {
    if (p.componentType !== "series" || !p.name) return;
    addFocus(p.name);
  });

  chart.getZr().on("click", (e) => {
    if (!e.target) resetFocus();
  });

  slide.querySelector(".deck-text")?.addEventListener("click", (e) => {
    if (e.target.closest(".ch10-paradox-card")) return;
    resetFocus();
  });

  el._explicitRatioFocus = addFocus;
  el._explicitRatioReset = resetFocus;
}

function renderExplicitRatio(el, data) {
  const isDeck = !!el.closest(".ch10-paradox");
  const chart = initChart(el, buildExplicitRatioOption(data));
  if (isDeck) setupExplicitRatioDeckUI(el, chart, data);

  chart.on("click", (p) => {
    if (isDeck || p.componentType !== "series" || !p.name) return;
    const st = stories().explicit_ratio?.[p.name];
    if (st) {
      window.ChartStories?.storyDrawerPush(
        `<div class="sp-title">${explicitRatioGenreLabel(p.name)} · ${p.value.toFixed(2)}%</div><p>${st.story}</p>`
      );
    }
  });

  bindStory(chart, (p) => {
    const st = stories().explicit_ratio?.[p.name];
    return st
      ? `<div class="sp-title">${explicitRatioGenreLabel(p.name)} · ${p.value.toFixed(2)}%</div><p>${st.story}</p>`
      : `<div class="sp-title">${explicitRatioGenreLabel(p.name)}</div><p class="sp-num">${p.value.toFixed(2)}% · ${p.data.explicit}/${p.data.total} 首</p>`;
  });
  return chart;
}

const RENDERERS = {
  genre_market: (el, charts) =>
    renderGenreMarket(el, charts.genre_market, window.__genreMarketOpts || {}),
  genre_trend: (el, charts) => renderGenreTrend(el, charts.genre_trend, charts.meta),
  artist_scatter: (el, charts) =>
    renderArtistScatter(el, charts.artist_scatter, window.__artistScatterOpts || {}),
  top100_golden: (el, charts) => renderTop100Golden(el, charts.top100_golden, charts.meta),
  top10_golden: (el, charts) =>
    renderTop10Golden(el, charts.top10_golden, charts.meta, charts.top100_golden),
  top10_heatmap: (el, charts) => renderTop10Heatmap(el, charts.top10_heatmap),
  style_distribution: (el, charts) =>
    renderStyleDistribution(el, charts.style_distribution, charts.meta),
  emotion_quadrant: (el, charts) => renderEmotionQuadrant(el, charts.emotion_quadrant),
  explicit_trend: (el, charts) => renderExplicitTrend(el, charts.explicit_trend, charts.meta),
  explicit_ratio: (el, charts) => renderExplicitRatio(el, charts.explicit_ratio),
};

async function renderChart(chartKey, containerId, chartsData) {
  await window.TableauTheme.loadTableauPalette();
  await window.ChartStories?.loadChartStories();
  const el = document.getElementById(containerId);
  if (!el || !RENDERERS[chartKey]) return;
  RENDERERS[chartKey](el, chartsData);
}

window.ChartRenderers = {
  renderChart,
  resizeAllCharts,
  renderBillieRadarCompare,
  renderGenreMarket,
  renderGenreMarketRose,
};
