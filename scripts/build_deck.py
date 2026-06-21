"""Build Guizang-style interactive deck with ECharts + music player."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIZANG = Path.home() / ".agents" / "skills" / "guizang-ppt-skill"
DECK = ROOT / "deck"
STORY = json.loads((ROOT / "web" / "data" / "story.json").read_text(encoding="utf-8"))
CHARTS = json.loads((ROOT / "web" / "data" / "charts.json").read_text(encoding="utf-8"))
PALETTE = json.loads((ROOT / "web" / "data" / "palette.json").read_text(encoding="utf-8"))
CHART_STORIES = json.loads((ROOT / "web" / "data" / "chart_stories.json").read_text(encoding="utf-8"))
FEATURED = json.loads((ROOT / "web" / "data" / "featured_tracks.json").read_text(encoding="utf-8"))
GENRE_COLORS = PALETTE.get("main_genres", {})

TITLE = "10,000次心跳的采样"
SUBTITLE = "全球数字音乐的「情绪脉动」报告"
TOTAL = 12  # cover + 10 chapters + closing

CHAPTER_THEMES = [
    ("Act I · 宏观流派", "Genre Market"),
    ("Act II · 历史趋势", "Genre Trend"),
    ("Act III · 顶流艺人", "Artist Mirror"),
    ("Act IV · 音频指纹", "Golden Ratio"),
    ("Act V · 异类样本", "Outlier"),
    ("Act V · 热度轨迹", "Heat Trajectory"),
    ("Act VI · 风格光谱", "Style Matrix"),
    ("Act VII · 情绪空间", "Emotion Quadrant"),
    ("Act VIII · 文化反叛", "Explicit Trend"),
    ("Act IX · 行业悖论", "Explicit Ratio"),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def narrative_html(s: str) -> str:
    """story.json 叙事允许 <strong>/<em>，其余字符转义。"""
    import re

    if not s:
        return ""
    token_re = re.compile(r"(</?(?:strong|em)>)", re.I)
    out = []
    for part in token_re.split(s):
        if token_re.fullmatch(part or ""):
            out.append(part.lower())
        else:
            out.append(esc(part))
    return "".join(out)


def bullets_html(items):
    if not items:
        return ""
    return '<ul class="deck-bullets body-zh">' + "".join(f"<li>{b}</li>" for b in items) + "</ul>"


def compact_body(ch) -> str:
    """文字区精简：叙事 + 要点，避免 detail/bullets 重复堆叠。"""
    parts = [f'<p class="body-zh deck-lead" data-anim>{ch["narrative"]}</p>']
    if ch.get("bullets"):
        parts.append(bullets_html(ch["bullets"][:3]))
    elif ch.get("detail"):
        parts.append(f'<p class="body-zh deck-detail" data-anim>{ch["detail"]}</p>')
    return "\n      ".join(parts)


FEATURED_ARTISTS = ["Taylor Swift", "Bad Bunny", "Drake", "Playboi Carti"]


def fmt_followers(n: float) -> str:
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{n / 1e6:.0f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}K"
    return str(int(n))


def fmt_pop_k(n: float) -> str:
    return f"{n / 1000:.2f}K"


def ch3_body_html(ch) -> str:
    """第三章：叙事一段即可，艺人信息交给下方卡片。"""
    return f'<p class="body-zh deck-lead" data-anim>{ch["narrative"]}</p>'


def ch3_blurb(artist: str) -> str:
    story = CHART_STORIES.get("artist_scatter", {}).get(artist, {}).get("story", "")
    if len(story) > 46:
        return story[:44] + "…"
    return story


def ch3_aside_html() -> str:
    by_name = {d["artist"]: d for d in CHARTS["artist_scatter"]}
    ch3 = next((c for c in STORY if c["id"] == 3), {})
    cards = ""
    for name in FEATURED_ARTISTS:
        d = by_name.get(name)
        if not d:
            continue
        safe = name.replace(" ", "_")
        color = GENRE_COLORS.get(d["genre"], "#bab0ac")
        blurb = esc(ch3_blurb(name))
        cards += (
            f'<button type="button" class="ch3-artist-mini" data-artist="{esc(name)}">'
            f'<img class="ch3-artist-thumb" src="images/artists/{safe}.jpg" alt="{esc(name)}" loading="lazy">'
            f'<span class="ch3-artist-mini-cap">'
            f'<span class="ch3-artist-mini-row">'
            f'<span class="ch3-artist-mini-name">{esc(name)}</span>'
            f'<span class="ch3-artist-mini-tag" style="--tag:{color}">{esc(d["genre"])}</span>'
            f"</span>"
            f'<span class="ch3-artist-mini-meta">{fmt_followers(d["followers"])} 粉 · {fmt_pop_k(d["popularity"])} 热</span>'
            f'<span class="ch3-artist-mini-blurb">{blurb}</span>'
            f"</span></button>"
        )
    bridge = ch3.get("bridge", "")
    bridge_html = f'<p class="ch3-bridge body-zh">{bridge}</p>' if bridge else ""
    return f"""
      <div class="ch3-aside">
        <div class="ch3-aside-head">代表性顶流 · 点击卡片或图表气泡</div>
        <div class="ch3-artist-list">{cards}</div>
        {bridge_html}
      </div>"""


def ch1_aside_html() -> str:
    items = sorted(CHARTS["genre_market"], key=lambda x: -x["count"])[:5]
    total = sum(d["count"] for d in CHARTS["genre_market"])
    stats = "".join(
        f'<div class="ch1-stat">'
        f'<span class="ch1-stat-swatch" style="background:{GENRE_COLORS.get(d["genre"], "#bab0ac")}"></span>'
        f'<span class="ch1-stat-main"><span class="ch1-stat-genre">{esc(d["genre"])}</span>'
        f'<span class="ch1-stat-val">{d["count"]:,} 首</span></span>'
        f'<span class="ch1-stat-pct">{d["count"] / total * 100:.1f}%</span></div>'
        for d in items
    )
    return f"""
      <div class="ch1-aside">
        <p class="ch1-hint">点击玫瑰图扇区 · 播放代表曲 · 点击空白处停止</p>
        <div class="ch1-stats-head">2024 · Top 5 流派曲目数</div>
        <div class="ch1-stats">{stats}</div>
        <p class="ch1-footnote">长尾 {max(0, len(CHARTS["genre_market"]) - 5)}+ 流派归入 Other · 数据集共 {total:,} 首</p>
      </div>"""


def golden_ref_rail_html(row_keys: list[str], footnote: str, *, compact: bool = False) -> str:
    """矩阵右侧竖排参考带图例（行序与矩阵一致）。"""
    p = CHARTS["top100_golden"]["params"]
    spec_by_key = {
        "danceability": (
            "dance",
            "Danceability",
            "#f16913",
            ["#f9f3ef", "#f9e3d4", "#f3baac"],
            [
                ("弱律动", 0),
                ("轻微律动", p["danceability"]["light"]),
                ("强律动", p["danceability"]["strong"]),
            ],
        ),
        "energy": (
            "energy",
            "Energy",
            "#238b45",
            ["#f7faf0", "#e8edda", "#dee8bb"],
            [
                ("低能量", p["energy"]["low"]),
                ("中能量", p["energy"]["mid"]),
                ("高能量", p["energy"]["high"]),
            ],
        ),
        "loudness": (
            "loud",
            "Loud",
            "#2171b5",
            ["#f0f7fa", "#ddebf0", "#cbe6f0"],
            [
                ("低响度", p["loudness"]["soft"]),
                ("标准响度", p["loudness"]["standard"]),
                ("高响度", p["loudness"]["loud"]),
            ],
        ),
        "tempo": (
            "tempo",
            "Tempo",
            "#6a51a3",
            ["#f0f3fa", "#e2e6f0", "#d5dbf0"],
            [
                ("慢板", p["tempo"]["slow"]),
                ("中速", p["tempo"]["mid"]),
                ("快板", p["tempo"]["fast"]),
            ],
        ),
    }
    unit_by_key = {
        "danceability": "0–1",
        "energy": "0–1",
        "loudness": "dB",
        "tempo": "BPM",
    }
    cells = ""
    for key in row_keys:
        css_key, title, accent, band_colors, bands = spec_by_key[key]
        unit = unit_by_key.get(key, "")
        grad = f"linear-gradient(to bottom,{','.join(band_colors)})"
        items = "".join(
            f'<div class="golden-ref-item">'
            f'<span class="golden-ref-val" style="color:{accent}">{val:g}</span>'
            f'<span class="golden-ref-lbl">{esc(label)}</span></div>'
            for label, val in bands
        )
        cells += (
            f'<div class="golden-ref-cell golden-ref-{css_key}">'
            f'<div class="golden-ref-stripe" style="background:{grad}" title="色带分区"></div>'
            f'<div class="golden-ref-body">'
            f'<div class="golden-ref-metric" style="color:{accent}">{esc(title)}'
            f'<span class="golden-ref-unit">{esc(unit)}</span></div>'
            f'<div class="golden-ref-items">{items}</div>'
            f"</div></div>"
        )
    compact_cls = " is-compact" if compact else ""
    return f"""
        <aside class="golden-ref-rail{compact_cls}" aria-label="参考带图例">
          <div class="golden-ref-rail-head">参考带</div>
          <div class="golden-ref-rail-body">{cells}</div>
          <div class="golden-ref-rail-foot">{esc(footnote)}</div>
        </aside>"""


def ch4_ref_rail_html() -> str:
    return golden_ref_rail_html(
        ["danceability", "energy", "loudness", "tempo"],
        "虚线=分界 · 蓝点=均值",
    )


def ch5_ref_rail_html() -> str:
    row_keys = [r["key"] for r in CHARTS["meta"]["top10_golden_rows"]]
    return golden_ref_rail_html(
        row_keys,
        "虚线=分界 · 蓝=Billie异类",
        compact=True,
    )


def ch4_aside_html() -> str:
    samples = CHARTS["top100_golden"].get("samples") or []
    order = ["Top 100", "Middle(101-9000)", "Edge (9000-10000)"]
    by_group = {s["group"]: s for s in samples}
    cards = ""
    for grp in order:
        s = by_group.get(grp)
        if not s:
            continue
        tier = esc(s.get("label") or grp)
        preview_attr = (
            f' data-preview-url="{esc(s["preview_url"])}"' if s.get("preview_url") else ""
        )
        cards += (
            f'<button type="button" class="ch4-golden-track" '
            f'data-track-id="{esc(s["track_id"])}" '
            f'data-artist="{esc(s["artist"])}" '
            f'data-track="{esc(s["track"])}"{preview_attr}>'
            f'<span class="ch4-gt-tier">{tier}</span>'
            f'<span class="ch4-gt-title">{esc(s["track"])}</span>'
            f'<span class="ch4-gt-artist">{esc(s["artist"])}'
            f'{f" · {esc(s['genre'])}" if s.get("genre") else ""}</span>'
            f'<span class="ch4-gt-metrics">'
            f'Tempo {s["tempo"]:.0f} · Energy {s["energy"]:.2f} · Danceability {s["danceability"]:.2f}'
            f'</span>'
            f'<span class="ch4-gt-meta">#{s["rank"]} · Loud {s["loudness"]:.1f}</span>'
            f'<span class="ch4-gt-play">♪ 点击播放</span>'
            f"</button>"
        )
    return f"""
      <div class="ch4-aside">
        <div class="ch4-aside-head">三层样本 · 对应矩阵列 · 点击试听</div>
        <div class="ch4-golden-list">{cards}</div>
      </div>"""


CH5_BILLIE_TRACK = {
    "track": "bad guy",
    "track_id": "2Fxmhks0bxGSBdJ92vM42m",
    "artist": "Billie Eilish",
    "genre": "Pop",
}

BILLIE_TIMELINE = [
    {
        "year": "2016",
        "title": "横空出世",
        "text": "《Ocean Eyes》爆红 · 签约 Interscope",
        "key": True,
        "tag": "起点",
    },
    {
        "year": "2017",
        "title": "初露锋芒",
        "text": "首张 EP · Billboard 200 第 14",
    },
    {
        "year": "2019",
        "title": "全球爆红",
        "text": "首专夺冠 ·《bad guy》Hot 100 登顶",
        "key": True,
        "tag": "爆发",
    },
    {
        "year": "2020",
        "title": "格莱美横扫",
        "text": "18 岁揽五项格莱美 · 最年轻年度专辑",
    },
    {
        "year": "2021",
        "title": "奖项延续",
        "text": "格莱美年度制作 · Bond 主题曲",
    },
    {
        "year": "2022",
        "title": "奥斯卡加冕",
        "text": "《No Time To Die》奥斯卡最佳原创歌曲",
    },
    {
        "year": "2024",
        "title": "三专双奖",
        "text": "《What Was I Made For?》奥斯卡 + 格莱美",
    },
    {
        "year": "2025",
        "title": "巅峰持续",
        "text": "AMA 七项大奖 · 全球巡演至 11 月",
        "key": True,
        "tag": "当下",
    },
]


def ch6_aside_html() -> str:
    items = ""
    for ev in BILLIE_TIMELINE:
        key_cls = " is-key" if ev.get("key") else ""
        tag = ev.get("tag")
        tag_html = f'<span class="ch6-tl-badge">{esc(tag)}</span>' if tag else ""
        items += (
            f'<div class="ch6-tl-item{key_cls}" data-ch6-year="{esc(ev["year"])}" role="button" tabindex="0">'
            f'<div class="ch6-tl-marker" aria-hidden="true"></div>'
            f'<div class="ch6-tl-body">'
            f'<div class="ch6-tl-headline">'
            f'<span class="ch6-tl-year">{esc(ev["year"])}</span>'
            f'<span class="ch6-tl-title">{esc(ev["title"])}</span>'
            f"{tag_html}"
            f"</div>"
            f'<p class="ch6-tl-text">{esc(ev["text"])}</p>'
            f"</div></div>"
        )
    return f"""
      <div class="ch6-aside">
        <div class="ch6-tl-label">Billie Eilish · 发展时间轴</div>
        <p class="ch6-tl-hint">点击节点 · 联动热力图 · 双击图表空白恢复</p>
        <div class="ch6-timeline">{items}</div>
      </div>"""


def ch5_aside_html() -> str:
    top100 = CHARTS["top100_golden"]["groups"]["Top 100"]
    billie = next(d for d in CHARTS["top10_golden"] if d["artist"] == "Billie Eilish")
    track = CH5_BILLIE_TRACK
    featured = FEATURED.get("by_artist", {}).get("Billie Eilish") or {}
    preview_url = featured.get("preview_url") if featured.get("track") == track["track"] else None
    preview_attr = f' data-preview-url="{esc(preview_url)}"' if preview_url else ""
    return f"""
      <div class="ch5-aside">
        <div class="ch5-aside-head">物理指标 · Billie vs Top 100</div>
        <div class="ch5-radar-wrap">
          <div id="chart-5-radar" class="ch5-radar"></div>
        </div>
        <div class="ch5-outlier-notes">
          <div class="ch5-hi"><strong>Energy {billie['energy']:.2f}</strong><span>Top100 {top100['energy']:.2f}</span></div>
          <div class="ch5-hi"><strong>Loud {billie['loudness']:.1f}</strong><span>Top100 {top100['loudness']:.1f}</span></div>
          <div class="ch5-hi"><strong>Tempo {billie['tempo']:.0f}</strong><span>Top100 {top100['tempo']:.0f}</span></div>
        </div>
        <button type="button" class="ch5-billie-track"
          data-track-id="{esc(track['track_id'])}"
          data-artist="{esc(track['artist'])}"
          data-track="{esc(track['track'])}"{preview_attr}>
          <span class="ch5-bt-label">代表曲 · 点击试听</span>
          <span class="ch5-bt-title">{esc(track['track'])}</span>
          <span class="ch5-bt-artist">{esc(track['artist'])} · {esc(track['genre'])}</span>
          <span class="ch5-bt-play">♪ 播放</span>
        </button>
      </div>"""


STYLE_LABELS = {
    "Billie Eilish": "暗黑电子流行",
    "Linkin Park": "新金属",
    "Mrs. GREEN APPLE": "日式流行摇滚",
    "Taylor Swift": "乡村流行",
    "The Weeknd": "复古 R&B",
}


def style_top_track(artist: str) -> dict | None:
    tracks = CHARTS.get("style_distribution", {}).get(artist) or []
    if not tracks:
        return None
    return max(tracks, key=lambda t: t["popularity"])


def ch7_aside_html() -> str:
    items = ""
    for artist in CHARTS["meta"]["style_artists"]:
        tag = STYLE_LABELS.get(artist, "")
        color = PALETTE.get("artists", {}).get(artist, "#bab0ac")
        top = style_top_track(artist)
        if top:
            title = top["track"]
            if len(title) > 40:
                title = title[:38] + "…"
            metrics = (
                f"Danceability {top['danceability']:.2f} · "
                f"Energy {top['energy']:.2f} · "
                f"Tempo {top['tempo']:.0f} · "
                f"Loud {top['loudness']:.1f}"
            )
            track_html = (
                f'<div class="ch7-style-track" title="{esc(top["track"])}">'
                f"♪ {esc(title)}"
                f'<span class="ch7-style-pop">Pop {top["popularity"]}</span>'
                f"</div>"
                f'<div class="ch7-style-metrics">{esc(metrics)}</div>'
            )
        else:
            track_html = '<div class="ch7-style-metrics ch7-style-metrics--empty">暂无曲目数据</div>'
        items += (
            f'<div class="ch7-style-card">'
            f'<span class="ch7-style-dot" style="background:{color}"></span>'
            f'<div class="ch7-style-main">'
            f'<div class="ch7-style-head">'
            f'<span class="ch7-style-name">{esc(artist)}</span>'
            f'<span class="ch7-style-tag">{esc(tag)}</span>'
            f"</div>"
            f"{track_html}"
            f"</div></div>"
        )
    return f"""
      <div class="ch7-aside">
        <div class="ch7-aside-head">五位代表 · 最热曲目 · 物理指标</div>
        <div class="ch7-style-list">{items}</div>
      </div>"""


def emotion_anchor_track() -> dict:
    billie = [
        x for x in CHARTS.get("emotion_quadrant", []) if x.get("artist") == "Billie Eilish"
    ]
    if not billie:
        return {
            "track": "listen before i go",
            "track_id": "0tMSssfxAL2oV8Vri0mFHE",
            "artist": "Billie Eilish",
            "energy": 0.0561,
            "valence": 0.082,
            "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
        }
    return min(billie, key=lambda x: x["energy"] + x["valence"])


def ch8_viz_inline() -> str:
    svg_path = DECK / "images" / "ch8-sang-culture.svg"
    if svg_path.is_file():
        return svg_path.read_text(encoding="utf-8")
    return ""


def ch8_aside_html() -> str:
    anchor = emotion_anchor_track()
    featured = FEATURED.get("by_artist", {}).get("Billie Eilish") or {}
    preview_url = None
    if featured.get("track_id") == anchor["track_id"]:
        preview_url = featured.get("preview_url")
    preview_attr = f' data-preview-url="{esc(preview_url)}"' if preview_url else ""
    viz = ch8_viz_inline()
    viz_block = (
        f'<div class="ch8-viz" aria-hidden="true">{viz}</div>'
        if viz
        else '<div class="ch8-viz ch8-viz--fallback" aria-hidden="true"></div>'
    )
    return f"""
      <div class="ch8-emotion-panel">
        <p class="ch8-aside-hint">点击图表最左下角 Billie 散点 · 高亮锚点并展开侧栏</p>
        <div class="ch8-aside" aria-hidden="true">
          <div class="ch8-viz-wrap">
            {viz_block}
            <span class="ch8-viz-cap">左下象限 · {esc(anchor["track"])}</span>
          </div>
          <button type="button" class="ch8-track-play"
            data-track-id="{esc(anchor["track_id"])}"
            data-artist="{esc(anchor["artist"])}"
            data-track="{esc(anchor["track"])}"{preview_attr}>
            <span class="ch8-tp-label">代表曲 · 点击试听</span>
            <span class="ch8-tp-title">{esc(anchor["track"])}</span>
            <span class="ch8-tp-artist">{esc(anchor["artist"])} · {esc(anchor.get("album", ""))}</span>
            <span class="ch8-tp-metrics">Energy {anchor["energy"]:.3f} · Valence {anchor["valence"]:.3f}</span>
            <span class="ch8-tp-play">♪ 播放</span>
          </button>
          <p class="ch8-anchor-note">Billie 在 Top 10,000 曲目中<strong>最靠近左下角</strong>的单曲——低 Energy + 低 Valence，是「丧文化」情绪坐标的极端样本。</p>
          <div class="ch8-aside-foot" aria-hidden="true">Energy × Valence</div>
        </div>
      </div>"""


def ch10_paradox_card(
    genre: str,
    pct: float,
    note: str,
    color: str,
    *,
    featured: bool = False,
    compare: str = "",
) -> str:
    mod = " ch10-paradox-card--featured" if featured else ""
    compare_html = (
        f'<span class="ch10-paradox-compare">{compare}</span>' if compare else ""
    )
    return f"""
        <div class="ch10-paradox-card{mod}" data-genre="{esc(genre)}" style="--ch10-accent:{color}">
          <span class="ch10-paradox-kicker">行业悖论 · {esc(genre)}</span>
          <span class="ch10-paradox-pct">{pct:.2f}%</span>
          <span class="ch10-paradox-note">{esc(note)}</span>
          {compare_html}
        </div>"""


CH9_PEAK_NOTES = {
    "HipHop": "2024 峰值 · 街头叙事与 Explicit 高度绑定",
    "Latin": "西语流行 · 身体与欲望的直接表达",
    "Pop": "主流 Pop 同步抬升，Billie 系审美外溢",
    "R&B": "黑人文化谱系里的长期规范抵抗",
    "Rock": "总量低于 HipHop，但 2018 年后同样抬头",
}


def explicit_trend_peak(genre: str) -> dict:
    series = CHARTS.get("explicit_trend", {}).get(genre) or {}
    years = series.get("years") or []
    counts = series.get("counts") or []
    if not counts:
        return {"year": 0, "count": 0}
    peak_i = max(range(len(counts)), key=lambda i: counts[i])
    return {"year": years[peak_i], "count": counts[peak_i]}


def ch9_bubble_size(count: int, max_count: int) -> float:
    if not count:
        return 5.0
    return max(5.0, min(14.0, (count / max_count) * 13 + 5))


def ch9_bubble_legend_html() -> str:
    genres = CHARTS.get("meta", {}).get("explicit_trend_genres") or list(
        CHARTS.get("explicit_trend", {}).keys()
    )
    max_peak = max((explicit_trend_peak(g)["count"] for g in genres), default=261)
    steps = sorted({0, 100, 200, max_peak})
    items = []
    for val in steps:
        sz = ch9_bubble_size(max(val, 1), max_peak) if val else 5
        items.append(
            f'<span class="ch9-bl-item"><i class="ch9-bl-dot" style="--s:{sz:.0f}px"></i>{val}</span>'
        )
    return f"""<div class="ch9-bubble-legend" aria-hidden="true">
          <span class="ch9-bl-caption">气泡大小 = Explicit（首/年）</span>
          <div class="ch9-bl-steps">{''.join(items)}</div>
        </div>"""


def ch9_peak_card(genre: str, year: int, count: int, note: str, color: str, featured: bool = False) -> str:
    mod = " ch9-peak-card--featured" if featured else ""
    return f"""
        <div class="ch9-peak-card{mod}" data-genre="{esc(genre)}" style="--ch9-accent:{color}">
          <span class="ch9-peak-genre">{esc(genre)}</span>
          <span class="ch9-peak-count">{count}</span>
          <span class="ch9-peak-meta">{year} 年峰值 · 首 Explicit</span>
          <span class="ch9-peak-note">{esc(note)}</span>
        </div>"""


def ch9_aside_html() -> str:
    genres = CHARTS.get("meta", {}).get("explicit_trend_genres") or list(
        CHARTS.get("explicit_trend", {}).keys()
    )
    ranked = sorted(genres, key=lambda g: explicit_trend_peak(g)["count"], reverse=True)
    cards = []
    for i, genre in enumerate(ranked):
        peak = explicit_trend_peak(genre)
        cards.append(
            ch9_peak_card(
                genre,
                peak["year"],
                peak["count"],
                CH9_PEAK_NOTES.get(genre, ""),
                GENRE_COLORS.get(genre, "#bab0ac"),
                featured=i == 0,
            )
        )
    return f"""
      <div class="ch9-explicit-aside">
        <div class="ch9-aside-label">2018–2024 · Explicit 标签激增</div>
        <div class="ch9-peak-cards">{''.join(cards)}</div>
        <p class="ch9-aside-hint">点击流派卡片 · 左侧信息逐条常亮 · 图表仅高亮当前项 · 点击空白处重置</p>
      </div>"""


def ch10_aside_html() -> str:
    ratios = {x["genre"]: x for x in CHARTS.get("explicit_ratio", [])}
    rock = ratios.get("Rock", {})
    rb = ratios.get("R&B", {})
    metal = ratios.get("Metal", {})
    latin = ratios.get("Latin", {})
    hip = ratios.get("HipHop", {})
    rock_pct = rock.get("ratio", 0)
    rb_pct = rb.get("ratio", 0)
    vs_rb = f"{rock_pct / rb_pct * 100:.0f}%" if rb_pct else "—"
    cards = [
        ch10_paradox_card(
            "R&B",
            rb.get("ratio", 0),
            "根植于黑人文化对社会规范的长期抵抗",
            GENRE_COLORS.get("R&B", "#86bcb6"),
        ),
        ch10_paradox_card(
            "Metal",
            metal.get("ratio", 0),
            "极端表达的另一面",
            GENRE_COLORS.get("Metal", "#b6992d"),
        ),
        ch10_paradox_card(
            "Latin",
            latin.get("ratio", 0),
            "对身体与欲望的直接表达习惯",
            GENRE_COLORS.get("Latin", "#8cd17d"),
        ),
        ch10_paradox_card(
            "Rock",
            rock_pct,
            "刻板印象最「狂躁」，Explicit 占比却低于 Pop",
            GENRE_COLORS.get("Rock", "#ff9d9a"),
            featured=True,
            compare=f"仅为 R&amp;B（{rb_pct:.2f}%）的 {vs_rb} · HipHop 高达 {hip.get('ratio', 0):.2f}%",
        ),
    ]
    return f"""
      <div class="ch10-paradox-aside">
        <div class="ch10-paradox-cards">{''.join(cards)}</div>
        <p class="ch10-aside-hint">点击卡片或图表条柱 · 左侧信息逐条常亮 · 首次点击条柱增长 · 点击空白处重置</p>
      </div>"""


def chapter_slide(ch, idx: int, theme_left: str, theme_right: str, dark: bool):
    tone = "dark" if dark else "light"
    num = idx + 2
    chart_class = {
        "top100_golden": "matrix",
        "top10_golden": "matrix",
        "top10_heatmap": "heatmap",
        "explicit_trend": "facet",
        "explicit_ratio": "ratio",
        "genre_trend": "wide",
        "artist_scatter": "wide",
        "style_distribution": "wide",
    }.get(ch["chart"], "")

    showcase = ""
    ch1 = ch["id"] == 1
    ch2 = ch["id"] == 2
    ch3 = ch["id"] == 3
    ch4 = ch["id"] == 4
    ch5 = ch["id"] == 5
    ch6 = ch["id"] == 6
    ch7 = ch["id"] == 7
    ch8 = ch["id"] == 8
    ch9 = ch["id"] == 9
    ch10 = ch["id"] == 10
    chart_heavy = ch4 or ch5 or ch6
    if ch5:
        layout_class = "deck-layout-ch5"
    elif ch8:
        layout_class = "deck-layout-ch8"
    elif chart_heavy:
        layout_class = "deck-layout-chart-heavy"
    else:
        layout_class = "deck-layout-4060"
    if ch2:
        panel_hint = "单位：Popularity 年度合计（K = 千分）"
    elif ch3:
        panel_hint = "横轴对数 · 纵轴线性 · 淡点=全量艺人（低热区重叠属正常）"
    elif ch.get("chart") == "top10_heatmap":
        panel_hint = "点击 Billie 色块/时间轴 · 按该年均值(分)重排 · 双击空白恢复"
    elif ch.get("chart") == "top100_golden":
        panel_hint = "矩阵 · 右侧参考带 · 单位见行标/图例"
    elif ch.get("chart") == "top10_golden":
        panel_hint = "蓝=Billie异类 · 右侧参考带 · 单位见行标"
    elif ch.get("chart") == "style_distribution":
        panel_hint = "图例含流派 · 点击散点播放"
    elif ch.get("chart") == "emotion_quadrant":
        panel_hint = "横轴 最大值 Valence · 纵轴 最大值 Energy · 刻度 0.05 · 点击最左下 Billie 点高亮"
    elif ch.get("chart") == "explicit_trend":
        panel_hint = "纵轴：Explicit（首/年）· 横轴：发行年份 · 初始全量 · 点击仅亮一条"
    elif ch.get("chart") == "explicit_ratio":
        panel_hint = "占比 = Explicit / 总曲目 · 初始全量 · 点击仅亮一条"
    else:
        panel_hint = "点击数据点 · 查看故事解读"
    if ch9:
        chart_head = f"""<div class="chart-panel-head ch9-chart-head">
        <div class="chart-panel-head-col">
          <span class="chart-panel-title">{esc(ch['subtitle'])}</span>
          <span class="chart-panel-unit">纵轴 Explicit（首/年）· 横轴 发行年份 · Main Genres</span>
        </div>
        {ch9_bubble_legend_html()}
      </div>"""
    elif ch2 or ch3 or ch10:
        chart_head = f"""<div class="chart-panel-head">
        <span class="chart-panel-title">{esc(ch['subtitle'])}</span>
        <span class="chart-panel-unit">{panel_hint}</span>
      </div>"""
    else:
        chart_head = f"""<div class="chart-panel-head">
        <span>{esc(ch['subtitle'])}</span>
        <span>{panel_hint}</span>
      </div>"""
    ch1_sidebar = ch1_aside_html() if ch1 else ""
    ch3_sidebar = ch3_aside_html() if ch3 else ""
    ch4_sidebar = ch4_aside_html() if ch4 else ""
    ch5_sidebar = ch5_aside_html() if ch5 else ""
    ch6_sidebar = ch6_aside_html() if ch6 else ""
    ch7_sidebar = ch7_aside_html() if ch7 else ""
    ch8_sidebar = ch8_aside_html() if ch8 else ""
    ch9_sidebar = ch9_aside_html() if ch9 else ""
    ch10_sidebar = ch10_aside_html() if ch10 else ""
    ch2_sidebar = ""
    if ch2:
        ch2_sidebar = """
      <div class="genre-trend-sidebar">
        <p class="gt-sidebar-hint">点击时间节点 · 右侧图表联动 · 上方字幕切换</p>
        <div class="genre-trend-notes" id="genre-trend-notes" aria-live="polite"></div>
      </div>"""
        chart_block = f'<div id="chart-{ch["id"]}" class="deck-chart {chart_class}"></div>'
    elif ch4:
        chart_block = f"""<div class="golden-matrix-wrap">
        <div id="chart-{ch["id"]}" class="deck-chart {chart_class}"></div>
        {ch4_ref_rail_html()}
      </div>"""
    elif ch5:
        chart_block = f"""<div class="golden-matrix-wrap is-compact">
        <div id="chart-{ch["id"]}" class="deck-chart {chart_class}"></div>
        {ch5_ref_rail_html()}
      </div>"""
    else:
        chart_block = f'<div id="chart-{ch["id"]}" class="deck-chart {chart_class}"></div>'

    extra_class = ""
    if ch1:
        extra_class = " ch1-genre"
    elif ch2:
        extra_class = " ch2-trend"
    elif ch3:
        extra_class = " ch3-artist"
    elif ch4:
        extra_class = " ch4-golden"
    elif ch5:
        extra_class = " ch5-outlier"
    elif ch6:
        extra_class = " ch6-heat"
    elif ch7:
        extra_class = " ch7-style"
    elif ch8:
        extra_class = " ch8-emotion"
    elif ch9:
        extra_class = " ch9-explicit"
    elif ch10:
        extra_class = " ch10-paradox"

    if ch3:
        body_html = ch3_body_html(ch)
    elif ch2:
        body_html = (
            '<p class="body-zh deck-lead gt-narrative is-enter" data-anim>'
            "在 2000 年代初，Rock 依然是最受欢迎的流派。"
            "</p>"
        )
    elif ch8:
        body_html = (
            '<p class="body-zh deck-lead deck-lead-ch8" data-anim>'
            "我们专门对 Taylor 和 Billie 的情绪象限进行了比较分析。"
            "数据显示，Billie 的歌普遍落在低 Energy、低 Valence 区域——"
            "也就是低能量 + 负面情绪的象限。"
            "</p>"
            '<p class="body-zh deck-detail deck-detail-ch8" data-anim>'
            "这恰好对应了 2016 年前后在年轻人中蔓延的「丧文化」："
            "疲惫、焦虑、反对过度积极。"
            "</p>"
        )
    elif ch9:
        body_html = (
            f'<p class="body-zh deck-lead deck-lead-compact" data-anim>{narrative_html(ch["narrative"])}</p>'
        )
    elif ch5 or ch6:
        body_html = f'<p class="body-zh deck-lead deck-lead-compact" data-anim>{narrative_html(ch["narrative"])}</p>'
    elif ch10:
        body_html = (
            '<p class="body-zh deck-lead deck-lead-compact" data-anim>'
            "最有趣的行业悖论发生在「哪些流派更叛逆」的占比分析中："
            "</p>"
        )
    else:
        body_html = compact_body(ch)

    return f"""
