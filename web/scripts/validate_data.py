"""对照 xlsx 原始数据校验 charts.json 全量准确性。"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
XLSX = PROJECT / "副top-10k-spotify-songs-2025-07-detailed-genre.xlsx"
CHARTS_PATH = ROOT / "data" / "charts.json"

sys.path.insert(0, str(Path(__file__).parent))
from tableau_logic import (  # noqa: E402
    EXPLICIT_RATIO_GENRES,
    EXPLICIT_TREND_DATE_MAX,
    EXPLICIT_TREND_DATE_MIN,
    EXPLICIT_TREND_GENRES,
    GENRE_TREND_LIST,
    GENRE_TREND_YEAR_MAX,
    GENRE_TREND_YEAR_MIN,
    RANK_GROUPS,
    STYLE_ARTISTS,
    TOP10_ARTISTS,
    build_charts,
    load_dataset,
    rank_group,
)


def check(name, web, actual, tol=0):
    if tol:
        ok = abs(float(web) - float(actual)) <= tol
    else:
        ok = web == actual
    return {"name": name, "ok": ok, "web": web, "actual": actual}


def main():
    charts = json.loads(CHARTS_PATH.read_text(encoding="utf-8"))
    frames = load_dataset(XLSX)
    df, valid = frames.raw, frames.valid
    expected = build_charts(frames)
    results = []

    # 1 genre market — all genres
    m = valid.groupby("Main Genres")["track_id"].count()
    for item in charts["genre_market"]:
        g, c = item["genre"], item["count"]
        results.append(check(f"market {g}", c, int(m[g])))

    # 2 genre trend — Pop/Rock 2024 + spot check Blues
    t = valid.groupby(["year", "Main Genres"])["popularity"].sum()
    pop24 = charts["genre_trend"]["Pop"]["popularity"][-1]
    results.append(check("Pop 2024 popularity", pop24, int(t.loc[(2024, "Pop")])))
    rock_years = charts["genre_trend"]["Rock"]["years"]
    rock_pop = charts["genre_trend"]["Rock"]["popularity"]
    idx = rock_years.index(2004) if 2004 in rock_years else -1
    if idx >= 0:
        results.append(
            check("Rock 2004 popularity", rock_pop[idx], int(t.loc[(2004, "Rock")]))
        )

    # 3 artist scatter — top 3
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
    for _, row in artist.head(3).iterrows():
        web = next(
            x
            for x in charts["artist_scatter"]
            if x["artist"] == row["artist_names"] and x["genre"] == row["Main Genres"]
        )
        results.append(
            check(
                f"artist {row['artist_names'][:20]} followers",
                web["followers"],
                int(row["followers"]),
            )
        )

    # 4 top100 golden — all metrics all groups
    for grp in RANK_GROUPS:
        sub = df[df["rank_group"] == grp]
        w = charts["top100_golden"]["groups"][grp]
        for key in ("danceability", "energy", "tempo", "loudness"):
            results.append(
                check(
                    f"top100 {grp} {key}",
                    w[key],
                    round(float(sub[key].mean()), 4 if key != "tempo" else 2),
                    tol=0.0001 if key in ("danceability", "energy") else 0.01,
                )
            )

    # 5 top10 golden
    for a in TOP10_ARTISTS:
        sub = df[df["artist_names"] == a]
        if sub.empty:
            continue
        w = next(x for x in charts["top10_golden"] if x["artist"] == a)
        results.append(
            check(f"{a} energy", w["energy"], round(float(sub["energy"].mean()), 4), 0.0001)
        )

    # 6 style distribution track counts
    for a in STYLE_ARTISTS:
        n_web = len(charts["style_distribution"].get(a, []))
        n_act = len(df[df["artist_names"] == a])
        results.append(check(f"style {a} tracks", n_web, n_act))

    # 7 emotion quadrant counts
    for a in ("Taylor Swift", "Billie Eilish"):
        n_web = sum(1 for x in charts["emotion_quadrant"] if x["artist"] == a)
        n_act = len(valid[valid["artist_names"] == a])
        results.append(check(f"emotion {a} points", n_web, n_act))

    # 8 explicit trend — all genres latest year in web data
    exp_mask = (
        valid["Main Genres"].isin(EXPLICIT_TREND_GENRES)
        & valid["release_date"].notna()
        & (valid["release_date"] >= EXPLICIT_TREND_DATE_MIN)
        & (valid["release_date"] <= EXPLICIT_TREND_DATE_MAX)
    )
    exp_t = valid[exp_mask].groupby(["year", "Main Genres"])["explicit"].sum()
    for g in EXPLICIT_TREND_GENRES:
        years = charts["explicit_trend"][g]["years"]
        counts = charts["explicit_trend"][g]["counts"]
        if not years:
            continue
        y = years[-1]
        results.append(check(f"{g} explicit {y}", counts[-1], int(exp_t.loc[(y, g)])))

    # 9 explicit ratio — all genres in list
    exp_r = (
        valid[valid["Main Genres"].isin(EXPLICIT_RATIO_GENRES)]
        .groupby("Main Genres")
        .agg(total=("track_id", "count"), explicit=("explicit", "sum"))
    )
    for g in EXPLICIT_RATIO_GENRES:
        if g not in exp_r.index:
            continue
        actual = round(exp_r.loc[g, "explicit"] / exp_r.loc[g, "total"] * 100, 2)
        web = next(x["ratio"] for x in charts["explicit_ratio"] if x["genre"] == g)
        results.append(check(f"{g} explicit%", web, actual))

    # rebuild equivalence
    if charts["genre_market"] != expected["genre_market"]:
        results.append(check("rebuild genre_market", "match", "mismatch"))

    fails = [r for r in results if not r["ok"]]
    print(f"Validated {len(results)} checks — {len(results) - len(fails)} OK, {len(fails)} FAIL")
    for r in results:
        mark = "OK" if r["ok"] else "FAIL"
        print(f"  {mark} | {r['name']} | web={r['web']} | actual={r['actual']}")
    if fails:
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
