"""批量拉取展演用本地配图：流派专辑封面 + 艺人头像 → deck/images/**/*.jpg"""
from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENRE_DIR = ROOT / "deck" / "images" / "genres"
ARTIST_DIR = ROOT / "deck" / "images" / "artists"
GENRE_JSON = ROOT / "web" / "data" / "genre_images.json"
ARTIST_JSON = ROOT / "web" / "data" / "artist_images.json"
FEATURED = ROOT / "web" / "data" / "featured_tracks.json"

UA = {"User-Agent": "SZU-DataViz/1.0 (local-image-fetch)"}

WIKI_ARTIST = {
    "Taylor Swift": "Taylor_Swift",
    "Bad Bunny": "Bad_Bunny",
    "Drake": "Drake_(musician)",
    "Playboi Carti": "Playboi_Carti",
}


def ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi  # noqa: F401

        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


CTX = ssl_ctx()


def get_json(url: str, timeout: float = 18) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def download_bytes(url: str, timeout: float = 25) -> bytes | None:
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            data = resp.read()
        return data if len(data) > 800 else None
    except Exception:
        return None


def save_jpg(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path.stat().st_size > 800


def upscale_itunes(url: str) -> str:
    if not url:
        return url
    return (
        url.replace("100x100bb", "600x600bb")
        .replace("100x100", "600x600")
        .replace("200x200", "600x600")
    )


def fetch_spotify_cover(track_id: str) -> str | None:
    oembed = (
        "https://open.spotify.com/oembed?url="
        + urllib.parse.quote(f"https://open.spotify.com/track/{track_id}")
    )
    data = get_json(oembed)
    if isinstance(data, dict):
        return data.get("thumbnail_url")
    return None


def fetch_deezer_cover(track: str, artist: str) -> str | None:
    primary = (artist or "").split("|")[0].strip()
    q = urllib.parse.quote(f"{track} {primary}")
    data = get_json(f"https://api.deezer.com/search?q={q}&limit=1")
    if not isinstance(data, dict):
        return None
    items = data.get("data") or []
    if not items:
        return None
    album = items[0].get("album") or {}
    return album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium")


def fetch_itunes_cover(track: str, artist: str) -> str | None:
    primary = (artist or "").split("|")[0].strip()
    q = urllib.parse.quote(f"{track} {primary}")
    data = get_json(f"https://itunes.apple.com/search?term={q}&entity=song&limit=1")
    if not isinstance(data, dict):
        return None
    items = data.get("results") or []
    if not items:
        return None
    return upscale_itunes(items[0].get("artworkUrl100") or items[0].get("artworkUrl60"))


def fetch_wiki_thumb(title: str) -> str | None:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    data = get_json(url)
    if isinstance(data, dict):
        return (data.get("thumbnail") or {}).get("source")
    return None


def fetch_itunes_artist(artist: str) -> str | None:
    primary = (artist or "").split("|")[0].strip()
    q = urllib.parse.quote(primary)
    data = get_json(f"https://itunes.apple.com/search?term={q}&entity=musicArtist&limit=1")
    if not isinstance(data, dict):
        return None
    items = data.get("results") or []
    if not items:
        return None
    return upscale_itunes(items[0].get("artworkUrl100"))


def resolve_cover(track_id: str | None, track: str, artist: str) -> tuple[str | None, str]:
    if track_id:
        url = fetch_spotify_cover(track_id)
        if url:
            return url, "spotify"
    url = fetch_deezer_cover(track, artist)
    if url:
        return url, "deezer"
    url = fetch_itunes_cover(track, artist)
    if url:
        return url, "itunes"
    return None, "failed"


def safe_genre_file(genre: str) -> str:
    return genre.replace("&", "and").replace(" ", "_")


def safe_artist_file(name: str) -> str:
    return name.replace(" ", "_")


def fetch_genres() -> dict:
    catalog = json.loads(GENRE_JSON.read_text(encoding="utf-8"))
    report = {}
    for genre, meta in catalog.items():
        safe = safe_genre_file(genre)
        dest = GENRE_DIR / f"{safe}.jpg"
        if dest.exists() and dest.stat().st_size > 800:
            meta["image"] = f"images/genres/{safe}.jpg"
            meta["source"] = meta.get("source", "local")
            report[genre] = "cached"
            continue

        track_id = meta.get("track_id")
        track = meta.get("track") or ""
        artist = meta.get("artist") or ""
        url, src = resolve_cover(track_id, track, artist)
        ok = False
        if url:
            data = download_bytes(url)
            if data and save_jpg(dest, data):
                meta["image"] = f"images/genres/{safe}.jpg"
                meta["source"] = src
                ok = True
        report[genre] = src if ok else "failed"
        print(f"  genre {genre}: {report[genre]} -> {meta['image']}")
        time.sleep(0.15)

    GENRE_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def fetch_artists() -> dict:
    catalog = json.loads(ARTIST_JSON.read_text(encoding="utf-8"))
    report = {}
    for name, meta in catalog.items():
        safe = safe_artist_file(name)
        dest = ARTIST_DIR / f"{safe}.jpg"
        if dest.exists() and dest.stat().st_size > 800:
            meta["image"] = f"images/artists/{safe}.jpg"
            report[name] = "cached"
            continue

        wiki = WIKI_ARTIST.get(name, name.replace(" ", "_"))
        url = fetch_wiki_thumb(wiki)
        src = "wikipedia"
        if not url:
            url = fetch_itunes_artist(name)
            src = "itunes"
        ok = False
        if url:
            data = download_bytes(url)
            if data and save_jpg(dest, data):
                meta["image"] = f"images/artists/{safe}.jpg"
                meta["source"] = src
                ok = True
        report[name] = src if ok else "failed"
        print(f"  artist {name}: {report[name]} -> {meta['image']}")
        time.sleep(0.15)

    ARTIST_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    print("Fetching genre covers…")
    genre_report = fetch_genres()
    print("Fetching artist portraits…")
    artist_report = fetch_artists()
    ok_g = sum(1 for v in genre_report.values() if v != "failed")
    ok_a = sum(1 for v in artist_report.values() if v != "failed")
    print(f"Done: genres {ok_g}/{len(genre_report)}, artists {ok_a}/{len(artist_report)}")
    print(f"Output: {GENRE_DIR} , {ARTIST_DIR}")


if __name__ == "__main__":
    main()