<section class="slide {tone} split-slide{extra_class}" data-chart="{ch['chart']}" data-chart-id="chart-{ch['id']}" data-slide="{ch['id']}">
  <div class="chrome"><div>{theme_left}</div><div>{num:02d} / {TOTAL}</div></div>
  <div class="{layout_class} deck-split">
    <div class="col deck-text">
      <div class="kicker" data-anim>第 {ch['id']} 章</div>
      <h2 class="h1-zh" data-anim>{esc(ch['title'])}</h2>
      {body_html}
      {ch1_sidebar}
      {ch2_sidebar}
      {ch3_sidebar}
      {ch4_sidebar}
      {ch5_sidebar}
      {ch6_sidebar}
      {ch7_sidebar}
      {ch8_sidebar}
      {ch9_sidebar}
      {ch10_sidebar}
      {showcase}
    </div>
    <div class="chart-panel" data-anim>
      {chart_head}
      {chart_block}
    </div>
  </div>
  <div class="foot"><div>{esc(ch['subtitle'])}</div><div>{theme_right}</div></div>
</section>"""


def build_slides() -> str:
    parts = [
        f"""
<section class="slide hero dark" data-slide="0">
  <div class="chrome"><div>Spotify Top 10,000 · 情绪脉动</div><div>01 / {TOTAL}</div></div>
  <div class="frame" style="display:grid;gap:3.2vh;align-content:center;min-height:78vh">
    <div class="kicker" data-anim>Data Visualization · Final Project</div>
    <h1 class="display-zh" data-anim>{esc(TITLE)}</h1>
    <h2 class="h2-zh" data-anim style="opacity:.88">{esc(SUBTITLE)}</h2>
    <p class="lead" style="max-width:64vw" data-anim>
      基于 Spotify 全球 Top 10,000 热门歌曲数据集，以 Tableau 工作簿为视觉基准，
      复刻 10 组交互图表，讲述从<strong>流派王权交替</strong>到<strong>情绪象限</strong>、
      从<strong>黄金公式</strong>到<strong>文化反叛</strong>的完整数据叙事。
    </p>
  </div>
  <div class="foot"><div>点击播放 · ← → 翻页</div><div>2026</div></div>
