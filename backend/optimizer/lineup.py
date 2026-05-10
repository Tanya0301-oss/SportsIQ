"""
Fantasy lineup optimizer using integer linear programming (PuLP + CBC solver).

Objective: maximise total expected_points
Constraints:
  - Exactly 11 players selected
  - Total salary ≤ budget
  - Exactly 1 GK
  - 3-5 DEF
  - 3-5 MID
  - 1-3 FWD
  - Max 3 players from same club
"""
from loguru import logger
from pulp import PULP_CBC_CMD, LpBinary, LpMaximize, LpProblem, LpStatus, LpVariable, lpSum, value


def optimise_lineup(players: list[dict], budget: float = 100.0, formation: str = "4-3-3") -> dict:
    """
    Solve the lineup optimisation problem.

    Args:
        players: list of player dicts with keys:
                 id, name, team, position (GK/DEF/MID/FWD),
                 salary, expected_points
        budget: total salary cap
        formation: "4-4-2" | "4-3-3" | "3-5-2"

    Returns:
        dict with selected_players, total_salary, total_expected_points, status
    """
    # Formation → position counts
    formation_map = {
        "4-4-2": {"DEF": (4, 4), "MID": (4, 4), "FWD": (2, 2)},
        "4-3-3": {"DEF": (4, 4), "MID": (3, 3), "FWD": (3, 3)},
        "3-5-2": {"DEF": (3, 3), "MID": (5, 5), "FWD": (2, 2)},
        "flexible": {"DEF": (3, 5), "MID": (3, 5), "FWD": (1, 3)},
    }
    pos_limits = formation_map.get(formation, formation_map["flexible"])

    n = len(players)
    if n < 11:
        return {"status": "Infeasible", "reason": "Not enough players in pool"}

    prob = LpProblem("LineupOptimiser", LpMaximize)
    x = [LpVariable(f"x_{i}", cat=LpBinary) for i in range(n)]

    # Objective
    prob += lpSum(players[i]["expected_points"] * x[i] for i in range(n))

    # Total squad size
    prob += lpSum(x) == 11

    # Budget constraint
    prob += lpSum(players[i]["salary"] * x[i] for i in range(n)) <= budget

    # Exactly 1 GK
    gk_indices = [i for i, p in enumerate(players) if p["position"].upper() == "GK"]
    prob += lpSum(x[i] for i in gk_indices) == 1

    # Position constraints
    for pos, (lo, hi) in pos_limits.items():
        indices = [i for i, p in enumerate(players) if p["position"].upper() == pos]
        prob += lpSum(x[i] for i in indices) >= lo
        prob += lpSum(x[i] for i in indices) <= hi

    # Max 3 players per club
    teams = {p["team"] for p in players}
    for team in teams:
        indices = [i for i, p in enumerate(players) if p["team"] == team]
        prob += lpSum(x[i] for i in indices) <= 3

    # Solve (suppress CBC output)
    solver = PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    status = LpStatus[prob.status]
    if status != "Optimal":
        logger.warning(f"Lineup optimisation status: {status}")
        return {"status": status, "selected_players": [], "total_salary": 0, "total_expected_points": 0}

    selected = [players[i] for i in range(n) if value(x[i]) == 1]
    total_salary = sum(p["salary"] for p in selected)
    total_pts = sum(p["expected_points"] for p in selected)

    logger.info(f"Optimal lineup: {len(selected)} players, £{total_salary:.1f}m, {total_pts:.1f} pts")

    return {
        "status": "Optimal",
        "selected_players": selected,
        "total_salary": round(total_salary, 2),
        "total_expected_points": round(total_pts, 2),
        "formation": formation,
    }
