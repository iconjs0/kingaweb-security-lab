"""CTF dynamic scoring — pure, testable. No DB/docker."""
from __future__ import annotations
import math

def dynamic_points(base: int, solves_before: int, floor: int = 100, decay: float = 0.9) -> int:
    pts = base * (decay ** max(0, solves_before))
    return max(floor, int(math.floor(pts)))

def score_solve(base: int, solves_before: int, hint_cost: int = 0,
                attempts: int = 1, is_first_blood: bool = False,
                remediation_done: bool = False, floor: int = 100) -> int:
    pts = dynamic_points(base, solves_before, floor)
    if is_first_blood:
        pts = int(pts * 1.1)
    pts -= max(0, hint_cost)
    pts -= max(0, (attempts - 1)) * 2  # spam penalty, capped below
    if remediation_done:
        pts += 25
    return max(floor // 2, pts)
