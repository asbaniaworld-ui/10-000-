import html
import json
import re
from pathlib import Path

twb = (Path(__file__).resolve().parents[2] / "20260603_期末故事线初版（1）.twb").read_text(
    encoding="utf-8"
)

CANONICAL_GENRES = [
    "Blues",
    "Christian",
    "Classical",
    "Country",
    "EasyListening",
    "Electronic",
    "Folk",
    "HipHop",
    "Jazz",
    "Latin",
    "Metal",
    "NewAge",
    "Pop",
    "R&B",
    "Reggae",
    "Rock",
    "TraditionalMusic",
]

palette = {
    "main_genres": {},
    "artists": {},
    "rank_groups": {
        "Top 100": "#e15759",
        "Middle(101-9000)": "#59a14f",
        "Edge (9000-10000)": "#4e79a7",
    },
    "measures": {
        "danceability": {"palette": "orange", "mark": "#e15759"},
        "energy": {"palette": "green", "mark": "#59a14f"},
        "loudness": {"palette": "blue", "mark": "#4e79a7"},
        "tempo": {"palette": "purple", "mark": "#76b7b2"},
    },
    "top100_mark": "#75a1c7",
    "explicit_trend_genres": ["HipHop", "Latin", "Pop", "R&B", "Rock"],
}


def parse_bucket(map_block: str) -> str | None:
    b = re.search(r"<bucket>(.*?)</bucket>", map_block)
    if not b:
        return None
    text = html.unescape(b.group(1).strip())
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith(" "):
        return None
    return text.strip()


block_match = re.search(
    r"<encoding attr='color' field='\[none:Main Genres:nk\]' type='palette'>([\s\S]*?)</encoding>",
    twb,
)
if block_match:
    for m in re.finditer(r"<map to='(#[0-9a-fA-F]+)'>[\s\S]*?</map>", block_match.group(1)):
        name = parse_bucket(m.group(0))
        if not name or name == "%null%":
            continue
        palette["main_genres"][name] = m.group(1).lower()

for g in CANONICAL_GENRES:
    palette["main_genres"].setdefault(g, "#bab0ac")

artist_match = re.search(
    r"<encoding attr='color' field='\[none:artist_names:nk\]' type='palette'>([\s\S]*?)</encoding>",
    twb,
)
if artist_match:
    for m in re.finditer(r"<map to='(#[0-9a-fA-F]+)'>[\s\S]*?</map>", artist_match.group(1)):
        name = parse_bucket(m.group(0))
        if name:
            palette["artists"][name] = m.group(1).lower()

out = Path(__file__).resolve().parents[1] / "data" / "palette.json"
out.write_text(json.dumps(palette, ensure_ascii=False, indent=2), encoding="utf-8")
print("R&B", palette["main_genres"].get("R&B"), "Rock", palette["main_genres"].get("Rock"))
