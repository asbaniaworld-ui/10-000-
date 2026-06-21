"""从 xlsx 生成 charts.json / featured_tracks.json（聚合逻辑见 tableau_logic.py）。"""
import argparse
import base64
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from tableau_logic import (
    STYLE_ARTISTS,
    TOP10_ARTISTS,
    build_charts,
    load_dataset,
)

base = Path(__file__).resolve().parents[1]
project = base.parent
assets = base / "assets" / "thumbnails"
data_dir = base / "data"
assets.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)

xlsx = project / "副top-10k-spotify-songs-2025-07-detailed-genre.xlsx"


def extract_thumbnails():
    twb_path = project / "20260603_期末故事线初版（1）.twb"
    if not twb_path.exists():
        return
    twb = twb_path.read_text(encoding="utf-8")
    for m in re.finditer(
        r"<thumbnail height='(\d+)' name='([^']+)' width='(\d+)'>\s*([\s\S]*?)\s*</thumbnail>",
        twb,
    ):
        name = m.group(2).replace("/", "-").replace(" ", "_").replace('"', "")
        b64 = re.sub(r"\s+", "", m.group(4))
        (assets / f"{name}.png").write_bytes(base64.b64decode(b64))


def fetch_deezer_preview(track_name: str, artist: str) -> str | None:
    q = urllib.parse.quote(f"{track_name} {artist}")
    url = f"https://api.deezer.com/search?q={q}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            payload = json.loads(resp.read().decode())
        items = payload.get("data") or []
        return items[0].get("preview") if items else None
    except Exception:
        return None


def fetch_itunes_preview(track_name: str, artist: str) -> str | None:
    q = urllib.parse.quote(f"{track_name} {artist}")
    url = f"https://itunes.apple.com/search?term={q}&entity=song&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            payload = json.loads(resp.read().decode())
        items = payload.get("results") or []
        return items[0].get("previewUrl") if items else None
    except Exception:
        return None


def fetch_preview(track_name: str, artist: str) -> str | None:
    return fetch_deezer_preview(track_name, artist) or fetch_itunes_preview(track_name, artist)


TOP5_GENRES = ["Pop", "Rock", "HipHop", "Latin", "R&B"]

NOISE_PATTERN = (
    r"(?i)(?:white noise|sleep|loopable|rain sounds|brown noise|ambient noise|"
    r"phase noise|babbling brook|calmness|dreams &|raining for hours)"
)

GENRE_REP_OVERRIDES = {
    "R&B": "2CGNAOSuO1MEFCbBRgUzjd",  # luther (with sza) — 有 Deezer 预览
    "Latin": "2lTm559tuIvatlT1u0JYG2",  # BAILE INoLVIDABLE — 有 Deezer 预览
}


def pick_representative(sub: pd.DataFrame) -> pd.Series:
    """跳过白噪音/环境音，取 popularity 最高的正常曲目。"""
    clean = sub[~sub["track_name"].str.contains(NOISE_PATTERN, na=False, regex=True)]
    if clean.empty:
        clean = sub
    return clean.sort_values("popularity", ascending=False).iloc[0]


def build_genre_rep_tracks(valid: pd.DataFrame, skip_previews: bool) -> dict:
    """各主流派代表曲：过滤噪音后 popularity 最高的一首。"""
    by_genre: dict = {}

    def row_to_track(row) -> dict:
        artist = str(row["artist_names"])
        track_name = str(row["track_name"])
        preview = None if skip_previews else fetch_deezer_preview(track_name, artist)
        if not skip_previews:
            time.sleep(0.12)
        return {
            "track": track_name[:80],
            "track_id": str(row["track_id"]),
            "artist": artist,
            "genre": str(row["Main Genres"]) if pd.notna(row["Main Genres"]) else "",
            "popularity": int(row["popularity"]),
            "preview_url": preview,
            "spotify_url": f"https://open.spotify.com/track/{row['track_id']}",
        }

    for genre in TOP5_GENRES:
        sub = valid[valid["Main Genres"] == genre]
        if sub.empty:
            continue
        if genre in GENRE_REP_OVERRIDES:
            hit = sub[sub["track_id"] == GENRE_REP_OVERRIDES[genre]]
            row = hit.iloc[0] if not hit.empty else pick_representative(sub)
        else:
            row = pick_representative(sub)
        by_genre[genre] = row_to_track(row)

    return by_genre


