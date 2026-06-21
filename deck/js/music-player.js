/** 点击即播 — Deezer / iTunes 30s 预览 · Spotify 兜底（悬停不播放） */
window.DeckMusic = (() => {
  let catalog = { by_artist: {}, by_track_id: {}, by_genre: {} };
  const previewCache = new Map();
  let hideTimer = null;
  let currentKey = "";
  let playing = false;

  const bar = () => document.getElementById("music-bar");
  const audio = () => document.getElementById("music-audio");
  const spotify = () => document.getElementById("music-spotify");

  function trackKey(t) {
    return `${t.artist || ""}::${t.track || ""}::${t.track_id || ""}`;
  }

  function primaryArtist(artist) {
    return (artist || "").split("|")[0].trim();
  }

  function enrich(track) {
    if (!track) return null;
    const byId = track.track_id ? catalog.by_track_id?.[track.track_id] : null;
    const genreKey = track.genreKey || track.genre;
    const base =
      catalog.by_genre?.[genreKey] ||
      catalog.by_other_genre?.[genreKey] ||
      catalog.by_artist?.[track.artist] ||
      byId ||
      {};
    return {
      ...base,
      ...track,
      preview_url: track.preview_url || base.preview_url || previewCache.get(trackKey({ ...base, ...track })) || null,
      spotify_url:
        track.spotify_url ||
        base.spotify_url ||
        (track.track_id ? `https://open.spotify.com/track/${track.track_id}` : null),
    };
  }

  function setBarVisible(show) {
    const el = bar();
    if (el) el.classList.toggle("is-visible", show);
  }

  function updateUI(track, mode) {
    const el = bar();
    if (!el) return;
    el.querySelector(".mp-track").textContent = track.track || "—";
    el.querySelector(".mp-artist").textContent = primaryArtist(track.artist);
    const modeEl = el.querySelector(".mp-mode");
    if (modeEl) {
      const labels = {
        loading: "正在加载预览…",
        playing: "正在播放",
        preview: "30 秒预览",
        spotify: "Spotify 播放",
        ready: "点击播放",
      };
      modeEl.textContent = labels[mode] || "播放中";
    }
  }

  async function fetchDeezerPreview(track, artist) {
    const q = encodeURIComponent(`${track} ${primaryArtist(artist)}`);
    try {
      const res = await fetch(`https://api.deezer.com/search?q=${q}&limit=1`);
      const data = await res.json();
      return data.data?.[0]?.preview || null;
    } catch {
      return null;
    }
  }

  async function fetchItunesPreview(track, artist) {
    const term = encodeURIComponent(`${track} ${primaryArtist(artist)}`);
    try {
      const res = await fetch(`https://itunes.apple.com/search?term=${term}&entity=song&limit=1`);
      const data = await res.json();
      return data.results?.[0]?.previewUrl || null;
    } catch {
      return null;
    }
  }

  async function resolvePreviewUrl(track, { forceFresh = false } = {}) {
    const key = trackKey(track);
    if (!forceFresh && previewCache.has(key)) return previewCache.get(key);
    if (!forceFresh && track.preview_url) {
      previewCache.set(key, track.preview_url);
      return track.preview_url;
    }
    let url = await fetchDeezerPreview(track.track, track.artist);
    if (!url) url = await fetchItunesPreview(track.track, track.artist);
    if (url) previewCache.set(key, url);
    return url;
  }

  async function playAudio(track, url) {
    const a = audio();
    const s = spotify();
    if (!a || !url) return false;
    s?.classList.add("hidden");
    a.classList.remove("hidden");
    if (a.src !== url) {
      a.src = url;
      a.load();
    }
    try {
      await a.play();
      updateUI(track, "playing");
      setBarVisible(true);
      playing = true;
      return true;
    } catch {
      return false;
    }
  }

  function playSpotify(track) {
    const s = spotify();
    const a = audio();
    if (!s || !track.spotify_url) return false;
    a?.pause();
    a?.classList.add("hidden");
    const embed =
      track.spotify_url.replace("open.spotify.com/track/", "open.spotify.com/embed/track/") +
      "?utm_source=generator&theme=0&autoplay=1";
    if (s.src !== embed) s.src = embed;
    s.classList.remove("hidden");
    updateUI(track, "spotify");
    setBarVisible(true);
    playing = true;
    return true;
  }

  async function play(track) {
    const t = enrich(track);
    if (!t) return;
    const key = trackKey(t);
    currentKey = key;
    clearTimeout(hideTimer);

    setBarVisible(true);
    updateUI(t, "loading");

    const tryPlayPreview = async (url) => url && (await playAudio(t, url));

    let preview = await resolvePreviewUrl(t);
    if (await tryPlayPreview(preview)) return;

    previewCache.delete(key);
    preview = await resolvePreviewUrl(t, { forceFresh: true });
    if (await tryPlayPreview(preview)) return;

    playSpotify(t);
  }

  function preview() {
    /* 悬停不再触发播放，保留 API 兼容旧调用 */
  }

  function stopPreview() {
    /* 悬停不再触发播放 */
  }

  function stop() {
    currentKey = "";
    playing = false;
    clearTimeout(hideTimer);
    audio()?.pause();
    if (audio()) audio().src = "";
    setBarVisible(false);
    spotify()?.classList.add("hidden");
    if (spotify()) spotify().src = "";
  }

  function indexCharts(chartsData) {
    const idx = catalog.by_track_id || {};
    (chartsData?.emotion_quadrant || []).forEach((t) => {
      if (t.track_id) idx[t.track_id] = { track: t.track, artist: t.artist, track_id: t.track_id };
    });
    Object.values(chartsData?.style_distribution || {})
      .flat()
      .forEach((t) => {
        if (t.track_id) idx[t.track_id] = { track: t.track, artist: t.artist, track_id: t.track_id };
      });
    (chartsData?.top100_golden?.samples || []).forEach((t) => {
      if (t.track_id) {
        idx[t.track_id] = {
          track: t.track,
          artist: t.artist,
          track_id: t.track_id,
          preview_url: t.preview_url || null,
          spotify_url: t.spotify_url || null,
        };
      }
    });
    catalog.by_track_id = idx;
  }

  async function load() {
    try {
      const base = window.__WEB_DATA_BASE || "../web/data/";
      const res = await fetch(`${base}featured_tracks.json?v=120`);
      catalog = await res.json();
      catalog.by_other_genre = Object.fromEntries(
        (catalog.other_playlist || []).map((t) => [t.genre, t])
      );
      const idx = catalog.by_track_id || {};
      (catalog.other_playlist || []).forEach((t) => {
        if (t.track_id) idx[t.track_id] = t;
      });
      catalog.by_track_id = idx;
    } catch (e) {
      console.warn("[DeckMusic] featured_tracks.json unavailable", e);
      catalog = { by_artist: {}, by_track_id: {}, by_genre: {} };
    }
    document.getElementById("music-close")?.addEventListener("click", stop);
    bar()?.addEventListener("mouseenter", () => clearTimeout(hideTimer));
  }

  return {
    load,
    play,
    preview,
    stopPreview,
    stop,
    indexCharts,
    lookupArtist: (a) => catalog.by_artist?.[a] || null,
    lookupGenre: (g) => catalog.by_genre?.[g] || catalog.by_other_genre?.[g] || null,
  };
})();
