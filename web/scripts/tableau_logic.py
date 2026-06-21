"""Tableau 工作簿与 xlsx 对齐的聚合逻辑（单一数据源）。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

GENRE_TREND_LIST = [
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

EXPLICIT_RATIO_GENRES = [
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

EXPLICIT_TREND_GENRES = ["HipHop", "Latin", "Pop", "R&B", "Rock"]

TOP10_ARTISTS = [
    "Bad Bunny",
    "Billie Eilish",
    "Coldplay",
    "Drake",
    "Imagine Dragons",
    "Taylor Swift",
    "The Weeknd",
]

STYLE_ARTISTS = [
    "Billie Eilish",
    "Linkin Park",
    "Mrs. GREEN APPLE",
    "Taylor Swift",
    "The Weeknd",
]

STYLE_LABELS = {
    "Billie Eilish": "暗黑电子流行",
    "Linkin Park": "新金属",
    "Mrs. GREEN APPLE": "日式流行摇滚",
    "Taylor Swift": "乡村流行",
    "The Weeknd": "复古 R&B",
}

TOP10_HEATMAP_ARTISTS = [
    "Bad Bunny",
    "Billie Eilish",
    "Drake",
    "Imagine Dragons",
    "Taylor Swift",
    "The Weeknd",
]

TOP10_HEATMAP_GENRE_ORDER = ["HipHop", "Latin", "Pop", "R&B", "Rock", "Electronic", "Country"]

TOP10_HEATMAP_YEAR_MIN = 2000
TOP10_HEATMAP_YEAR_MAX = 2024
TOP10_HEATMAP_DATE_MIN = pd.Timestamp("1999-12-18")
TOP10_HEATMAP_DATE_MAX = pd.Timestamp("2024-12-31")

RANK_GROUPS = ["Top 100", "Middle(101-9000)", "Edge (9000-10000)"]

RANK_GROUP_LABELS = {
    "Top 100": "Top 100",
    "Middle(101-9000)": "Middle",
    "Edge (9000-10000)": "Edge",
}

PARAMS = {
    "danceability": {"weak": 0.0, "light": 0.4, "strong": 0.7},
    "energy": {"low": 0.0, "mid": 0.33, "high": 0.66},
    "tempo": {"slow": 40.0, "mid": 90.0, "fast": 130.0},
    "loudness": {"soft": -20.0, "standard": -12.0, "loud": -6.0},
}

# twb: 各音乐流派的受欢迎程度变化趋势 — release_date 1905~2024
GENRE_TREND_YEAR_MIN = 1905
GENRE_TREND_YEAR_MAX = 2024

# twb: 文化叛逆变化趋势 — release_date 2000-11-01 ~ 2025-08-04
EXPLICIT_TREND_DATE_MIN = pd.Timestamp("2000-11-01")
EXPLICIT_TREND_DATE_MAX = pd.Timestamp("2025-08-04")


def rank_group(rank: int) -> str:
    if rank <= 100:
        return "Top 100"
    if rank >= 9000:
        return "Edge (9000-10000)"
    return "Middle(101-9000)"


def golden_metric_distance(row, target: dict) -> float:
    return (
        (float(row["danceability"]) - target["danceability"]) ** 2 * 1.2
        + (float(row["energy"]) - target["energy"]) ** 2 * 1.4
        + ((float(row["tempo"]) - target["tempo"]) / 100) ** 2 * 1.0
        + ((float(row["loudness"]) - target["loudness"]) / 10) ** 2 * 0.9
    )


def in_golden_band(row) -> bool:
    """流媒体黄金区间：中速 + 中高能量 + 标准响度。"""
    return (
        0.55 <= float(row["danceability"]) <= 0.72
        and 0.55 <= float(row["energy"]) <= 0.70
        and 108 <= float(row["tempo"]) <= 132
        and -10.5 <= float(row["loudness"]) <= -6.5
    )


def golden_sample_pool(df: pd.DataFrame, grp: str) -> pd.DataFrame:
    sub = df[df["rank_group"] == grp].copy()
    if sub.empty:
        return sub
    banded = sub[sub.apply(in_golden_band, axis=1)].drop_duplicates(subset=["track_id"])
    return banded if len(banded) > 0 else sub.drop_duplicates(subset=["track_id"])


def golden_sample_row_to_dict(row, grp: str, preview_url: str | None = None) -> dict:
    genre = row["Main Genres"]
    sample = {
        "group": grp,
        "label": RANK_GROUP_LABELS[grp],
        "track": str(row["track_name"])[:50],
        "artist": str(row["artist_names"]),
        "track_id": str(row["track_id"]),
        "genre": str(genre) if pd.notna(genre) else "",
        "rank": int(row["rank"]),
        "popularity": int(row["popularity"]),
        "danceability": round(float(row["danceability"]), 4),
        "energy": round(float(row["energy"]), 4),
        "tempo": round(float(row["tempo"]), 2),
        "loudness": round(float(row["loudness"]), 2),
        "spotify_url": f"https://open.spotify.com/track/{row['track_id']}",
    }
    if preview_url:
        sample["preview_url"] = preview_url
    return sample


def pick_golden_sample_row(pool: pd.DataFrame, target: dict, preview_fetcher=None):
    """优先选指标最接近均值的曲目；若有 preview_fetcher 则在候选中找可预览的一首。"""
    pool = pool.copy()
    pool["_dist"] = pool.apply(lambda r: golden_metric_distance(r, target), axis=1)
    pool["_single"] = ~pool["artist_names"].astype(str).str.contains("|", regex=False)
    pool = pool.sort_values(["_dist", "_single", "popularity"], ascending=[True, False, False])
    if preview_fetcher is None:
        return pool.iloc[0], None

    best = pool.iloc[0]
    for _, row in pool.head(15).iterrows():
        artist_full = str(row["artist_names"])
        artist = artist_full.split("|")[0].strip()
        track_name = str(row["track_name"])
        preview = preview_fetcher(track_name, artist)
        if not preview and "|" in artist_full:
            preview = preview_fetcher(track_name, artist_full.replace("|", " "))
        if preview:
            return row, preview
    return best, None


def build_golden_samples(
    df: pd.DataFrame, groups: dict, preview_fetcher=None
) -> list:
    """每层选一首四维指标最接近该层均值的曲目（供 deck 试听）。"""
    samples = []
    for grp in RANK_GROUPS:
        pool = golden_sample_pool(df, grp)
        target = groups.get(grp)
        if pool.empty or not target:
            continue
        best, preview_url = pick_golden_sample_row(pool, target, preview_fetcher)
        samples.append(golden_sample_row_to_dict(best, grp, preview_url))
    return samples


@dataclass
class SpotifyFrames:
    raw: pd.DataFrame
    valid: pd.DataFrame  # Main Genres 非空（与 twb 多数图表一致）


def load_dataset(xlsx: Path) -> SpotifyFrames:
    df = pd.read_excel(xlsx)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["year"] = df["release_date"].dt.year
    df["rank_group"] = df["rank"].apply(rank_group)
    valid = df[df["Main Genres"].notna()].copy()
    return SpotifyFrames(raw=df, valid=valid)


def build_charts(frames: SpotifyFrames) -> dict:
    df, valid = frames.raw, frames.valid
    charts: dict = {}

    market = (
        valid.groupby("Main Genres")["track_id"]
        .count()
        .sort_values(ascending=False)
        .reset_index()
    )
    charts["genre_market"] = [
        {"genre": row["Main Genres"], "count": int(row["track_id"])}
        for _, row in market.iterrows()
    ]

    trend = (
        valid.groupby(["year", "Main Genres"])["popularity"]
        .sum()
        .reset_index()
    )
    trend = trend[
        (trend["year"] >= GENRE_TREND_YEAR_MIN)
        & (trend["year"] <= GENRE_TREND_YEAR_MAX)
    ]
    charts["genre_trend"] = {}
    for g in GENRE_TREND_LIST:
        sub = trend[trend["Main Genres"] == g].sort_values("year")
        charts["genre_trend"][g] = {
            "years": sub["year"].astype(int).tolist(),
            "popularity": sub["popularity"].astype(int).tolist(),
        }

    artist = (
        valid.groupby(["artist_names", "Main Genres"])
        .agg(
            followers=("total_artist_followers", "sum"),
            popularity=("avg_artist_popularity", "sum"),
            tracks=("track_id", "count"),
        )
        .reset_index()
        .sort_values("followers", ascending=False)
    )
    charts["artist_scatter"] = [
        {
            "artist": row["artist_names"],
            "genre": row["Main Genres"],
            "followers": int(row["followers"]),
            "popularity": round(float(row["popularity"]), 2),
            "tracks": int(row["tracks"]),
        }
        for _, row in artist.iterrows()
    ]

    charts["top100_golden"] = {"groups": {}, "params": PARAMS}
    for g in RANK_GROUPS:
        sub = df[df["rank_group"] == g]
        charts["top100_golden"]["groups"][g] = {
            "danceability": round(float(sub["danceability"].mean()), 4),
            "energy": round(float(sub["energy"].mean()), 4),
            "tempo": round(float(sub["tempo"].mean()), 2),
            "loudness": round(float(sub["loudness"].mean()), 2),
        }
    charts["top100_golden"]["samples"] = build_golden_samples(
        df, charts["top100_golden"]["groups"]
    )

    top10_data = []
    for a in TOP10_ARTISTS:
        sub = df[df["artist_names"] == a]
        if sub.empty:
            continue
        top10_data.append(
            {
                "artist": a,
                "genre": sub["Main Genres"].mode().iloc[0],
                "followers": int(sub["total_artist_followers"].sum()),
                "danceability": round(float(sub["danceability"].mean()), 4),
                "energy": round(float(sub["energy"].mean()), 4),
                "tempo": round(float(sub["tempo"].mean()), 2),
                "loudness": round(float(sub["loudness"].mean()), 2),
                "tracks": int(len(sub)),
            }
        )
    charts["top10_golden"] = sorted(
        top10_data, key=lambda x: x["followers"], reverse=True
    )

    heat_sub = df[
        df["artist_names"].isin(TOP10_HEATMAP_ARTISTS)
        & df["release_date"].notna()
        & (df["release_date"] >= TOP10_HEATMAP_DATE_MIN)
        & (df["release_date"] <= TOP10_HEATMAP_DATE_MAX)
        & df["Main Genres"].notna()
    ]
    heat_sub = heat_sub.copy()
    heat_sub["year"] = heat_sub["release_date"].dt.year
    heat_sub = heat_sub[
        (heat_sub["year"] >= TOP10_HEATMAP_YEAR_MIN)
        & (heat_sub["year"] <= TOP10_HEATMAP_YEAR_MAX)
    ]
    # 格内数字：当年新发曲目数 + Popularity 均值（分，0–100，与色块一致）
    # 颜色：当年曲目 Popularity 均值（0–100）
    # 注：不可 SUM(total_artist_followers)，同一艺人每首歌会重复计入粉丝总量
    artist_year = (
        heat_sub.groupby(["artist_names", "year"])
        .agg(
            followers=("total_artist_followers", "max"),
            popularity=("popularity", "mean"),
            pop_sum=("popularity", "sum"),
            track_count=("track_id", "nunique"),
        )
        .reset_index()
    )
    genre_by_artist = (
        heat_sub.groupby(["artist_names", "Main Genres"])["track_id"]
        .count()
        .reset_index(name="n")
        .sort_values(["artist_names", "n"], ascending=[True, False])
        .drop_duplicates("artist_names")
        .set_index("artist_names")["Main Genres"]
        .to_dict()
    )
    artist_rank = (
        artist_year.groupby("artist_names")
        .agg(
            avg_pop=("popularity", "mean"),
            total_followers=("followers", "sum"),
        )
        .reset_index()
        .sort_values(["avg_pop", "total_followers"], ascending=[False, False])
    )
    heat_rows = [
        {
            "genre": genre_by_artist.get(a, ""),
            "artist": a,
        }
        for a in artist_rank["artist_names"]
    ]
    heat_years = sorted(artist_year["year"].astype(int).unique().tolist())
    heat_cells = [
        {
            "genre": genre_by_artist.get(r["artist_names"], ""),
            "artist": r["artist_names"],
            "year": int(r["year"]),
            "followers": int(r["followers"]),
            "popularity": round(float(r["popularity"]), 2),
            "pop_sum": int(round(float(r["pop_sum"]))),
            "track_count": int(r["track_count"]),
        }
        for _, r in artist_year.iterrows()
    ]
    charts["top10_heatmap"] = {
        "rows": heat_rows,
        "years": heat_years,
        "cells": heat_cells,
    }

    charts["style_distribution"] = {}
    for a in STYLE_ARTISTS:
        sub = df[df["artist_names"] == a]
        charts["style_distribution"][a] = [
            {
                "track": str(r["track_name"])[:50],
                "track_id": str(r["track_id"]),
                "artist": a,
                "popularity": int(r["popularity"]),
                "danceability": round(float(r["danceability"]), 4),
                "energy": round(float(r["energy"]), 4),
                "tempo": round(float(r["tempo"]), 2),
                "loudness": round(float(r["loudness"]), 2),
            }
            for _, r in sub.iterrows()
        ]

    emotion = []
    for a in ["Taylor Swift", "Billie Eilish"]:
        sub = valid[valid["artist_names"] == a]
        for _, r in sub.iterrows():
            emotion.append(
                {
                    "artist": a,
                    "energy": round(float(r["energy"]), 4),
                    "valence": round(float(r["valence"]), 4),
                    "track": str(r["track_name"])[:50],
                    "track_id": str(r["track_id"]),
                    "album": str(r["album_name"])[:40],
                }
            )
    charts["emotion_quadrant"] = emotion

    exp_mask = (
        valid["Main Genres"].isin(EXPLICIT_TREND_GENRES)
        & valid["release_date"].notna()
        & (valid["release_date"] >= EXPLICIT_TREND_DATE_MIN)
        & (valid["release_date"] <= EXPLICIT_TREND_DATE_MAX)
    )
    exp_trend = (
        valid[exp_mask]
        .groupby(["year", "Main Genres"])["explicit"]
        .sum()
        .reset_index()
    )
    charts["explicit_trend"] = {}
    for g in EXPLICIT_TREND_GENRES:
        sub = exp_trend[exp_trend["Main Genres"] == g].sort_values("year")
        charts["explicit_trend"][g] = {
            "years": sub["year"].astype(int).tolist(),
            "counts": sub["explicit"].astype(int).tolist(),
        }

    exp_ratio = (
        valid[valid["Main Genres"].isin(EXPLICIT_RATIO_GENRES)]
        .groupby("Main Genres")
        .agg(total=("track_id", "count"), explicit=("explicit", "sum"))
        .reset_index()
    )
    exp_ratio["ratio"] = (exp_ratio["explicit"] / exp_ratio["total"] * 100).round(2)
    exp_ratio = exp_ratio.sort_values("ratio", ascending=False)
    charts["explicit_ratio"] = [
        {
            "genre": row["Main Genres"],
            "ratio": float(row["ratio"]),
            "total": int(row["total"]),
            "explicit": int(row["explicit"]),
        }
        for _, row in exp_ratio.iterrows()
    ]

    charts["meta"] = {
        "source": "副top-10k-spotify-songs-2025-07-detailed-genre.xlsx",
        "source_rows": int(len(df)),
        "valid_rows": int(len(valid)),
        "unique_ranks": int(df["rank"].nunique()),
        "genre_trend_order": GENRE_TREND_LIST,
        "explicit_trend_genres": EXPLICIT_TREND_GENRES,
        "style_artists": STYLE_ARTISTS,
        "style_labels": STYLE_LABELS,
        "top10_artists": TOP10_ARTISTS,
        "top10_heatmap_artists": TOP10_HEATMAP_ARTISTS,
        "golden_groups": RANK_GROUPS,
        "golden_rows": [
            {"key": "danceability", "label": "Danceability", "min": 0, "max": 1},
            {"key": "energy", "label": "Energy", "min": 0, "max": 1},
            {"key": "loudness", "label": "Loudness", "min": -20, "max": 0},
            {"key": "tempo", "label": "Tempo", "min": 40, "max": 220},
        ],
        "top10_golden_rows": [
            {"key": "loudness", "label": "Loudness", "min": -20, "max": 0},
            {"key": "danceability", "label": "Danceability", "min": 0, "max": 1},
            {"key": "energy", "label": "Energy", "min": 0, "max": 1},
            {"key": "tempo", "label": "Tempo", "min": 40, "max": 220},
        ],
        "style_metrics": [
            {"key": "danceability", "label": "Danceability", "min": 0, "max": 1},
            {"key": "energy", "label": "Energy", "min": 0, "max": 1},
            {"key": "tempo", "label": "Tempo", "min": 40, "max": 220},
            {"key": "loudness", "label": "Loudness", "min": -20, "max": 0},
        ],
        "aggregations": {
            "genre_market": "COUNT(track_id) BY Main Genres, exclude null",
            "genre_trend": f"SUM(popularity) BY YEAR(release_date), Main Genres; years {GENRE_TREND_YEAR_MIN}-{GENRE_TREND_YEAR_MAX}",
            "artist_scatter": "SUM(total_artist_followers), SUM(avg_artist_popularity), COUNT(track_id) BY artist_names, Main Genres",
            "top100_golden": "AVG(audio metrics) BY rank_group",
            "top10_golden": "AVG(audio metrics) BY artist (filtered list)",
            "top10_heatmap": "AVG(popularity) color & score label; COUNT(track) label; sort by avg popularity BY artist, year",
            "explicit_trend": f"SUM(explicit) BY YEAR, genre; date {EXPLICIT_TREND_DATE_MIN.date()}–{EXPLICIT_TREND_DATE_MAX.date()}",
            "explicit_ratio": "SUM(explicit)/COUNT(track_id) BY Main Genres",
        },
    }
    return charts
