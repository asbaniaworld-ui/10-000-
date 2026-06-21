"""仅更新 charts.json 中 top100_golden.samples 的曲目与预览 URL。"""
import json
import sys
import time
from pathlib import Path

base = Path(__file__).resolve().parents[1]
project = base.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_data import fetch_preview
from tableau_logic import build_charts, build_golden_samples, load_dataset

xlsx = project / "副top-10k-spotify-songs-2025-07-detailed-genre.xlsx"
charts_path = base / "data" / "charts.json"


def main():
    frames = load_dataset(xlsx)
    charts = build_charts(frames)

    def golden_preview_fetcher(track_name: str, artist: str) -> str | None:
        preview = fetch_preview(track_name, artist)
        time.sleep(0.12)
        return preview

    charts["top100_golden"]["samples"] = build_golden_samples(
        frames.raw,
        charts["top100_golden"]["groups"],
        preview_fetcher=golden_preview_fetcher,
    )

    charts_path.write_text(
        json.dumps(charts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for s in charts["top100_golden"]["samples"]:
        mark = "OK" if s.get("preview_url") else "NO"
        print(f"{mark} {s['label']}: {s['track']} - {s['artist'][:40]}")


if __name__ == "__main__":
    main()
