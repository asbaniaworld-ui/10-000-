/** Tableau 配色与主题 — 从 palette.json / twb 提取 */
let TABLEAU_PALETTE = {
  main_genres: {},
  artists: {},
  rank_groups: {},
  measures: {},
  top100_mark: "#75a1c7",
};

/** Tableau 10 连续色阶（与 twb palette 名对应） */
const TABLEAU_SEQ = {
  orange: ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#8c2d04"],
  green: ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#005a32"],
  blue: ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
  purple: ["#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#4a1486"],
};

/** Top100 / 五种风格 参考带颜色（twb refline fill-above） */
const REF_BANDS = {
  danceability: [
    { to: 0.4, color: "#f9f3ef" },
    { to: 0.7, color: "#f9e3d4" },
    { to: 1.0, color: "#f3baac" },
  ],
  energy: [
    { to: 0.33, color: "#f7faf0" },
    { to: 0.66, color: "#e8edda" },
    { to: 1.0, color: "#dee8bb" },
  ],
  loudness: [
    { to: -12, color: "#f0f7fa" },
    { to: -6, color: "#ddebf0" },
    { to: 0, color: "#cbe6f0" },
  ],
  tempo: [
    { to: 90, color: "#f0f3fa" },
    { to: 130, color: "#e2e6f0" },
    { to: 220, color: "#d5dbf0" },
  ],
};

const REF_LINES = {
  danceability: [0.4, 0.7],
  energy: [0.33, 0.66],
  loudness: [-12, -6],
  tempo: [90, 130],
};

async function loadTableauPalette() {
  const base = window.__WEB_DATA_BASE || "data/";
  const res = await fetch(`${base}palette.json?v=100`);
  TABLEAU_PALETTE = await res.json();
}

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

function rgbToHex(r, g, b) {
  return `#${[r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
}

function lerpColor(c1, c2, t) {
  const a = hexToRgb(c1);
  const b = hexToRgb(c2);
  return rgbToHex(
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t
  );
}

function seqColor(paletteName, value, min, max, reverse = false) {
  const grad = [...TABLEAU_SEQ[paletteName || "blue"]];
  if (reverse) grad.reverse();
  const t = Math.max(0, Math.min(1, (value - min) / (max - min || 1)));
  const pos = t * (grad.length - 1);
  const i = Math.floor(pos);
  const frac = pos - i;
  if (i >= grad.length - 1) return grad[grad.length - 1];
  return lerpColor(grad[i], grad[i + 1], frac);
}

function genreColor(name) {
  return TABLEAU_PALETTE.main_genres[name] || "#bab0ac";
}

function artistColor(name) {
  return TABLEAU_PALETTE.artists[name] || "#4e79a7";
}

function measureColor(key, value, min, max) {
  const spec = TABLEAU_PALETTE.measures[key];
  const palette = spec?.palette || "blue";
  const reverse = key === "loudness";
  return seqColor(palette, value, min, max, reverse);
}

function blueMeasureColor(value, min, max) {
  return seqColor("blue", value, min, max, false);
}

function fmtNum(n) {
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(n);
}

const GOLDEN_BAND_LABELS = {
  danceability: ["弱律动", "轻微律动", "强律动"],
  energy: ["低能量 舒缓", "中能量 情绪平稳", "高能量 亢奋"],
  loudness: ["低响度 轻柔", "标准流媒体响度 均衡", "高压缩 高响度"],
  tempo: ["慢板 低速", "中速 流行", "快板 高速"],
};

/** 雷达图归一化：与 Tableau 参数区间一致 */
const GOLDEN_NORM = {
  danceability: { min: 0, max: 1 },
  energy: { min: 0, max: 1 },
  loudness: { min: -20, max: -6 },
  tempo: { min: 40, max: 130 },
};

function normGoldenMetric(key, val) {
  const r = GOLDEN_NORM[key] || { min: 0, max: 1 };
  return Math.max(0, Math.min(100, ((val - r.min) / (r.max - r.min || 1)) * 100));
}

function buildMarkAreaBands(key, min, max, withLabels = false) {
  const bands = REF_BANDS[key] || [];
  if (!bands.length) return null;
  const labels = GOLDEN_BAND_LABELS[key] || [];
  let prev = min;
  const data = bands.map((b, i) => {
    const seg = [
      {
        xAxis: prev,
        itemStyle: { color: b.color, opacity: 1 },
        ...(withLabels && labels[i]
          ? {
              label: {
                show: true,
                position: "inside",
                formatter: labels[i],
                color: "#888",
                fontSize: 8,
                fontWeight: "normal",
              },
            }
          : {}),
      },
      { xAxis: Math.min(b.to, max) },
    ];
    prev = b.to;
    return seg;
  });
  return { silent: true, data };
}

function buildRefLines(key) {
  const lines = REF_LINES[key] || [];
  if (!lines.length) return null;
  return {
    silent: true,
    symbol: "none",
    lineStyle: { color: "#898989", type: "dashed", width: 1 },
    label: { show: false },
    data: lines.map((x) => ({ xAxis: x })),
  };
}

window.TableauTheme = {
  loadTableauPalette,
  getPalette: () => TABLEAU_PALETTE,
  genreColor,
  artistColor,
  measureColor,
  blueMeasureColor,
  fmtNum,
  SEQ: TABLEAU_SEQ,
  REF_BANDS,
  GOLDEN_BAND_LABELS,
  GOLDEN_NORM,
  normGoldenMetric,
  buildMarkAreaBands,
  buildRefLines,
};