</section>"""
    ]

    for i, ch in enumerate(STORY):
        left, right = CHAPTER_THEMES[i]
        parts.append(chapter_slide(ch, i, left, right, dark=(i % 2 == 1)))

    parts.append(
        f"""
<section class="slide hero light" data-slide="10">
  <div class="chrome"><div>Closing · 结语</div><div>{TOTAL:02d} / {TOTAL}</div></div>
  <div class="frame" style="display:grid;gap:3.5vh;align-content:center;min-height:72vh;text-align:center">
    <div class="kicker" data-anim style="justify-self:center">Takeaway</div>
    <h2 class="h1-zh" data-anim>音乐没有标准答案，<br><em>但有数据可循。</em></h2>
    <p class="body-zh" style="max-width:58vw;justify-self:center;opacity:.85" data-anim>
      从王权交替到情绪象限，从黄金公式到文化反叛——10,000 次心跳的采样，
      让我们听见全球数字音乐的情绪脉动。数据不会替代审美，
      但它能帮我们读懂 Spotify 热门歌曲背后，那些关于时代、身份与反叛的故事。
    </p>
    <div class="meta-row" data-anim style="justify-content:center;font-family:var(--mono);font-size:12px;letter-spacing:.16em;opacity:.6">
      <span>谢谢</span><span>·</span><span>Q&amp;A</span>
    </div>
  </div>
  <div class="foot"><div>{esc(TITLE)}</div><div>2026</div></div>
