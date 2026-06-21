/** 点击散点气泡 → 左侧滑入艺人详情卡 */
window.ArtistShowcase = (() => {
  let currentTrack = null;
  let catalog = {};

  const root = () => document.getElementById("artist-showcase");

  function safeFile(name) {
    return name.replace(/\s+/g, "_");
  }

  function absUrl(rel) {
    try {
      return new URL(rel, window.location.href).href;
    } catch {
      return rel;
    }
  }

  function fmt(n) {
    return window.TableauTheme?.fmtNum(n) ?? String(n);
  }

  function fmtPop(n) {
    const v = Number(n);
    if (v >= 1000) return `${(v / 1000).toFixed(2)}K`;
    return String(Math.round(v));
  }

  function setVisible(show) {
    const el = root();
    if (!el) return;
    el.classList.toggle("is-visible", show);
    el.setAttribute("aria-hidden", show ? "false" : "true");
    document.body.classList.toggle("artist-panel-open", show);
    document.querySelector(".ch3-artist")?.classList.toggle("has-artist-panel", show);
  }

  function syncActiveCard(artist) {
    document.querySelectorAll(".ch3-artist-mini").forEach((btn) => {
      btn.classList.toggle("is-active", !!artist && btn.dataset.artist === artist);
    });
  }

  function applyPhoto(artist, genre) {
    const el = root();
    const photo = el?.querySelector(".as-photo");
    const hero = el?.querySelector(".as-hero");
    if (!photo || !hero) return;

    const meta = catalog[artist];
    const color =
      meta?.color ||
      window.TableauTheme?.artistColor?.(artist) ||
      window.TableauTheme?.genreColor?.(genre) ||
      "#499894";

    const candidates = [
      meta?.image,
      `images/artists/${safeFile(artist)}.jpg`,
      `images/artists/${safeFile(artist)}.png`,
    ].filter(Boolean);

    photo.alt = artist;
    photo.style.display = "";
    hero.style.setProperty("--as-accent", color);
    photo.style.objectPosition = meta?.facePosition || "center 18%";

    let idx = 0;
    const probe = () => {
      if (idx >= candidates.length) {
        photo.style.display = "none";
        hero.style.background = `linear-gradient(135deg, ${color} 0%, #1a1a1a 88%)`;
        return;
      }
      const src = absUrl(candidates[idx]);
      const img = new Image();
      img.onload = () => {
        photo.src = src;
        photo.style.display = "";
        hero.style.background = `linear-gradient(180deg, rgba(0,0,0,.05) 0%, rgba(0,0,0,.72) 100%), ${color}`;
      };
      img.onerror = () => {
        idx += 1;
        probe();
      };
      img.src = src;
    };
    probe();
  }

  function show(artist, point, track) {
    const el = root();
    if (!el || !artist) return;

    currentTrack = track || window.DeckMusic?.lookupArtist?.(artist) || null;
    const genre = point?.genre || currentTrack?.genre || catalog[artist]?.genre || "";
    const st = window.ChartStories?.get()?.artist_scatter?.[artist];

    const name = el.querySelector(".as-name");
    const genreEl = el.querySelector(".as-genre");
    const stats = el.querySelector(".as-stats");
    const eventEl = el.querySelector(".as-event");
    const story = el.querySelector(".as-story");
    const playBtn = el.querySelector(".as-track-play");

    applyPhoto(artist, genre);

    if (name) name.textContent = artist;
    if (genreEl) genreEl.textContent = genre || "—";

    const followers = point?.followers ?? 0;
    const popularity = point?.popularity ?? 0;
    const tracks = point?.tracks ?? 0;
    if (stats) {
      stats.textContent = `粉丝 ${fmt(followers)} · 热度 ${fmtPop(popularity)} · ${tracks} 首曲目`;
    }
    if (eventEl) eventEl.textContent = st?.event || "";
    if (story) story.textContent = st?.story || "该艺人在数据集中处于流派顶流坐标带。";

    if (playBtn) {
      if (currentTrack) {
        playBtn.hidden = false;
        playBtn.textContent = `♪ 播放 ${currentTrack.track}`;
      } else {
        playBtn.hidden = true;
        playBtn.textContent = "";
      }
    }

    setVisible(true);
    syncActiveCard(artist);
  }

  function hide() {
    currentTrack = null;
    syncActiveCard(null);
    setVisible(false);
  }

  async function load() {
    try {
      const res = await fetch(absUrl("../web/data/artist_images.json?v=124"));
      catalog = await res.json();
    } catch {
      catalog = {};
    }
  }

  function bind() {
    const el = root();
    if (!el || el.dataset.bound) return;
    el.dataset.bound = "1";
    el.querySelector(".as-close")?.addEventListener("click", hide);
    el.querySelector(".as-track-play")?.addEventListener("click", () => {
      if (currentTrack) void window.DeckMusic?.play?.(currentTrack);
    });
  }

  return { load, show, hide, bind };
})();
