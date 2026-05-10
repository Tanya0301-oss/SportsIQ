"""Tests for the lineup optimizer."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from optimizer.lineup import optimise_lineup


def _make_players():
    """Generate a pool of 30 realistic players."""
    players = []
    pid = 1

    def add(name, team, pos, salary, xpts):
        nonlocal pid
        players.append({
            "id": pid, "name": name, "team": team,
            "position": pos, "salary": salary, "expected_points": xpts,
            "recent_rating": 7.0, "goals_per_match": 0.1, "assists_per_match": 0.1,
        })
        pid += 1

    # GKs
    add("GK1", "Team A", "GK", 5.0, 5.5)
    add("GK2", "Team B", "GK", 4.5, 5.0)

    # DEFs (8)
    for i in range(8):
        add(f"DEF{i}", f"Team {chr(65 + i % 6)}", "DEF",
            round(5.0 + i * 0.3, 1), round(5.5 + i * 0.2, 1))

    # MIDs (10)
    for i in range(10):
        add(f"MID{i}", f"Team {chr(65 + i % 6)}", "MID",
            round(6.0 + i * 0.5, 1), round(6.0 + i * 0.4, 1))

    # FWDs (10)
    for i in range(10):
        add(f"FWD{i}", f"Team {chr(65 + i % 6)}", "FWD",
            round(7.0 + i * 0.6, 1), round(7.0 + i * 0.5, 1))

    return players


def test_optimal_squad_size():
    players = _make_players()
    result = optimise_lineup(players, budget=100.0, formation="flexible")
    assert result["status"] == "Optimal"
    assert len(result["selected_players"]) == 11


def test_exactly_one_goalkeeper():
    players = _make_players()
    result = optimise_lineup(players, budget=100.0, formation="flexible")
    gks = [p for p in result["selected_players"] if p["position"] == "GK"]
    assert len(gks) == 1


def test_budget_not_exceeded():
    players = _make_players()
    budget = 75.0
    result = optimise_lineup(players, budget=budget, formation="flexible")
    if result["status"] == "Optimal":
        assert result["total_salary"] <= budget


def test_max_3_per_club():
    players = _make_players()
    result = optimise_lineup(players, budget=100.0, formation="flexible")
    if result["status"] == "Optimal":
        from collections import Counter
        club_counts = Counter(p["team"] for p in result["selected_players"])
        for team, count in club_counts.items():
            assert count <= 3, f"Club {team} has {count} players (max 3)"


def test_infeasible_tiny_budget():
    players = _make_players()
    result = optimise_lineup(players, budget=1.0, formation="4-3-3")
    assert result["status"] != "Optimal"


def test_formation_433():
    players = _make_players()
    result = optimise_lineup(players, budget=100.0, formation="4-3-3")
    if result["status"] == "Optimal":
        selected = result["selected_players"]
        defs = sum(1 for p in selected if p["position"] == "DEF")
        mids = sum(1 for p in selected if p["position"] == "MID")
        fwds = sum(1 for p in selected if p["position"] == "FWD")
        assert defs == 4
        assert mids == 3
        assert fwds == 3
