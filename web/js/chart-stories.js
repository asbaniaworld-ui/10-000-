/** 图表叙事 — 左侧抽屉，点击数据点后推入 */
let CHART_STORIES = {};

async function loadChartStories() {
  if (Object.keys(CHART_STORIES).length) return CHART_STORIES;
  try {
    const base = window.__WEB_DATA_BASE || "data/";
    const res = await fetch(`${base}chart_stories.json?v=121`);
    CHART_STORIES = await res.json();
  } catch (e) {
    console.warn("[chart-stories] load failed", e);
    CHART_STORIES = {};
  }
  return CHART_STORIES;
}

function drawer() {
  return document.getElementById("story-drawer");
}

function storyDrawerPush(html) {
  const el = drawer();
  if (!el) return;
  el.innerHTML = `<button class="sd-close" type="button" aria-label="关闭">×</button>${html}`;
  el.classList.add("is-on");
  el.setAttribute("aria-hidden", "false");
  el.querySelector(".sd-close")?.addEventListener("click", storyDrawerHide);
}

function storyDrawerHide() {
  const el = drawer();
  if (!el) return;
  el.classList.remove("is-on");
  el.setAttribute("aria-hidden", "true");
  setTimeout(() => {
    if (!el.classList.contains("is-on")) el.innerHTML = "";
  }, 480);
}

window.ChartStories = {
  loadChartStories,
  storyDrawerPush,
  storyDrawerHide,
  storyPanelShow: storyDrawerPush,
  storyPanelHide: storyDrawerHide,
  get: () => CHART_STORIES,
};
