/** 点击玫瑰图扇区 → 左侧滑入流派故事卡 / Other playlist */
window.GenreShowcase = (() => {
  let catalog = {};
  let otherPlaylist = [];
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

  function playItem(track, btn) {
    if (!track || !window.DeckMusic) return;
    const el = root();
    const trackEl = el?.querySelector(".gs-track");
    if (trackEl) {
      trackEl.textContent = `♪ ${track.track} — ${primaryArtist(track.artist)}`;
    }
    el?.querySelectorAll(".gs-pl-item").forEach((b) => b.classList.remove("is-active"));
    btn?.classList.add("is-active");
    void window.DeckMusic.play(track);
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
      const genre = btn.dataset.genre;
      const idx = Number(btn.dataset.idx);
      const track =
        (genre && otherPlaylist.find((t) => t.genre === genre)) ||
        otherPlaylist[idx];
      playItem(track, btn);
    });
  }

  async function preloadCatalog() {
    await Promise.all(
      Object.entries(catalog).map(async ([genre, meta]) => {
        const rel = meta?.image || `${IMG_BASE}${safeFile(genre)}.svg`;
        if (!rel.endsWith(".svg")) return;
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

  function applyPoster(wrap, genre, meta) {
    if (!wrap) return;
    const color = meta?.color || "#499894";
    const safe = safeFile(genre);
    const candidates = [meta?._blobUrl, meta?.image, `${IMG_BASE}${safe}.jpg`, `${IMG_BASE}${safe}.svg`]
      .filter(Boolean)
      .map(absUrl);
    wrap.style.backgroundColor = color;
    wrap.style.backgroundImage = "none";
    let idx = 0;
    const probe = () => {
      if (idx >= candidates.length) {
        wrap.style.backgroundImage = `linear-gradient(135deg, ${color} 0%, #1a1a1a 88%)`;
        return;
      }
      const img = new Image();
      img.onload = () => {
        wrap.style.backgroundImage = `url("${candidates[idx]}")`;
        wrap.style.backgroundSize = "cover";
        wrap.style.backgroundPosition = "center";
      };
      img.onerror = () => {
        idx += 1;
        probe();
      };
      img.src = candidates[idx];
    };
    probe();
  }

  function renderPlaylist(items, stat) {
    const container = root()?.querySelector(".gs-playlist");
    if (!container) return;
    const counts = Object.fromEntries((stat?.rest || []).map((r) => [r.genre, r.count]));
    container.innerHTML = items
      .map(
        (t, i) => `
      <button class="gs-pl-item" type="button" data-idx="${i}" data-genre="${t.genre}" aria-label="播放 ${t.genre}：${t.track}">
        <span class="gs-pl-main">
          <span class="gs-pl-genre">${t.genre}</span>
          <span class="gs-pl-play" aria-hidden="true">▶</span>
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
    if (blurb) blurb.textContent = "点击流派名称即可播放代表曲";
    if (story) story.innerHTML = "";
    if (trackEl) trackEl.textContent = "";
    renderPlaylist(items, stat);
    bindPlaylistEvents();
    setVisible(true);
  }

  function show(genre, stat, track) {
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

    applyPoster(wrap, genre, meta);
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
    bindPlaylistEvents();
    try {
      const res = await fetch(absUrl("../web/data/genre_images.json?v=111"));
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
