/** 点击玫瑰图扇区 → 左侧滑入流派故事卡 / Other playlist */
window.GenreShowcase = (() => {
  let catalog = {};
  let otherPlaylist = [];
  let otherPlaylistById = new Map();
  let total = 0;
  let playlistBound = false;
  const IMG_BASE = "images/genres/";

  const root = () => document.getElementById("genre-showcase");

  function fmt(n) {
    return window.TableauTheme?.fmtNum(n) ?? String(n);
  }

  function primaryArtist(artist) {
    return (artist || "").split("|")[0].trim();
  }

  function safeFile(genre) {
    return genre.replace(/&/g, "and").replace(/\s+/g, "_");
  }

  function absUrl(rel) {
    try {
      return new URL(rel, window.location.href).href;
    } catch {
      return rel;
    }
  }

  function setVisible(show) {
    const el = root();
    if (!el) return;
    el.classList.toggle("is-visible", show);
    el.setAttribute("aria-hidden", show ? "false" : "true");
  }

  function playlistForOther(stat) {
    const byGenre = Object.fromEntries(otherPlaylist.map((t) => [t.genre, t]));
    const rest = stat?.rest || [];
    const ordered = rest.map((r) => byGenre[r.genre]).filter(Boolean);
    const seen = new Set(ordered.map((t) => t.genre));
    otherPlaylist.forEach((t) => {
      if (!seen.has(t.genre)) ordered.push(t);
    });
    return ordered;
  }

  async function playItem(track, btn) {
    if (!track || !window.DeckMusic) return;
    const el = root();
    const trackEl = el?.querySelector(".gs-track");
    if (trackEl) {
      trackEl.textContent = `♪ ${track.track} — ${primaryArtist(track.artist)}`;
    }
    el?.querySelectorAll(".gs-pl-item").forEach((b) => b.classList.remove("is-active"));
    btn?.classList.add("is-active");
    btn?.classList.add("is-loading");
    try {
      await window.DeckMusic.play(track);
    } finally {
      btn?.classList.remove("is-loading");
    }
  }

  function trackFromButton(btn) {
    const id = btn.dataset.trackId;
    if (id && otherPlaylistById.has(id)) return otherPlaylistById.get(id);
    const genre = btn.dataset.genre;
    if (genre) return otherPlaylist.find((t) => t.genre === genre) || null;
    const idx = Number(btn.dataset.idx);
    return Number.isFinite(idx) ? otherPlaylist[idx] : null;
  }

  function bindPlaylistEvents() {
    if (playlistBound) return;
    const container = root()?.querySelector(".gs-playlist");
    if (!container) return;
    playlistBound = true;
    container.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const btn = e.target.closest(".gs-pl-item");
      if (!btn) return;
      const track = trackFromButton(btn);
      playItem(track, btn);
    });
  }

  async function preloadCatalog() {
    await Promise.all(
      Object.entries(catalog).map(async ([genre, meta]) => {
        const safe = safeFile(genre);
        const rel = meta?.image || `${IMG_BASE}${safe}.jpg`;
        try {
          const res = await fetch(absUrl(rel));
          if (res.ok) {
            const blob = await res.blob();
            meta._blobUrl = URL.createObjectURL(blob);
          }
        } catch (_) {}
      })
    );
  }

  function setPosterBg(wrap, url, color) {
    if (!wrap || !url) return;
    wrap.style.backgroundImage = `url("${url}")`;
    wrap.style.backgroundSize = "cover";
    wrap.style.backgroundPosition = "center";
    wrap.style.backgroundColor = color;
  }

  function applySvgPoster(wrap, url, color, onFail) {
    fetch(url)
      .then((r) => (r.ok ? r.text() : Promise.reject()))
      .then((svg) => {
        wrap.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
        wrap.style.backgroundSize = "cover";
        wrap.style.backgroundPosition = "center";
      })
      .catch(onFail);
  }

  async function applyPoster(wrap, genre, meta) {
    if (!wrap) return;
    const color = meta?.color || "#499894";
    const safe = safeFile(genre);
    wrap.style.backgroundColor = color;
    wrap.style.backgroundImage = "none";

    const relCandidates = [
      meta?.image,
      `${IMG_BASE}${safe}.jpg`,
      `${IMG_BASE}${safe}.svg`,
    ].filter(Boolean);
    const candidates = [...new Set(relCandidates.map(absUrl))];
    if (meta?._blobUrl) candidates.unshift(meta._blobUrl);

    let idx = 0;
    const fail = () => {
      if (idx >= candidates.length) {
        wrap.style.backgroundImage = `linear-gradient(135deg, ${color} 0%, #1a1a1a 88%)`;
        return;
      }
      const url = candidates[idx];
      idx += 1;
      const isSvg = url.includes(".svg") || url.startsWith("blob:");
      if (isSvg && !url.startsWith("blob:")) {
        applySvgPoster(wrap, url, color, fail);
      } else {
        const img = new Image();
        img.onload = () => setPosterBg(wrap, url, color);
        img.onerror = fail;
        img.src = url;
      }
    };
    fail();
  }

  function renderPlaylist(items, stat) {
    const container = root()?.querySelector(".gs-playlist");
    if (!container) return;
    const counts = Object.fromEntries((stat?.rest || []).map((r) => [r.genre, r.count]));
    container.innerHTML = items
      .map(
        (t, i) => `
      <button class="gs-pl-item" type="button" data-idx="${i}" data-genre="${t.genre}" data-track-id="${t.track_id || ""}" aria-label="播放 ${t.genre}：${t.track}">
        <span class="gs-pl-main">
          <span class="gs-pl-genre">${t.genre}</span>
        </span>
        <span class="gs-pl-meta">${t.track} · ${primaryArtist(t.artist)}</span>
        ${counts[t.genre] ? `<span class="gs-pl-count">${fmt(counts[t.genre])} 首</span>` : ""}
      </button>`
      )
      .join("");
  }

  function showOther(stat) {
    const el = root();
    if (!el) return;
    const count = stat?.count ?? 0;
    const pct = total ? ((count / total) * 100).toFixed(1) : "0";
    const wrap = el.querySelector(".gs-img-wrap");
    const name = el.querySelector(".gs-name");
    const stats = el.querySelector(".gs-stats");
    const blurb = el.querySelector(".gs-blurb");
    const story = el.querySelector(".gs-story");
    const trackEl = el.querySelector(".gs-track");
    const items = playlistForOther(stat);

    el.classList.add("gs-mode-playlist");
    if (wrap) wrap.style.display = "none";
    if (name) name.textContent = "Other · 长尾流派歌单";
    if (stats) stats.textContent = `${fmt(count)} 首 · 占比 ${pct}%`;
    if (blurb) blurb.textContent = "点击任意流派行即可播放 30 秒预览";
    if (story) story.innerHTML = "";
    if (trackEl) trackEl.textContent = "";
    renderPlaylist(items, stat);
    bindPlaylistEvents();
    setVisible(true);
  }

  async function show(genre, stat, track) {
    const el = root();
    if (!el) return;

    if (genre === "Other") {
      showOther(stat);
      return;
    }

    el.classList.remove("gs-mode-playlist");
    const wrap = el.querySelector(".gs-img-wrap");
    if (wrap) wrap.style.display = "";
    el.querySelector(".gs-playlist")?.replaceChildren();

    const meta = catalog[genre];
    if (!meta) return;

    const count = stat?.count ?? 0;
    const pct = total ? ((count / total) * 100).toFixed(1) : "0";
    const name = el.querySelector(".gs-name");
    const stats = el.querySelector(".gs-stats");
    const blurb = el.querySelector(".gs-blurb");
    const story = el.querySelector(".gs-story");
    const trackEl = el.querySelector(".gs-track");

    await applyPoster(wrap, genre, meta);
    if (name) name.textContent = genre;
    if (stats) stats.textContent = `${fmt(count)} 首 · 占比 ${pct}%`;
    if (blurb) blurb.textContent = meta.blurb || "";

    const st = window.ChartStories?.get()?.genre_market?.[genre];
    if (story) {
      story.innerHTML = st
        ? `<span class="gs-story-head">${st.headline}</span>${st.story}`
        : "";
    }
    if (trackEl) {
      trackEl.textContent = track ? `♪ ${track.track} — ${primaryArtist(track.artist)}` : "";
    }

    setVisible(true);
  }

  function hide() {
    const el = root();
    el?.classList.remove("gs-mode-playlist");
    setVisible(false);
  }

  async function load(marketData, playlist) {
    total = (marketData || []).reduce((s, d) => s + d.count, 0);
    otherPlaylist = playlist || [];
    otherPlaylistById = new Map(otherPlaylist.filter((t) => t.track_id).map((t) => [t.track_id, t]));
    bindPlaylistEvents();
    try {
      const res = await fetch(absUrl("../web/data/genre_images.json?v=125"));
      catalog = await res.json();
      await preloadCatalog();
    } catch (e) {
      console.warn("[GenreShowcase] genre_images.json missing", e);
    }
    root()
      ?.querySelector(".gs-close")
      ?.addEventListener("click", hide);
  }

  return { load, show, reset: hide, hide, playByGenre: (genre) => {
    const t = otherPlaylist.find((x) => x.genre === genre);
    const btn = root()?.querySelector(`.gs-pl-item[data-genre="${genre}"]`);
    if (t) playItem(t, btn);
  }};
})();
