"""
Seed historical match data from football-data.co.uk CSV files into the database.

Usage:
  python -m scripts.seed_data --csv path/to/E0.csv [--csv path/to/E1.csv ...]

Downloads:
  Visit https://www.football-data.co.uk/englandm.php
  Download E0.csv (Premier League), E1.csv (Championship), etc.

Alternatively run without --csv to generate 500 synthetic historical matches
for immediate testing without any data download.
"""
import argparse
import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app import models
from app.database import AsyncSessionLocal, init_db

TEAMS = [
    "Manchester City", "Arsenal", "Liverpool", "Chelsea",
    "Manchester United", "Tottenham", "Newcastle", "Brighton",
    "Aston Villa", "West Ham", "Wolves", "Crystal Palace",
    "Everton", "Brentford", "Fulham", "Nottingham Forest",
]

RESULTS = ["H", "D", "A"]
RESULT_WEIGHTS = [0.46, 0.26, 0.28]   # Realistic distribution


def _synthetic_matches(n: int = 1000) -> list[dict]:
    """Generate synthetic but statistically realistic historical matches."""
    matches = []
    base_date = datetime(2021, 8, 1)

    for i in range(n):
        home, away = random.sample(TEAMS, 2)
        result = random.choices(RESULTS, weights=RESULT_WEIGHTS)[0]

        if result == "H":
            hg = random.randint(1, 4)
            ag = random.randint(0, hg - 1)
        elif result == "A":
            ag = random.randint(1, 4)
            hg = random.randint(0, ag - 1)
        else:
            g = random.randint(0, 3)
            hg = ag = g

        match_date = base_date + timedelta(days=i // 5)
        season = "2021/22" if match_date.year <= 2022 else (
            "2022/23" if match_date.year <= 2023 else "2023/24"
        )

        matches.append({
            "season": season,
            "home_team": home,
            "away_team": away,
            "home_goals": hg,
            "away_goals": ag,
            "result": result,
            "home_shots": random.randint(3, 18),
            "away_shots": random.randint(2, 15),
            "home_shots_on_target": random.randint(1, 8),
            "away_shots_on_target": random.randint(0, 7),
            "match_date": match_date.strftime("%Y-%m-%d"),
            "league": "E0",
        })

    return matches


async def seed_historical(csv_paths: list[str], n_synthetic: int = 0):
    await init_db()

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(func.count()).select_from(models.HistoricalMatch)
        )
        count = existing.scalar()

    if count > 0:
        print(f"Historical data already seeded ({count} rows). Use --force to re-seed.")
        return

    records = []

    if csv_paths:
        import pandas as pd
        for path in csv_paths:
            print(f"Loading {path}...")
            df = pd.read_csv(path)
            df.columns = [c.strip() for c in df.columns]

            rename = {
                "HomeTeam": "home_team", "AwayTeam": "away_team",
                "FTHG": "home_goals", "FTAG": "away_goals", "FTR": "result",
                "HST": "home_shots_on_target", "AST": "away_shots_on_target",
                "HS": "home_shots", "AS": "away_shots",
                "Date": "match_date", "Div": "league",
            }
            df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
            df = df.dropna(subset=["home_team", "away_team", "result"])
            df["result"] = df["result"].str.strip().str.upper()
            df = df[df["result"].isin(["H", "D", "A"])]

            for _, row in df.iterrows():
                records.append({
                    "season": str(row.get("season", "2023/24")),
                    "home_team": str(row["home_team"]),
                    "away_team": str(row["away_team"]),
                    "home_goals": int(row.get("home_goals", 0)),
                    "away_goals": int(row.get("away_goals", 0)),
                    "result": str(row["result"]),
                    "home_shots": int(row.get("home_shots", 0)),
                    "away_shots": int(row.get("away_shots", 0)),
                    "home_shots_on_target": int(row.get("home_shots_on_target", 0)),
                    "away_shots_on_target": int(row.get("away_shots_on_target", 0)),
                    "match_date": str(row.get("match_date", "2023-01-01")),
                    "league": str(row.get("league", "E0")),
                })
            print(f"  → {len(df)} rows loaded")
    else:
        print(f"No CSV provided — generating {n_synthetic} synthetic historical matches...")
        records = _synthetic_matches(n_synthetic)

    # Bulk insert
    async with AsyncSessionLocal() as db:
        for r in records:
            db.add(models.HistoricalMatch(**r))
        await db.commit()

    print(f"✓ Seeded {len(records)} historical matches")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="append", default=[], help="Path to CSV file(s)")
    parser.add_argument("--synthetic", type=int, default=1000,
                        help="Number of synthetic matches to generate if no CSV provided")
    args = parser.parse_args()
    asyncio.run(seed_historical(args.csv, args.synthetic))
