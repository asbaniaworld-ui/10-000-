"""为各流派准备展示图：优先 Wikipedia 缩略图，失败则生成杂志风 SVG 海报。"""
import argparse
import json
import re
import urllib.parse
import urllib.request
import xml.sax.saxutils as xml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deck" / "images" / "genres"
DATA = ROOT / "web" / "data" / "genre_images.json"
FEATURED = ROOT / "web" / "data" / "featured_tracks.json"

WIKI = {
    "Pop": "Pop_music",
    "Rock": "Rock_music",
    "HipHop": "Hip_hop_music",
    "Latin": "Latin_music",
    "R&B": "Rhythm_and_blues",
    "TraditionalMusic": "Traditional_music",
    "Electronic": "Electronic_music",
    "Country": "Country_music",
    "Folk": "Folk_music",
    "Metal": "Heavy_metal_music",
    "NewAge": "New-age_music",
    "EasyListening": "Easy_listening",
    "Reggae": "Reggae",
    "Jazz": "Jazz",
    "Christian": "Contemporary_Christian_music",
    "Classical": "Classical_music",
    "Blues": "Blues",
}

BLURBS = {
    "Pop": "全球流媒体的王座流派，旋律记忆点与商业传播力的集合。",
    "Rock": "吉他、鼓点与反叛叙事，长期占据热门榜核心席位。",
    "HipHop": "节奏与说唱文化驱动，Explicit 与街头美学高度集中。",
    "Latin": "西语世界逆袭全球，舞曲律动与地域身份交织。",
    "R&B": "灵魂乐脉络下的情感表达，旋律细腻且制作精良。",
    "TraditionalMusic": "民族与传统乐器，在长尾曲库中保持文化多样性。",
    "Electronic": "合成器与电子节拍，俱乐部文化与流媒体播放紧密相连。",
    "Country": "叙事民谣与美国乡村根源，在主流榜中稳定存在。",
    "Folk": "原声吉他与人声叙事，小而美的听众基本盘。",
    "Metal": "高能量与极端音色，亚文化圈层鲜明。",
    "NewAge": "氛围与冥想质感，播放场景偏功能与疗愈。",
    "EasyListening": "轻柔编曲与低刺激听感，适合背景播放。",
    "Reggae": "加勒比节奏与低音线条，全球传播的文化符号。",
    "Jazz": "即兴与复杂和声，经典曲目在榜单中历久弥新。",
    "Christian": "信仰主题与合唱编制，欧美市场稳定细分。",
    "Classical": "管弦与古典名曲，跨时代的高雅音乐资产。",
    "Blues": "十二小节与蓝调音阶，现代流行音乐的根源之一。",
}

PALETTE = {
    "Pop": "#499894",
    "Rock": "#ff9d9a",
    "HipHop": "#79706e",
    "Latin": "#8cd17d",
    "R&B": "#86bcb6",
    "TraditionalMusic": "#ffbe7d",
    "Electronic": "#a0cbe8",
    "Country": "#d7b5a6",
    "Folk": "#f28e2b",
    "Metal": "#b6992d",
    "NewAge": "#bab0ac",
    "EasyListening": "#f1ce63",
    "Reggae": "#e15759",
    "Jazz": "#59a14f",
    "Christian": "#d4a6c8",
    "Classical": "#9d7660",
    "Blues": "#b07aa1",
}

# 流派装饰：波形高度模式（0–1）
WAVE = {
    "Pop": [0.4, 0.7, 0.9, 0.6, 0.8, 0.5, 0.95, 0.55, 0.75, 0.45],
    "Rock": [0.9, 0.85, 0.95, 0.7, 0.88, 0.92, 0.6, 0.95, 0.8, 0.9],
    "HipHop": [0.95, 0.5, 0.85, 0.45, 0.9, 0.4, 0.88, 0.55, 0.92, 0.48],
    "Latin": [0.6, 0.85, 0.7, 0.95, 0.65, 0.9, 0.75, 0.88, 0.7, 0.92],
    "R&B": [0.5, 0.65, 0.55, 0.7, 0.48, 0.62, 0.58, 0.68, 0.52, 0.6],
    "TraditionalMusic": [0.35, 0.5, 0.4, 0.55, 0.38, 0.48, 0.42, 0.52, 0.36, 0.45],
    "Electronic": [0.7, 0.95, 0.65, 0.98, 0.72, 0.9, 0.68, 0.96, 0.74, 0.88],
    "Country": [0.45, 0.55, 0.5, 0.6, 0.48, 0.58, 0.52, 0.55, 0.47, 0.53],
    "Folk": [0.38, 0.42, 0.45, 0.4, 0.43, 0.39, 0.44, 0.41, 0.4, 0.42],
    "Metal": [0.98, 0.92, 0.96, 0.88, 0.95, 0.9, 0.97, 0.93, 0.96, 0.91],
    "NewAge": [0.25, 0.32, 0.28, 0.35, 0.26, 0.3, 0.27, 0.33, 0.25, 0.31],
    "EasyListening": [0.22, 0.28, 0.25, 0.3, 0.24, 0.27, 0.23, 0.29, 0.22, 0.26],
    "Reggae": [0.55, 0.72, 0.58, 0.75, 0.6, 0.7, 0.57, 0.73, 0.59, 0.71],
    "Jazz": [0.5, 0.78, 0.55, 0.82, 0.48, 0.75, 0.52, 0.8, 0.5, 0.76],
    "Christian": [0.42, 0.58, 0.45, 0.62, 0.4, 0.55, 0.44, 0.6, 0.43, 0.57],
    "Classical": [0.3, 0.55, 0.35, 0.62, 0.32, 0.58, 0.34, 0.6, 0.31, 0.56],
    "Blues": [0.48, 0.62, 0.52, 0.68, 0.5, 0.65, 0.49, 0.63, 0.51, 0.66],
}