</section>"""
    )
    return "\n".join(parts)


EXTRA_CSS = """
  .deck-layout-4060{display:grid;grid-template-columns:40fr 60fr;gap:3vw;flex:1;align-items:stretch}
  .deck-layout-ch8{display:grid;grid-template-columns:50fr 50fr;gap:2.4vw;flex:1;align-items:stretch}
  .deck-layout-chart-heavy{display:grid;grid-template-columns:28fr 72fr;gap:2.2vw;flex:1;align-items:stretch}
  .deck-layout-ch5{display:grid;grid-template-columns:34fr 66fr;gap:3.2vw;flex:1;align-items:stretch}
  .deck-split{align-items:stretch;padding-top:1.2vh;flex:1;min-height:0}
  .deck-text{gap:1vh;max-height:76vh;overflow:auto;padding-right:.5vw;justify-content:flex-start}
  .deck-text::-webkit-scrollbar{width:3px}
  .deck-text::-webkit-scrollbar-thumb{background:rgba(var(--ink-rgb),.2);border-radius:2px}
  .slide.dark .deck-text::-webkit-scrollbar-thumb{background:rgba(var(--paper-rgb),.25)}
  .split-slide .h1-zh{font-size:2.5vw;line-height:1.12;margin-bottom:.15vh}
  .deck-lead{font-size:max(13px,.92vw)!important;line-height:1.52!important;opacity:.82;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
  .deck-lead-compact{-webkit-line-clamp:4;font-size:max(12px,.88vw)!important;line-height:1.48!important}
  .deck-detail{font-size:max(12px,.86vw)!important;line-height:1.48!important;opacity:.72;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
  .deck-bullets{margin:.15vh 0 0 1em;line-height:1.42;font-size:max(11px,.84vw)!important;opacity:.78}
  .deck-bullets li{margin:.2em 0}
  .chart-panel{background:#fff;color:#111;border-radius:6px;padding:10px 12px 8px;min-height:68vh;height:100%;display:flex;flex-direction:column;box-shadow:0 18px 50px rgba(0,0,0,.18)}
  .slide.light .chart-panel{box-shadow:0 12px 40px rgba(0,0,0,.08)}
  .chart-panel-head{display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:8px;letter-spacing:.1em;text-transform:uppercase;opacity:.45;margin-bottom:4px;padding:0 2px;gap:.8vw}
  .chart-panel-head span:last-child{text-align:right;max-width:52%;line-height:1.35}
  .deck-chart{flex:1;min-height:62vh;width:100%}
  .deck-chart.wide{min-height:64vh}
  .deck-chart.matrix{min-height:68vh}
  .deck-chart.heatmap{min-height:68vh}
  .deck-chart.facet{min-height:66vh}
  .ch4-golden .deck-lead{-webkit-line-clamp:2}
  .ch4-golden .deck-bullets{font-size:max(10px,.78vw)!important;margin-top:.1vh}
  .ch4-golden .deck-bullets li{margin:.15em 0}
  .ch4-golden .ch4-aside{flex:1;display:flex;flex-direction:column;gap:.45vh;margin-top:.35vh;padding-top:.55vh;border-top:1px solid rgba(var(--ink-rgb),.12);min-height:0}
  .ch4-golden .ch4-aside-head{font-family:var(--mono);font-size:8px;letter-spacing:.1em;text-transform:uppercase;opacity:.42;margin-bottom:.2vh;flex-shrink:0}
  .ch4-golden .golden-matrix-wrap,
  .ch5-outlier .golden-matrix-wrap{display:flex;flex:1;min-height:0;align-items:stretch;gap:0;overflow:visible}
  .ch4-golden .golden-matrix-wrap .deck-chart.matrix,
  .ch5-outlier .golden-matrix-wrap .deck-chart.matrix{flex:1;min-width:0;min-height:0;overflow:visible}
  .ch4-golden .golden-ref-rail,
  .ch5-outlier .golden-ref-rail{width:min(10.5vw,118px);flex-shrink:0;display:flex;flex-direction:column;border-left:1px solid #ececec;padding:0 0 0 7px;margin-left:2px}
  .ch5-outlier .golden-ref-rail.is-compact{width:min(10vw,108px)}
  .ch4-golden .golden-ref-rail-head,
  .ch5-outlier .golden-ref-rail-head{font-family:var(--mono);font-size:7px;letter-spacing:.12em;text-transform:uppercase;color:#999;text-align:center;padding:2px 0 6px;flex-shrink:0}
  .ch4-golden .golden-ref-rail-body,
  .ch5-outlier .golden-ref-rail-body{flex:1;display:grid;grid-template-rows:repeat(4,1fr);gap:3px;padding-top:8.5%;min-height:0}
  .golden-ref-rail.is-compact .golden-ref-rail-body{padding-top:7.2%}
  .ch4-golden .golden-ref-cell,
  .ch5-outlier .golden-ref-cell{display:flex;gap:5px;align-items:stretch;min-height:0;padding:2px 0}
  .ch4-golden .golden-ref-stripe,
  .ch5-outlier .golden-ref-stripe{width:5px;border-radius:2px;flex-shrink:0;opacity:.92}
  .ch4-golden .golden-ref-body,
  .ch5-outlier .golden-ref-body{flex:1;display:flex;flex-direction:column;justify-content:center;gap:1px;min-width:0}
  .ch4-golden .golden-ref-metric,
  .ch5-outlier .golden-ref-metric{font-family:var(--mono);font-size:max(7px,.58vw);font-weight:600;letter-spacing:.04em;line-height:1.2;display:flex;align-items:baseline;gap:.2vw;flex-wrap:wrap}
  .ch4-golden .golden-ref-unit,
  .ch5-outlier .golden-ref-unit{font-size:max(6px,.5vw);font-weight:500;opacity:.55;letter-spacing:.02em}
  .ch4-golden .golden-ref-items,
  .ch5-outlier .golden-ref-items{display:flex;flex-direction:column;gap:1px}
  .ch4-golden .golden-ref-item,
  .ch5-outlier .golden-ref-item{display:grid;grid-template-columns:auto 1fr;gap:0 4px;align-items:baseline;line-height:1.25}
  .ch4-golden .golden-ref-val,
  .ch5-outlier .golden-ref-val{font-family:var(--mono);font-size:max(7px,.56vw);font-weight:600;letter-spacing:.02em;text-align:right;min-width:2.2em}
  .ch4-golden .golden-ref-lbl,
  .ch5-outlier .golden-ref-lbl{font-size:max(7px,.54vw);color:#666;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ch4-golden .golden-ref-rail-foot,
  .ch5-outlier .golden-ref-rail-foot{font-family:var(--mono);font-size:max(6px,.5vw);letter-spacing:.03em;color:#bbb;text-align:center;line-height:1.35;padding:5px 0 2px;flex-shrink:0}
  .golden-ref-rail.is-compact .golden-ref-val{font-size:max(6px,.52vw);min-width:2em}
  .golden-ref-rail.is-compact .golden-ref-lbl{font-size:max(6px,.5vw)}
  .ch4-golden .ch4-golden-list{display:flex;flex-direction:column;gap:.42vh;flex:1;min-height:0;overflow:auto;padding-right:.15vw}
  .ch4-golden .ch4-golden-list::-webkit-scrollbar{width:3px}
  .ch4-golden .ch4-golden-list::-webkit-scrollbar-thumb{background:rgba(var(--ink-rgb),.18);border-radius:2px}
  .ch4-golden .ch4-golden-track{display:flex;flex-direction:column;gap:.12vh;width:100%;padding:.55vh .5vw;border:1px solid rgba(var(--ink-rgb),.12);border-radius:5px;background:rgba(var(--ink-rgb),.03);cursor:pointer;text-align:left;color:inherit;font:inherit;transition:background .2s,border-color .2s,box-shadow .2s}
  .ch4-golden .ch4-golden-track:hover{background:rgba(117,161,199,.1);border-color:rgba(117,161,199,.4)}
  .ch4-golden .ch4-golden-track.is-active{border-color:rgba(117,161,199,.55);background:rgba(117,161,199,.14);box-shadow:inset 0 0 0 1px rgba(117,161,199,.22)}
  .ch4-golden .ch4-gt-tier{font-family:var(--mono);font-size:7px;letter-spacing:.12em;text-transform:uppercase;opacity:.55;color:#75a1c7}
  .ch4-golden .ch4-gt-title{font-family:var(--serif-zh);font-size:max(12px,.88vw);font-weight:600;line-height:1.25}
  .ch4-golden .ch4-gt-artist{font-size:max(10px,.76vw);opacity:.62;line-height:1.3}
  .ch4-golden .ch4-gt-metrics{font-family:var(--mono);font-size:max(9px,.68vw);letter-spacing:.03em;opacity:.72;margin-top:.1vh}
  .ch4-golden .ch4-gt-meta{font-family:var(--mono);font-size:max(8px,.64vw);opacity:.45}
  .ch4-golden .ch4-gt-play{font-family:var(--mono);font-size:max(9px,.68vw);letter-spacing:.06em;opacity:.55;margin-top:.15vh;color:#499894}
  .ch4-golden .chart-panel{padding:12px 14px 10px;overflow:visible}
  .ch4-golden .deck-chart.matrix{min-height:70vh}
  .ch6-heat .deck-text{display:flex;flex-direction:column;gap:1.35vh;min-height:0;max-height:76vh;padding-right:.8vw}
  .ch6-heat .h1-zh{margin-bottom:.65vh;line-height:1.14;font-size:2.15vw}
  .ch6-heat .deck-lead-compact{-webkit-line-clamp:2;margin-bottom:.5vh;line-height:1.55!important;flex-shrink:0}
  .ch6-heat .ch6-aside{flex:1;display:flex;flex-direction:column;gap:.7vh;margin-top:.65vh;padding-top:.85vh;border-top:1px solid rgba(var(--paper-rgb),.12);min-height:0;overflow:hidden}
  .ch6-heat .ch6-tl-label{font-family:var(--mono);font-size:7px;letter-spacing:.12em;text-transform:uppercase;opacity:.45;margin-bottom:.45vh;flex-shrink:0}
  .ch6-heat .ch6-tl-hint{margin:0 0 .35vh;font-family:var(--mono);font-size:max(7px,.56vw);letter-spacing:.06em;opacity:.42;flex-shrink:0}
  .ch6-heat .ch6-timeline{flex:1;overflow:auto;padding:.65vh .25vw .5vh 0;min-height:0;display:flex;flex-direction:column;gap:.15vh}
  .ch6-heat .ch6-timeline::-webkit-scrollbar{width:3px}
  .ch6-heat .ch6-timeline::-webkit-scrollbar-thumb{background:rgba(var(--paper-rgb),.22);border-radius:2px}
  .ch6-heat .ch6-tl-item{display:grid;grid-template-columns:10px 1fr;gap:0 .6vw;position:relative;padding-bottom:.85vh}
  .ch6-heat .ch6-tl-item[data-ch6-year]{cursor:pointer}
  .ch6-heat .ch6-tl-item[data-ch6-year]:hover .ch6-tl-body{background:rgba(117,161,199,.05)}
  .ch6-heat .ch6-tl-item.is-tl-active .ch6-tl-marker{background:#75a1c7;box-shadow:0 0 0 3px rgba(117,161,199,.28)}
  .ch6-heat .ch6-tl-item.is-tl-active:not(.is-key) .ch6-tl-body{border-left:2px solid rgba(117,161,199,.35);padding-left:.45vw}
  .ch6-heat .ch6-tl-item.is-tl-active .ch6-tl-year{color:#9ec5e8}
  .ch6-heat .ch6-tl-item:last-child{padding-bottom:0}
  .ch6-heat .ch6-tl-item:not(:last-child)::before{content:"";position:absolute;left:4px;top:8px;bottom:0;width:1px;background:rgba(var(--paper-rgb),.18)}
  .ch6-heat .ch6-tl-marker{width:7px;height:7px;border-radius:50%;background:rgba(117,161,199,.55);border:1px solid rgba(var(--paper-rgb),.25);margin-top:.4vh;position:relative;z-index:1;flex-shrink:0}
  .ch6-heat .ch6-tl-item.is-key .ch6-tl-marker{width:9px;height:9px;background:#75a1c7;border:1.5px solid rgba(255,255,255,.35);box-shadow:0 0 0 3px rgba(117,161,199,.22);margin-top:.32vh}
  .ch6-heat .ch6-tl-item.is-key .ch6-tl-body{padding:.45vh .5vw .5vh;border-left:2px solid rgba(117,161,199,.45);background:rgba(117,161,199,.08);border-radius:0 4px 4px 0}
  .ch6-heat .ch6-tl-body{min-width:0}
  .ch6-heat .ch6-tl-headline{display:flex;align-items:center;flex-wrap:wrap;gap:.3vw .4vw;margin-bottom:.18vh;line-height:1.25}
  .ch6-heat .ch6-tl-year{font-family:var(--mono);font-size:max(9px,.7vw);font-weight:600;color:rgba(117,161,199,.85);letter-spacing:.04em;flex-shrink:0}
  .ch6-heat .ch6-tl-item.is-key .ch6-tl-year{color:#9ec5e8;font-size:max(10px,.74vw)}
  .ch6-heat .ch6-tl-title{font-family:var(--serif-zh);font-size:max(11px,.84vw);font-weight:600;opacity:.92}
  .ch6-heat .ch6-tl-item.is-key .ch6-tl-title{opacity:1}
  .ch6-heat .ch6-tl-badge{font-family:var(--mono);font-size:max(6px,.52vw);letter-spacing:.08em;text-transform:uppercase;padding:.1vh .28vw;border:1px solid rgba(117,161,199,.45);color:#9ec5e8;border-radius:2px;line-height:1.3}
  .ch6-heat .ch6-tl-text{margin:0;font-size:max(9px,.7vw);line-height:1.5;opacity:.75}
  .ch6-heat .ch6-tl-item.is-key .ch6-tl-text{opacity:.88}
  .ch6-heat .chart-panel{padding:12px 14px 10px}
  .ch6-heat .deck-chart.heatmap{min-height:70vh}
  #story-drawer{position:fixed;left:0;top:50%;z-index:180;width:min(340px,36vw);max-height:72vh;overflow:auto;padding:2.2vh 1.4vw 2vh 1.6vw;background:rgba(var(--ink-rgb),.96);color:var(--paper);border:1px solid rgba(var(--paper-rgb),.12);border-left:none;border-radius:0 10px 10px 0;box-shadow:8px 0 40px rgba(0,0,0,.22);transform:translate(-108%,-50%);transition:transform .5s cubic-bezier(.22,1,.36,1);backdrop-filter:blur(14px);pointer-events:none;opacity:0}
  #story-drawer.is-on{transform:translate(0,-50%);pointer-events:auto;opacity:1}
  #story-drawer .sd-close{position:absolute;top:.8vh;right:.6vw;background:transparent;border:none;color:inherit;font-size:20px;line-height:1;cursor:pointer;opacity:.45;padding:4px 8px}
  #story-drawer .sd-close:hover{opacity:.9}
  #story-drawer .sp-title{font-family:var(--serif-zh);font-size:max(16px,1.1vw);font-weight:600;margin-bottom:.6vh;padding-right:1.4em}
  #story-drawer .sp-head{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-bottom:.4vh}
  #story-drawer p{font-size:max(12px,.88vw);line-height:1.55;margin:.35vh 0;opacity:.88}
  #story-drawer .sp-num{font-family:var(--mono);font-size:10px;opacity:.5;margin-top:.6vh}
  .ch1-genre .deck-lead{-webkit-line-clamp:unset;display:block;overflow:visible;line-height:1.62!important}
  .ch1-genre .deck-text{display:flex;flex-direction:column;gap:1.4vh;min-height:0;justify-content:flex-start}
  .ch1-genre .ch1-aside{margin-top:.6vh;padding-top:1vh;border-top:1px solid rgba(var(--ink-rgb),.12);display:flex;flex-direction:column;gap:.7vh}
  .ch1-genre .ch1-hint{font-family:var(--mono);font-size:9px;letter-spacing:.1em;opacity:.55;margin:0}
  .ch1-genre .ch1-stats-head{font-family:var(--mono);font-size:8px;letter-spacing:.14em;text-transform:uppercase;opacity:.45}
  .ch1-genre .ch1-stats{display:flex;flex-direction:column;gap:.45vh}
  .ch1-genre .ch1-stat{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:.45vw;padding:.5vh .4vw;border:1px solid rgba(var(--ink-rgb),.1);border-radius:4px;background:rgba(var(--ink-rgb),.03)}
  .ch1-genre .ch1-stat-swatch{width:9px;height:9px;border-radius:2px;flex-shrink:0}
  .ch1-genre .ch1-stat-main{display:flex;flex-direction:column;gap:.1vh;min-width:0}
  .ch1-genre .ch1-stat-genre{font-family:var(--serif-zh);font-size:max(12px,.88vw);font-weight:600;line-height:1.2}
  .ch1-genre .ch1-stat-val{font-family:var(--mono);font-size:8px;letter-spacing:.06em;opacity:.55}
  .ch1-genre .ch1-stat-pct{font-family:var(--mono);font-size:10px;letter-spacing:.04em;opacity:.7;text-align:right}
  .ch1-genre .ch1-footnote{font-family:var(--mono);font-size:8px;letter-spacing:.06em;opacity:.42;margin:0;line-height:1.4}
  .ch3-artist .deck-lead{-webkit-line-clamp:unset;display:block;overflow:visible;line-height:1.55!important;margin-bottom:0;opacity:.82}
  .ch3-artist .deck-text{display:flex;flex-direction:column;gap:.75vh;min-height:0;justify-content:flex-start;max-height:76vh}
  .ch3-artist .ch3-aside{flex:1;display:flex;flex-direction:column;gap:.55vh;margin-top:.35vh;padding-top:.65vh;border-top:1px solid rgba(var(--ink-rgb),.12);min-height:0}
  .ch3-artist .ch3-aside-head{font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;opacity:.45;margin-bottom:.15vh}
  .ch3-artist .ch3-artist-list{display:flex;flex-direction:column;gap:.42vh;flex:1;min-height:0;overflow:auto;padding-right:.2vw}
  .ch3-artist .ch3-artist-list::-webkit-scrollbar{width:3px}
  .ch3-artist .ch3-artist-list::-webkit-scrollbar-thumb{background:rgba(var(--ink-rgb),.18);border-radius:2px}
  .ch3-artist .ch3-artist-mini{display:grid;grid-template-columns:50px 1fr;gap:.45vw .55vw;padding:.55vh .5vw;border:1px solid rgba(var(--ink-rgb),.11);border-radius:6px;background:rgba(var(--ink-rgb),.025);cursor:pointer;text-align:left;color:inherit;font:inherit;transition:background .2s,border-color .2s,opacity .25s,box-shadow .2s}
  .ch3-artist .ch3-artist-mini:hover{background:rgba(73,152,148,.08);border-color:rgba(73,152,148,.35)}
  .ch3-artist .ch3-artist-mini.is-active{border-color:rgba(73,152,148,.55);background:rgba(73,152,148,.12);box-shadow:inset 0 0 0 1px rgba(73,152,148,.2)}
  .ch3-artist.has-artist-panel .ch3-artist-mini:not(.is-active){opacity:.42}
  .ch3-artist .ch3-artist-thumb{width:50px;height:50px;border-radius:5px;object-fit:cover;background:#1a1a1a;grid-row:1/span 2;align-self:center}
  .ch3-artist .ch3-artist-mini-cap{display:flex;flex-direction:column;gap:.18vh;min-width:0}
  .ch3-artist .ch3-artist-mini-row{display:flex;align-items:center;justify-content:space-between;gap:.35vw}
  .ch3-artist .ch3-artist-mini-name{font-family:var(--serif-zh);font-size:max(12px,.9vw);font-weight:600;line-height:1.2}
  .ch3-artist .ch3-artist-mini-tag{font-family:var(--mono);font-size:7px;letter-spacing:.06em;padding:2px 5px;border-radius:3px;background:color-mix(in srgb,var(--tag,#999) 18%,transparent);color:var(--tag,#666);border:1px solid color-mix(in srgb,var(--tag,#999) 35%,transparent);white-space:nowrap}
  .ch3-artist .ch3-artist-mini-meta{font-family:var(--mono);font-size:8px;letter-spacing:.04em;opacity:.58}
  .ch3-artist .ch3-artist-mini-blurb{font-size:max(10px,.76vw);line-height:1.4;opacity:.62;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .ch3-artist .ch3-bridge{font-size:max(11px,.84vw)!important;line-height:1.48!important;opacity:.68;margin:0;padding:.55vh 0 0;border-top:1px dashed rgba(var(--ink-rgb),.14);font-style:italic}
  .ch3-artist .deck-chart.wide{min-height:64vh;flex:1}
  .ch3-artist .chart-panel-head{flex-direction:column;align-items:flex-start;gap:3px;margin-bottom:8px;opacity:1;text-transform:none}
  .ch3-artist .chart-panel-title{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;opacity:.55}
  .ch3-artist .chart-panel-unit{font-family:var(--mono);font-size:9px;letter-spacing:.05em;opacity:.8;color:#555;text-transform:none;line-height:1.35}
  .ch5-outlier .deck-text{display:flex;flex-direction:column;gap:.65vh;padding-right:1vw;min-height:0}
  .ch5-outlier .h1-zh{font-size:2.35vw;line-height:1.1;margin-bottom:.25vh}
  .ch5-outlier .deck-lead-compact{-webkit-line-clamp:3;margin-bottom:.15vh;line-height:1.5!important}
  .ch5-outlier .ch5-aside{flex:1;display:flex;flex-direction:column;gap:.55vh;margin-top:.5vh;padding-top:.75vh;border-top:1px solid rgba(var(--ink-rgb),.1);min-height:0;overflow:hidden}
  .ch5-outlier .ch5-aside-head{font-family:var(--mono);font-size:8px;letter-spacing:.1em;text-transform:uppercase;opacity:.42;margin-bottom:.15vh;flex-shrink:0}
  .ch5-outlier .ch5-radar-wrap{flex:1 1 auto;min-height:200px;max-height:32vh;width:100%;position:relative;margin:.2vh 0}
  .ch5-outlier .ch5-radar{position:absolute;inset:0;width:100%!important;height:100%!important;min-height:unset;max-height:unset}
  .ch5-outlier .ch5-outlier-notes{display:grid;grid-template-columns:repeat(3,1fr);gap:.4vw;margin-top:.1vh;flex-shrink:0}
  .ch5-outlier .ch5-outlier-notes .ch5-hi{font-size:max(10px,.76vw);line-height:1.38;padding:.5vh .4vw;border-left:2px solid #4e79a7;background:rgba(78,121,167,.05);border-radius:0 3px 3px 0}
  .ch5-outlier .ch5-outlier-notes .ch5-hi strong{display:block;color:#2166ac;font-size:max(11px,.82vw)}
  .ch5-outlier .ch5-outlier-notes .ch5-hi span{display:block;color:#c44e52;opacity:.72;font-family:var(--mono);font-size:max(9px,.68vw);margin-top:.12vh}
  .ch5-outlier .ch5-billie-track{display:flex;flex-direction:column;gap:.15vh;width:100%;margin-top:.45vh;padding:.65vh .55vw;border:1px solid rgba(78,121,167,.28);border-radius:6px;background:rgba(78,121,167,.05);cursor:pointer;text-align:left;color:inherit;font:inherit;transition:background .2s,border-color .2s,box-shadow .2s;flex-shrink:0}
  .ch5-outlier .ch5-billie-track:hover{background:rgba(78,121,167,.1);border-color:rgba(78,121,167,.42)}
  .ch5-outlier .ch5-billie-track.is-active{border-color:rgba(78,121,167,.55);background:rgba(78,121,167,.12);box-shadow:inset 0 0 0 1px rgba(78,121,167,.16)}
  .ch5-outlier .ch5-bt-label{font-family:var(--mono);font-size:7px;letter-spacing:.12em;text-transform:uppercase;opacity:.5;color:#4e79a7}
  .ch5-outlier .ch5-bt-title{font-family:var(--serif-zh);font-size:max(13px,.92vw);font-weight:600;line-height:1.25;color:#2166ac}
  .ch5-outlier .ch5-bt-artist{font-size:max(10px,.74vw);opacity:.62;line-height:1.3}
  .ch5-outlier .ch5-bt-play{font-family:var(--mono);font-size:max(9px,.68vw);letter-spacing:.06em;opacity:.55;margin-top:.2vh;color:#4e79a7}
  .ch5-outlier .chart-panel{padding:12px 14px 10px;overflow:visible}
  .ch5-outlier .deck-chart.matrix{min-height:70vh}
  .ch7-style .deck-lead{-webkit-line-clamp:3}
  .ch7-style .deck-detail{-webkit-line-clamp:2}
  .ch7-style .ch7-aside{margin-top:.45vh;padding-top:.65vh;border-top:1px solid rgba(var(--ink-rgb),.12);flex-shrink:0;max-height:58vh;overflow:auto}
  .ch7-style .ch7-aside-head{font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;opacity:.45;margin-bottom:.4vh}
  .ch7-style .ch7-style-list{display:flex;flex-direction:column;gap:.15vh}
  .ch7-style .ch7-style-card{display:grid;grid-template-columns:8px 1fr;gap:0 .55vw;align-items:start;padding:.5vh 0 .55vh;border-bottom:1px dashed rgba(var(--ink-rgb),.1)}
  .ch7-style .ch7-style-card:last-child{border-bottom:none;padding-bottom:0}
  .ch7-style .ch7-style-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:.42vh}
  .ch7-style .ch7-style-main{min-width:0}
  .ch7-style .ch7-style-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.25vw .45vw;margin-bottom:.15vh;line-height:1.3}
  .ch7-style .ch7-style-name{font-weight:600;font-size:max(11px,.82vw);opacity:.9}
  .ch7-style .ch7-style-tag{font-family:var(--mono);font-size:max(8px,.66vw);letter-spacing:.04em;opacity:.52;white-space:nowrap}
  .ch7-style .ch7-style-track{font-size:max(10px,.76vw);opacity:.84;line-height:1.38}
  .ch7-style .ch7-style-pop{font-family:var(--mono);font-size:max(8px,.62vw);opacity:.5;margin-left:.35vw;letter-spacing:.02em}
  .ch7-style .ch7-style-metrics{font-family:var(--mono);font-size:max(8px,.64vw);opacity:.58;line-height:1.42;margin-top:.1vh;letter-spacing:.01em}
  .ch7-style .ch7-style-metrics--empty{opacity:.45;font-style:italic}
  .ch8-emotion .deck-text{display:flex;flex-direction:column;gap:0;min-height:0;max-height:78vh;overflow-y:auto;overflow-x:hidden;padding-right:.35vw;justify-content:flex-start}
  .ch8-emotion .deck-text::-webkit-scrollbar{width:3px}
  .ch8-emotion .deck-text::-webkit-scrollbar-thumb{background:rgba(var(--paper-rgb),.18);border-radius:2px}
  .ch8-emotion .kicker{margin-bottom:.1vh!important;opacity:.55}
  .ch8-emotion .h1-zh{margin-bottom:.4vh!important;line-height:1.08;font-size:2.35vw!important}
  .ch8-emotion .deck-lead-ch8{-webkit-line-clamp:unset;display:block;overflow:visible;margin:0 0 .55vh;line-height:1.55!important;opacity:.82;flex-shrink:0;font-size:max(12px,.88vw)!important}
  .ch8-emotion .deck-detail-ch8{-webkit-line-clamp:unset;display:block;overflow:visible;margin:0 0 .65vh;line-height:1.52!important;opacity:.68;flex-shrink:0;font-size:max(12px,.86vw)!important}
  .ch8-emotion .ch8-emotion-panel{display:flex;flex-direction:column;gap:.55vh;margin-top:.1vh;flex-shrink:0;width:100%}
  .ch8-emotion .ch8-aside-hint{margin:0;font-family:var(--mono);font-size:max(8px,.68vw);letter-spacing:.04em;opacity:.46;line-height:1.42;flex-shrink:0}
  .ch8-emotion .ch8-aside{display:none;flex-direction:column;gap:.85vh;flex-shrink:0;width:100%;padding:1.15vh .95vw 1vh;border:1px solid rgba(var(--paper-rgb),.16);border-radius:10px;background:rgba(0,0,0,.24);overflow:hidden;box-shadow:0 8px 28px rgba(0,0,0,.22)}
  .ch8-emotion .ch8-aside.is-visible{display:flex}
  .ch8-emotion .ch8-viz-wrap{position:relative;flex-shrink:0;width:100%;border-radius:8px;overflow:hidden;min-height:22vh}
  .ch8-emotion .ch8-viz{position:relative;border-radius:8px;overflow:hidden;border:1px solid rgba(var(--paper-rgb),.14);background:rgba(0,0,0,.25);line-height:0;height:100%;min-height:22vh}
  .ch8-emotion .ch8-viz svg{display:block;width:100%;height:100%;min-height:22vh;max-height:26vh;object-fit:cover}
  .ch8-emotion .ch8-viz--fallback{min-height:22vh;max-height:26vh;background:linear-gradient(135deg,rgba(78,121,167,.15),rgba(0,0,0,.35))}
  .ch8-emotion .ch8-viz-cap{position:absolute;left:.65vw;bottom:.55vh;font-family:var(--mono);font-size:max(9px,.72vw);letter-spacing:.1em;text-transform:uppercase;color:rgba(158,197,232,.92);opacity:.95;pointer-events:none;line-height:1.25;text-shadow:0 1px 4px rgba(0,0,0,.65)}
  .ch8-emotion .ch8-track-play{display:flex;flex-direction:column;gap:.22vh;width:100%;padding:1.1vh .9vw;border:1px solid rgba(78,121,167,.36);border-radius:8px;background:rgba(78,121,167,.09);cursor:pointer;text-align:left;color:inherit;font:inherit;transition:background .2s,border-color .2s,box-shadow .2s;flex-shrink:0}
  .ch8-emotion .ch8-track-play:hover{background:rgba(78,121,167,.15);border-color:rgba(78,121,167,.52)}
  .ch8-emotion .ch8-track-play.is-active{border-color:rgba(158,197,232,.55);background:rgba(78,121,167,.18);box-shadow:inset 0 0 0 1px rgba(78,121,167,.24)}
  .ch8-emotion .ch8-tp-label{font-family:var(--mono);font-size:max(8px,.64vw);letter-spacing:.12em;text-transform:uppercase;opacity:.5;color:#9ec5e8;line-height:1.2}
  .ch8-emotion .ch8-tp-title{font-family:var(--serif-zh);font-size:max(20px,1.42vw);font-weight:600;line-height:1.18;font-style:italic;margin-top:.12vh}
  .ch8-emotion .ch8-tp-artist{font-size:max(12px,.88vw);opacity:.58;line-height:1.34;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-top:.08vh}
  .ch8-emotion .ch8-tp-metrics{font-family:var(--mono);font-size:max(11px,.82vw);letter-spacing:.03em;color:#9ec5e8;opacity:.82;margin-top:.28vh;line-height:1.25}
  .ch8-emotion .ch8-tp-play{font-family:var(--mono);font-size:max(11px,.82vw);letter-spacing:.06em;opacity:.62;margin-top:.15vh;color:#9ec5e8;line-height:1.2}
  .ch8-emotion .ch8-anchor-note{margin:0;font-size:max(13px,.94vw);line-height:1.52;opacity:.74;flex-shrink:0}
  .ch8-emotion .ch8-anchor-note strong{color:#9ec5e8;font-weight:600}
  .ch8-emotion .ch8-aside-foot{margin-top:.1vh;padding-top:.4vh;border-top:1px solid rgba(var(--paper-rgb),.1);font-family:var(--mono);font-size:max(8px,.62vw);letter-spacing:.14em;text-transform:uppercase;text-align:center;opacity:.34;line-height:1.2;flex-shrink:0}
  .ch8-emotion .chart-panel{padding:12px 14px 10px}
  .ch8-emotion .deck-chart{min-height:68vh}
  .ch9-explicit .deck-text{display:flex;flex-direction:column;gap:1.25vh;min-height:0;max-height:76vh;overflow:hidden;padding-right:.5vw}
  .ch9-explicit .deck-lead-compact{-webkit-line-clamp:3;margin-bottom:.35vh;line-height:1.62!important;flex-shrink:0}
  .ch9-explicit .ch9-explicit-aside{flex:1;display:flex;flex-direction:column;gap:1vh;margin-top:.55vh;min-height:0;overflow:visible;padding-right:.15vw}
  .ch9-explicit .ch9-aside-label{font-family:var(--mono);font-size:max(8px,.66vw);letter-spacing:.12em;text-transform:uppercase;opacity:.42;margin-bottom:.2vh;flex-shrink:0}
  .ch9-explicit .ch9-peak-cards{display:flex;flex-direction:column;gap:.85vh;flex:1;justify-content:flex-start;padding:.25vh 0}
  .ch9-explicit .ch9-peak-card{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto auto;gap:.22vh .65vw;padding:1vh .75vw;border:1px solid color-mix(in srgb,var(--ch9-accent,#4e79a7) 28%,transparent);border-radius:8px;background:color-mix(in srgb,var(--ch9-accent,#4e79a7) 6%,transparent);flex-shrink:0;cursor:pointer;opacity:.42;transition:opacity .32s,background .28s,border-color .28s,box-shadow .28s,transform .28s}
  .ch9-explicit .ch9-peak-card .ch9-peak-count,
  .ch9-explicit .ch9-peak-card .ch9-peak-meta,
  .ch9-explicit .ch9-peak-card .ch9-peak-note{opacity:0;max-height:0;overflow:hidden;margin:0;padding:0;line-height:0;transition:opacity .28s,max-height .28s}
  .ch9-explicit .ch9-peak-card.is-active{opacity:1!important;border-color:color-mix(in srgb,var(--ch9-accent,#4e79a7) 58%,transparent);background:color-mix(in srgb,var(--ch9-accent,#4e79a7) 16%,transparent);box-shadow:0 3px 16px color-mix(in srgb,var(--ch9-accent,#4e79a7) 22%,transparent);transform:translateX(4px)}
  .ch9-explicit .ch9-peak-card.is-active .ch9-peak-count,
  .ch9-explicit .ch9-peak-card.is-active .ch9-peak-meta,
  .ch9-explicit .ch9-peak-card.is-active .ch9-peak-note{opacity:1;max-height:8vh;line-height:inherit}
  .ch9-explicit .ch9-peak-genre{font-weight:600;font-size:max(12px,.88vw);color:var(--ch9-accent,#4e79a7);grid-column:1;grid-row:1;line-height:1.3}
  .ch9-explicit .ch9-peak-count{font-family:var(--serif-zh);font-size:max(21px,1.5vw);font-weight:700;line-height:1.05;color:var(--ch9-accent,#4e79a7);grid-column:2;grid-row:1/3;align-self:center;transition:opacity .28s,max-height .28s}
  .ch9-explicit .ch9-peak-card.is-active .ch9-peak-count{font-size:max(24px,1.72vw)}
  .ch9-explicit .ch9-peak-meta{font-family:var(--mono);font-size:max(8px,.66vw);letter-spacing:.04em;opacity:.52;grid-column:1;grid-row:2;transition:opacity .28s,max-height .28s}
  .ch9-explicit .ch9-peak-note{font-size:max(10px,.78vw);opacity:.78;line-height:1.48;grid-column:1/3;grid-row:3;margin-top:.2vh;transition:opacity .28s,max-height .28s}
  .ch9-explicit .ch9-aside-hint{margin:.55vh 0 0;font-family:var(--mono);font-size:max(9px,.7vw);letter-spacing:.04em;opacity:.44;line-height:1.5;flex-shrink:0}
  .ch9-explicit .chart-panel{padding:12px 14px 14px;overflow:visible}
  .ch9-explicit .chart-panel-head.ch9-chart-head{flex-direction:row;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:4px;opacity:1;text-transform:none}
  .ch9-explicit .chart-panel-head-col{display:flex;flex-direction:column;align-items:flex-start;gap:3px;min-width:0;flex:1}
  .ch9-explicit .chart-panel-title{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;opacity:.55}
  .ch9-explicit .chart-panel-unit{font-family:var(--mono);font-size:9px;letter-spacing:.04em;opacity:.78;color:#555;text-transform:none;line-height:1.4;max-width:100%}
  .ch9-explicit .ch9-bubble-legend{display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0;padding-top:1px}
  .ch9-explicit .ch9-bl-caption{font-family:var(--mono);font-size:7px;letter-spacing:.04em;color:#888;line-height:1.2;white-space:nowrap}
  .ch9-explicit .ch9-bl-steps{display:flex;align-items:center;gap:5px}
  .ch9-explicit .ch9-bl-item{display:inline-flex;align-items:center;gap:2px;font-family:var(--mono);font-size:7px;color:#666;line-height:1}
  .ch9-explicit .ch9-bl-dot{width:var(--s,8px);height:var(--s,8px);border-radius:50%;background:#888;opacity:.42;flex-shrink:0;display:inline-block}
  .ch9-explicit .deck-chart.facet{min-height:66vh;padding-bottom:4px}
  .ch10-paradox .deck-text{display:flex;flex-direction:column;gap:1.1vh;min-height:0;max-height:76vh;overflow:hidden;padding-right:.5vw}
  .ch10-paradox .deck-lead-compact{-webkit-line-clamp:2;margin-bottom:.35vh;line-height:1.58!important;flex-shrink:0}
  .ch10-paradox .ch10-paradox-aside{flex:1;display:flex;flex-direction:column;gap:.85vh;margin-top:.45vh;min-height:0;overflow:auto;padding-right:.2vw}
  .ch10-paradox .ch10-paradox-aside::-webkit-scrollbar{width:3px}
  .ch10-paradox .ch10-paradox-aside::-webkit-scrollbar-thumb{background:rgba(var(--paper-rgb),.18);border-radius:2px}
  .ch10-paradox .ch10-paradox-cards{display:flex;flex-direction:column;gap:.78vh;flex-shrink:0}
  .ch10-paradox .ch10-paradox-card{display:flex;flex-direction:column;gap:.28vh;padding:.95vh .72vw;border:1px solid color-mix(in srgb,var(--ch10-accent,#ff9d9a) 32%,transparent);border-radius:8px;background:color-mix(in srgb,var(--ch10-accent,#ff9d9a) 7%,transparent);flex-shrink:0;cursor:pointer;opacity:.42;transition:opacity .32s,background .28s,border-color .28s,box-shadow .28s,transform .28s}
  .ch10-paradox .ch10-paradox-card .ch10-paradox-pct,
  .ch10-paradox .ch10-paradox-card .ch10-paradox-note,
  .ch10-paradox .ch10-paradox-card .ch10-paradox-compare{opacity:0;max-height:0;overflow:hidden;margin:0;padding:0;line-height:0;transition:opacity .28s,max-height .28s}
  .ch10-paradox .ch10-paradox-card.is-active{opacity:1!important;border-color:color-mix(in srgb,var(--ch10-accent,#ff9d9a) 55%,transparent);background:color-mix(in srgb,var(--ch10-accent,#ff9d9a) 15%,transparent);box-shadow:0 3px 16px color-mix(in srgb,var(--ch10-accent,#ff9d9a) 20%,transparent);transform:translateX(4px)}
  .ch10-paradox .ch10-paradox-card.is-active .ch10-paradox-pct,
  .ch10-paradox .ch10-paradox-card.is-active .ch10-paradox-note,
  .ch10-paradox .ch10-paradox-card.is-active .ch10-paradox-compare{opacity:1;max-height:12vh;line-height:inherit}
  .ch10-paradox .ch10-paradox-kicker{font-family:var(--mono);font-size:max(7px,.58vw);letter-spacing:.12em;text-transform:uppercase;color:var(--ch10-accent,#ff9d9a);opacity:.88;line-height:1.35}
  .ch10-paradox .ch10-paradox-pct{font-family:var(--serif-zh);font-size:max(22px,1.55vw);font-weight:700;line-height:1.1;color:var(--ch10-accent,#ff9d9a);transition:opacity .28s,max-height .28s}
  .ch10-paradox .ch10-paradox-card.is-active .ch10-paradox-pct{font-size:max(26px,1.85vw)}
  .ch10-paradox .ch10-paradox-note{font-size:max(10px,.78vw);opacity:.78;line-height:1.48;transition:opacity .28s,max-height .28s}
  .ch10-paradox .ch10-paradox-compare{font-family:var(--mono);font-size:max(8px,.66vw);letter-spacing:.03em;opacity:.52;margin-top:.15vh;line-height:1.4;transition:opacity .28s,max-height .28s}
  .ch10-paradox .ch10-aside-hint{margin:.55vh 0 0;font-family:var(--mono);font-size:max(9px,.7vw);letter-spacing:.04em;opacity:.44;line-height:1.5;flex-shrink:0}
  .ch10-paradox .chart-panel{padding:12px 14px 12px}
  .ch10-paradox .chart-panel-head{flex-direction:column;align-items:flex-start;gap:3px;margin-bottom:6px;opacity:1;text-transform:none}
  .ch10-paradox .chart-panel-title{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;opacity:.55}
  .ch10-paradox .chart-panel-unit{font-family:var(--mono);font-size:9px;letter-spacing:.05em;opacity:.75;color:#555;text-transform:none;line-height:1.35}
  .ch10-paradox .deck-chart.ratio{min-height:66vh}
  #genre-showcase{position:fixed;left:0;bottom:10vh;top:auto;z-index:185;width:min(300px,32vw);max-height:58vh;overflow:auto;overflow-x:hidden;background:var(--paper);color:var(--ink);border:1px solid rgba(var(--ink-rgb),.1);border-left:none;border-radius:0 10px 10px 0;box-shadow:8px 0 40px rgba(0,0,0,.18);transform:translateX(-108%);transition:transform .5s cubic-bezier(.22,1,.36,1),opacity .4s;opacity:0;pointer-events:none}
  #genre-showcase.is-visible{transform:translateX(0);opacity:1;pointer-events:auto}
  #genre-showcase .gs-close{position:absolute;top:.6vh;right:.5vw;z-index:2;background:rgba(0,0,0,.35);border:none;color:#fff;font-size:18px;line-height:1;width:28px;height:28px;border-radius:50%;cursor:pointer;opacity:.85}
  #genre-showcase .gs-img-wrap{height:22vh;min-height:130px;background:#1a1a1a center/cover no-repeat}
  #genre-showcase .gs-cap{padding:1.4vh 1.1vw 1.6vh}
  #genre-showcase .gs-name{font-family:var(--serif-zh);font-size:max(18px,1.25vw);font-weight:600;line-height:1.2}
  #genre-showcase .gs-stats{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-top:.5vh}
  #genre-showcase .gs-track{font-family:var(--serif-zh);font-size:max(12px,.88vw);line-height:1.4;opacity:.85;margin-top:.5vh;color:#499894}
  #genre-showcase .gs-blurb{font-size:max(12px,.85vw);line-height:1.5;opacity:.78;margin-top:.7vh}
  #genre-showcase .gs-story{font-size:max(11px,.82vw);line-height:1.5;opacity:.72;margin-top:.8vh;padding-top:.8vh;border-top:1px solid rgba(var(--ink-rgb),.1)}
  #genre-showcase .gs-story-head{display:block;font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;opacity:.5;margin-bottom:.35vh}
  #genre-showcase.gs-mode-playlist{width:min(320px,34vw);max-height:62vh}
  #genre-showcase .gs-playlist{display:none;margin-top:.6vh;max-height:42vh;overflow-y:auto;padding-right:.3vw}
  #genre-showcase.gs-mode-playlist .gs-playlist{display:block}
  #genre-showcase .gs-pl-item{display:block;width:100%;text-align:left;padding:.65vh .55vw;margin-bottom:.4vh;border:1px solid rgba(var(--ink-rgb),.12);background:transparent;color:inherit;cursor:pointer;border-radius:4px;transition:background .2s,border-color .2s}
  #genre-showcase .gs-pl-item:hover,#genre-showcase .gs-pl-item.is-active{background:rgba(73,152,148,.14);border-color:rgba(73,152,148,.5)}
  #genre-showcase .gs-pl-item.is-loading{opacity:.65;pointer-events:wait}
  #genre-showcase .gs-pl-main{display:flex;align-items:center;justify-content:space-between;gap:.5vw}
  #genre-showcase .gs-pl-genre{font-family:var(--serif-zh);font-size:max(13px,.92vw);font-weight:600;line-height:1.25;color:var(--ink)}
  #genre-showcase .gs-pl-meta{display:block;font-size:max(10px,.78vw);opacity:.55;margin-top:.25vh;line-height:1.35}
  #genre-showcase .gs-pl-count{display:block;font-family:var(--mono);font-size:8px;letter-spacing:.08em;opacity:.4;margin-top:.15vh}
  #artist-showcase{position:fixed;left:max(1.4vw,12px);top:50%;bottom:auto;z-index:186;width:min(288px,calc(36vw - 1rem));max-height:min(66vh,620px);overflow:auto;background:var(--paper);color:var(--ink);border:1px solid rgba(var(--ink-rgb),.12);border-radius:0 10px 10px 0;box-shadow:8px 0 40px rgba(0,0,0,.2);transform:translate(-108%,-50%);transition:transform .48s cubic-bezier(.22,1,.36,1),opacity .35s;opacity:0;pointer-events:none}
  #artist-showcase.is-visible{transform:translate(0,-50%);opacity:1;pointer-events:auto}
  #artist-showcase .as-close{position:absolute;top:.6vh;right:.5vw;z-index:3;background:rgba(0,0,0,.45);border:none;color:#fff;font-size:18px;line-height:1;width:28px;height:28px;border-radius:50%;cursor:pointer;opacity:.9}
  #artist-showcase .as-hero{position:relative;min-height:128px;background:var(--as-accent,#499894) center/cover no-repeat;overflow:hidden}
  #artist-showcase .as-photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 18%}
  #artist-showcase .as-hero-cap{position:relative;z-index:1;padding:3.8vh 1.1vw 1.2vh;background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,.72) 100%)}
  #artist-showcase .as-name{font-family:var(--serif-zh);font-size:max(18px,1.25vw);font-weight:600;line-height:1.2;color:#fff;margin:0}
  #artist-showcase .as-genre{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.8;color:#fff;margin-top:.35vh}
  #artist-showcase .as-cap{padding:1.2vh 1.1vw 1.5vh}
  #artist-showcase .as-stats{font-family:var(--mono);font-size:9px;letter-spacing:.08em;opacity:.6;line-height:1.45}
  #artist-showcase .as-event{font-family:var(--mono);font-size:8px;letter-spacing:.12em;text-transform:uppercase;opacity:.45;margin-top:.6vh}
  #artist-showcase .as-story{font-size:max(12px,.85vw);line-height:1.55;opacity:.78;margin-top:.5vh}
  #artist-showcase .as-track-play{display:block;width:100%;margin-top:.9vh;padding:.65vh .5vw;border:1px solid rgba(73,152,148,.45);background:rgba(73,152,148,.1);color:inherit;border-radius:4px;cursor:pointer;font-family:var(--serif-zh);font-size:max(12px,.88vw);text-align:left;transition:background .2s}
  #artist-showcase .as-track-play:hover{background:rgba(73,152,148,.18)}
  #music-bar{position:fixed;right:2.2vw;bottom:2.2vh;transform:translateY(120%);width:min(340px,42vw);z-index:200;background:rgba(var(--ink-rgb),.94);color:var(--paper);border:1px solid rgba(var(--paper-rgb),.15);padding:12px 14px;display:grid;grid-template-columns:1fr auto;gap:8px 10px;align-items:start;transition:transform .45s cubic-bezier(.22,1,.36,1);backdrop-filter:blur(12px);border-radius:8px;box-shadow:0 12px 40px rgba(0,0,0,.25)}
  #music-bar.is-visible{transform:translateY(0)}
  .mp-track{font-family:var(--serif-zh);font-size:14px;line-height:1.25;grid-column:1}
  .mp-artist{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-top:2px;grid-column:1}
  .mp-mode{font-family:var(--mono);font-size:9px;letter-spacing:.1em;opacity:.4;grid-column:1;margin-top:2px}
  .mp-actions{display:flex;gap:6px;grid-column:2;grid-row:1/3}
  .mp-btn{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;background:transparent;border:1px solid rgba(var(--paper-rgb),.3);color:inherit;padding:4px 8px;cursor:pointer;border-radius:4px}
  #music-audio,#music-spotify{display:none}
  #music-spotify{width:100%;height:72px;border:none;border-radius:6px}
  #music-spotify:not(.hidden){display:block;grid-column:1/-1}
  #music-bar:has(#music-spotify:not(.hidden)){grid-template-rows:auto auto auto}
  .ch2-trend .deck-text{gap:1.1vh;line-height:1.58}
  .ch2-trend .h1-zh{margin-bottom:.35vh}
  .ch2-trend .gt-narrative{min-height:2.8em;margin-bottom:.15vh;line-height:1.62!important;opacity:1;transform:translateY(0);transition:opacity .32s ease,transform .32s ease}
  .ch2-trend .gt-narrative.is-changing{opacity:0;transform:translateY(8px)}
  .ch2-trend .gt-narrative.is-enter{opacity:1;transform:translateY(0)}
  .ch2-trend .deck-lead{-webkit-line-clamp:unset;display:block;overflow:visible}
  .ch2-trend .genre-trend-sidebar{margin-top:.65vh;padding-top:.15vh;display:flex;flex-direction:column;gap:.55vh;min-height:0;flex:1;position:relative;z-index:5;pointer-events:auto}
  .ch2-trend .genre-trend-sidebar.is-intro-disabled{opacity:.65}
  .ch2-trend .gt-sidebar-hint{font-family:var(--mono);font-size:max(8px,.64vw);letter-spacing:.1em;opacity:.48;margin:0 0 .15vh}
  .ch2-trend .genre-trend-notes{display:flex;flex-direction:column;gap:.55vh;pointer-events:auto}
  .ch2-trend .gt-note{display:block;width:100%;padding:.58vh .48vw;border:none;border-left:3px solid rgba(127,127,127,.4);background:rgba(127,127,127,.06);border-radius:0 4px 4px 0;font-size:max(11px,.76vw);line-height:1.45;cursor:pointer;text-align:left;font:inherit;color:inherit;transition:background .2s,box-shadow .2s,border-color .2s,opacity .2s}
  .ch2-trend .gt-note:hover:not(:disabled){filter:brightness(1.06)}
  .ch2-trend .gt-note--y2005{border-left-color:#c9a227;background:rgba(201,162,39,.09)}
  .ch2-trend .gt-note--y2005:hover:not(:disabled){background:rgba(201,162,39,.14)}
  .ch2-trend .gt-note--y2005.is-active{border-left-color:#a8841a;background:rgba(201,162,39,.18);box-shadow:inset 0 0 0 1px rgba(201,162,39,.28)}
  .ch2-trend .gt-note--y2016{border-left-color:#499894;background:rgba(73,152,148,.09)}
  .ch2-trend .gt-note--y2016:hover:not(:disabled){background:rgba(73,152,148,.14)}
  .ch2-trend .gt-note--y2016.is-active{border-left-color:#3a7a76;background:rgba(73,152,148,.18);box-shadow:inset 0 0 0 1px rgba(73,152,148,.28)}
  .ch2-trend .gt-note--y2020{border-left-color:#c97b6d;background:rgba(201,123,109,.09)}
  .ch2-trend .gt-note--y2020:hover:not(:disabled){background:rgba(201,123,109,.14)}
  .ch2-trend .gt-note--y2020.is-active{border-left-color:#b85c4f;background:rgba(201,123,109,.18);box-shadow:inset 0 0 0 1px rgba(201,123,109,.28)}
  .ch2-trend .gt-note--y2024{border-left-color:#4e79a7;background:rgba(78,121,167,.1)}
  .ch2-trend .gt-note--y2024:hover:not(:disabled){background:rgba(78,121,167,.15)}
  .ch2-trend .gt-note--y2024.is-active{border-left-color:#3d6289;background:rgba(78,121,167,.2);box-shadow:inset 0 0 0 1px rgba(78,121,167,.32)}
  .ch2-trend .gt-note--peak .gt-note-label{color:#9ec5e8}
  .ch2-trend .gt-note:disabled{opacity:.5;cursor:default}
  .ch2-trend .gt-note-year{font-family:var(--mono);font-size:max(7px,.58vw);letter-spacing:.12em;opacity:.52;display:block}
  .ch2-trend .gt-note-label{font-family:var(--serif-zh);font-weight:600;display:block;margin:.12vh 0}
  .ch2-trend .gt-note-story{opacity:.76;margin:0;font-size:max(9px,.72vw);line-height:1.38;display:block}
  .ch2-trend .deck-chart.wide{min-height:64vh;flex:1;overflow:visible}
  .ch2-trend .chart-panel{overflow:visible}
  .ch2-trend .chart-panel-head{flex-direction:column;align-items:flex-start;gap:3px;margin-bottom:8px;opacity:1;text-transform:none}
  .ch2-trend .chart-panel-title{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;opacity:.55}
  .ch2-trend .chart-panel-unit{font-family:var(--mono);font-size:10px;letter-spacing:.05em;opacity:.85;color:#555;text-transform:none;line-height:1.35}
"""

STORY_DRAWER = """
<div id="story-drawer" aria-live="polite" aria-hidden="true"></div>
"""

GENRE_SHOWCASE = """
<div id="genre-showcase" class="genre-showcase" aria-hidden="true">
  <button class="gs-close" type="button" aria-label="关闭">×</button>
  <div class="gs-img-wrap" role="img" aria-hidden="true"></div>
  <div class="gs-cap">
    <h3 class="gs-name"></h3>
    <p class="gs-stats"></p>
    <p class="gs-track"></p>
    <p class="gs-blurb"></p>
    <p class="gs-story"></p>
    <div class="gs-playlist" role="list"></div>
  </div>
</div>
"""

ARTIST_SHOWCASE = """
<div id="artist-showcase" class="artist-showcase" aria-hidden="true">
  <button class="as-close" type="button" aria-label="关闭">×</button>
  <div class="as-hero">
    <img class="as-photo" alt="" />
    <div class="as-hero-cap">
      <h3 class="as-name"></h3>
      <p class="as-genre"></p>
    </div>
  </div>
  <div class="as-cap">
    <p class="as-stats"></p>
    <p class="as-event"></p>
    <p class="as-story"></p>
    <button class="as-track-play" type="button" hidden>♪ 播放代表曲</button>
  </div>
</div>
"""

MUSIC_BAR = """
<div id="music-bar" aria-live="polite">
  <div class="mp-track">—</div>
  <div class="mp-artist"></div>
  <div class="mp-mode">点击播放</div>
  <div class="mp-actions">
    <button class="mp-btn" id="music-close" type="button" title="关闭">×</button>
  </div>
  <audio id="music-audio" preload="none"></audio>
  <iframe id="music-spotify" class="hidden" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
</div>
"""

DECK_PATCH = """
<script>window.__WEB_DATA_BASE = "../web/data/";</script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<script src="../web/js/tableau-theme.js?v=104"></script>
<script src="../web/js/chart-stories.js?v=122"></script>
<script src="../web/js/charts.js?v=174"></script>
<script src="js/genre-showcase.js?v=126"></script>
<script src="js/artist-showcase.js?v=126"></script>
<script src="js/story-panel.js?v=119"></script>
<script src="js/music-player.js?v=123"></script>
<script src="js/deck-main.js?v=134"></script>
"""


def main():
    DECK.mkdir(parents=True, exist_ok=True)
    (DECK / "js").mkdir(exist_ok=True)
    shutil.copy2(GUIZANG / "assets" / "motion.min.js", DECK / "motion.min.js")
    if (GUIZANG / "assets" / "motion.min.js").parent.exists():
        assets = DECK / "assets"
        assets.mkdir(exist_ok=True)
        shutil.copy2(GUIZANG / "assets" / "motion.min.js", assets / "motion.min.js")

    template = (GUIZANG / "assets" / "template.html").read_text(encoding="utf-8")
    template = template.replace(
        "<title>[必填] 替换为 PPT 标题 · Deck Title</title>",
        f"<title>{TITLE} · {SUBTITLE}</title>",
    )
    template = template.replace("<!-- SLIDES_HERE -->", build_slides())
    template = template.replace("</style>", EXTRA_CSS + "\n</style>", 1)
    template = template.replace("</body>", STORY_DRAWER + GENRE_SHOWCASE + ARTIST_SHOWCASE + MUSIC_BAR + DECK_PATCH + "\n</body>")

  # fix motion path for deck folder
    template = template.replace(
        "window.__currentSlideIndex = idx;",
        "window.__currentSlideIndex = idx;\n  if(window.__onDeckSlide) window.__onDeckSlide(idx);",
    )

    (DECK / "index.html").write_text(template, encoding="utf-8")
    print(f"Built {DECK / 'index.html'} ({TOTAL} slides)")


if __name__ == "__main__":
    main()