def build_other_playlist(valid: pd.DataFrame, skip_previews: bool) -> list:
    """长尾流派各一首代表曲，供 Other 扇区 playlist 使用。"""
    playlist = []
    rest = valid[~valid["Main Genres"].isin(TOP5_GENRES)]
    for genre, grp in rest.groupby("Main Genres", sort=False):
        row = pick_representative(grp)
        artist = str(row["artist_names"])
        track_name = str(row["track_name"])
        preview = None if skip_previews else fetch_deezer_preview(track_name, artist)
        if not skip_previews:
            time.sleep(0.12)
        playlist.append(
            {
                "track": track_name[:80],
                "track_id": str(row["track_id"]),
                "artist": artist,
                "genre": str(genre),
                "popularity": int(row["popularity"]),
                "preview_url": preview,
                "spotify_url": f"https://open.spotify.com/track/{row['track_id']}",
            }
        )
    playlist.sort(key=lambda x: x["popularity"], reverse=True)
    return playlist


def build_featured_tracks(df: pd.DataFrame, valid: pd.DataFrame, skip_previews: bool) -> dict:
    music_artists = list(
        dict.fromkeys(
            TOP10_ARTISTS
            + STYLE_ARTISTS
            + ["Taylor Swift", "Billie Eilish", "Bad Bunny", "Drake", "Playboi Carti"]
        )
    )
    featured_tracks = {}
    for artist in music_artists:
        sub = df[df["artist_names"] == artist].sort_values("popularity", ascending=False)
        if sub.empty:
            continue
        row = sub.iloc[0]
        track_name = str(row["track_name"])
        preview = None if skip_previews else fetch_deezer_preview(track_name, artist)
        featured_tracks[artist] = {
            "track": track_name[:80],
            "track_id": str(row["track_id"]),
            "artist": artist,
            "genre": str(row["Main Genres"]) if pd.notna(row["Main Genres"]) else "",
            "popularity": int(row["popularity"]),
            "preview_url": preview,
            "spotify_url": f"https://open.spotify.com/track/{row['track_id']}",
        }
        if not skip_previews:
            time.sleep(0.12)

    chapter_samples = {}
    for ch_id, artist_list in {
        1: ["Taylor Swift", "Bad Bunny"],
        3: ["Taylor Swift", "Bad Bunny", "Drake", "Playboi Carti"],
        5: ["Billie Eilish"],
        6: STYLE_ARTISTS,
        7: ["Taylor Swift", "Billie Eilish"],
    }.items():
        chapter_samples[str(ch_id)] = [
            featured_tracks[a] for a in artist_list if a in featured_tracks
        ]
    return {
        "by_artist": featured_tracks,
        "by_chapter": chapter_samples,
        "by_genre": build_genre_rep_tracks(valid, skip_previews),
        "other_playlist": build_other_playlist(valid, skip_previews),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-previews", action="store_true", help="跳过 Deezer 预览抓取")
    parser.add_argument("--skip-thumbnails", action="store_true")
    args = parser.parse_args()

    if not args.skip_thumbnails:
        extract_thumbnails()

    frames = load_dataset(xlsx)
    charts = build_charts(frames)

    if not args.skip_previews:
        def golden_preview_fetcher(track_name: str, artist: str) -> str | None:
            preview = fetch_preview(track_name, artist)
            time.sleep(0.12)
            return preview

        from tableau_logic import build_golden_samples

        charts["top100_golden"]["samples"] = build_golden_samples(
            frames.raw,
            charts["top100_golden"]["groups"],
            preview_fetcher=golden_preview_fetcher,
        )

    (data_dir / "charts.json").write_text(
        json.dumps(charts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    featured = build_featured_tracks(frames.raw, frames.valid, args.skip_previews)
    (data_dir / "featured_tracks.json").write_text(
        json.dumps(featured, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    subprocess.run(
        ["python", str(Path(__file__).parent / "extract_palette.py")], check=True
    )
    subprocess.run(
        ["python", str(Path(__file__).parent / "validate_data.py")], check=True
    )

    pop = next(x["count"] for x in charts["genre_market"] if x["genre"] == "Pop")
    rock = next(x["count"] for x in charts["genre_market"] if x["genre"] == "Rock")
    print(f"charts.json OK — Pop: {pop}, Rock: {rock}, rows: {charts['meta']['source_rows']}")


if __name__ == "__main__":
    main()