def safe_name(genre: str) -> str:
    return genre.replace("&", "and").replace(" ", "_")


def load_genre_tracks() -> dict:
    if not FEATURED.exists():
        return {}
    data = json.loads(FEATURED.read_text(encoding="utf-8"))
    out = {}
    for genre, track in (data.get("by_genre") or {}).items():
        if genre != "Other":
            out[genre] = track
    for track in data.get("other_playlist") or []:
        out.setdefault(track["genre"], track)
    return out


def fetch_wiki_thumb(title: str) -> str | None:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SZU-DataViz/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return data.get("thumbnail", {}).get("source")
    except Exception:
        return None


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SZU-DataViz/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 800
    except Exception:
        return False


def esc(text: str) -> str:
    return xml.escape(str(text or ""))


def svg_poster(genre: str, color: str, track_meta: dict | None) -> str:
    label = re.sub(r"([a-z])([A-Z])", r"\1 \2", genre)
    track = track_meta.get("track", "") if track_meta else ""
    artist = (track_meta.get("artist", "") if track_meta else "").split("|")[0].strip()
    bars = WAVE.get(genre, WAVE["Pop"])
    bar_svg = ""
    for i, h in enumerate(bars):
        x = 48 + i * 68
        bh = int(120 * h)
        bar_svg += f'<rect x="{x}" y="{780 - bh}" width="36" height="{bh}" rx="4" fill="{color}" opacity=".55"/>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1000" width="800" height="1000">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0%" stop-color="#242424"/>
      <stop offset="100%" stop-color="#0e0e0e"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color}" stop-opacity=".92"/>
      <stop offset="100%" stop-color="{color}" stop-opacity=".35"/>
    </linearGradient>
    <radialGradient id="vinyl" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#111"/>
      <stop offset="55%" stop-color="#1a1a1a"/>
      <stop offset="56%" stop-color="#333"/>
      <stop offset="100%" stop-color="#0a0a0a"/>
    </radialGradient>
    <filter id="noise">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="table" tableValues="0 0.06"/></feComponentTransfer>
    </filter>
  </defs>
  <rect width="800" height="1000" fill="url(#bg)"/>
  <rect width="800" height="1000" filter="url(#noise)" opacity=".35"/>
  <rect x="0" y="0" width="800" height="8" fill="url(#accent)"/>
  <rect x="48" y="72" width="704" height="420" rx="12" fill="url(#accent)" opacity=".18"/>
  <rect x="48" y="72" width="704" height="420" rx="12" fill="none" stroke="{color}" stroke-opacity=".35" stroke-width="2"/>
  <circle cx="400" cy="282" r="148" fill="url(#vinyl)"/>
  <circle cx="400" cy="282" r="52" fill="{color}" opacity=".85"/>
  <circle cx="400" cy="282" r="14" fill="#0e0e0e"/>
  <text x="48" y="560" fill="#f1efea" font-family="Georgia,serif" font-size="24" letter-spacing="5" opacity=".45">GENRE</text>
  <text x="48" y="640" fill="#f1efea" font-family="Georgia,serif" font-size="68" font-weight="700">{esc(label)}</text>
  {f'<text x="48" y="710" fill="#f1efea" font-family="Georgia,serif" font-size="28" opacity=".72" font-style="italic">{esc(track)}</text>' if track else ''}
  {f'<text x="48" y="752" fill="#f1efea" font-family="monospace" font-size="22" opacity=".5">{esc(artist)}</text>' if artist else ''}
  {bar_svg}
  <text x="48" y="960" fill="#f1efea" font-family="monospace" font-size="20" opacity=".38">10,000 HEARTBEATS · SPOTIFY TOP</text>
</svg>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true", help="跳过 Wikipedia，仅生成本地 SVG")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    genre_tracks = load_genre_tracks()
    manifest = {}

    for genre, wiki_title in WIKI.items():
        color = PALETTE.get(genre, "#499894")
        safe = safe_name(genre)
        jpg_path = OUT_DIR / f"{safe}.jpg"
        svg_path = OUT_DIR / f"{safe}.svg"
        track_meta = genre_tracks.get(genre)
        src = "svg"
        image = f"images/genres/{safe}.svg"

        if jpg_path.exists() and jpg_path.stat().st_size > 800:
            src = "wikipedia"
            image = f"images/genres/{safe}.jpg"
        elif not args.local_only:
            thumb = fetch_wiki_thumb(wiki_title)
            if thumb and download(thumb, jpg_path):
                src = "wikipedia"
                image = f"images/genres/{safe}.jpg"
            else:
                svg_path.write_text(svg_poster(genre, color, track_meta), encoding="utf-8")
        else:
            svg_path.write_text(svg_poster(genre, color, track_meta), encoding="utf-8")

        entry = {
            "image": image,
            "source": src,
            "color": color,
            "blurb": BLURBS.get(genre, ""),
            "wiki": wiki_title,
        }
        if track_meta:
            entry["track_id"] = track_meta.get("track_id")
            entry["track"] = track_meta.get("track")
            entry["artist"] = track_meta.get("artist")
        manifest[genre] = entry
        print(f"{genre}: {src} -> {image}")

    DATA.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {DATA}")


if __name__ == "__main__":
    main()
