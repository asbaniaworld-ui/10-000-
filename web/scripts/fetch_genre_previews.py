"""为 by_genre 与 other_playlist 抓取 Deezer 30s 预览 URL。"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web" / "data" / "featured_tracks.json"


def fetch(track: str, artist: str) -> str | None:
    primary = artist.split("|")[0].strip()
    q = urllib.parse.quote(f"{track} {primary}")
    try:
        with urllib.request.urlopen(
            f"https://api.deezer.com/search?q={q}&limit=1", timeout=12
        ) as resp:
            payload = json.loads(resp.read().decode())
        return (payload.get("data") or [{}])[0].get("preview")
    except Exception:
        return None


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for genre, t in data.get("by_genre", {}).items():
        prev = fetch(t["track"], t["artist"])
        t["preview_url"] = prev
        print(f"{genre}: {'OK' if prev else 'no preview'}")
        time.sleep(0.15)
    for t in data.get("other_playlist", []):
        if t.get("preview_url"):
            continue
        prev = fetch(t["track"], t["artist"])
        t["preview_url"] = prev
        print(f"  [{t['genre']}] {'OK' if prev else 'no preview'}")
        time.sleep(0.15)
    if "Other" in data.get("by_genre", {}):
        del data["by_genre"]["Other"]
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
