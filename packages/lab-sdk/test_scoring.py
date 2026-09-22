import sys; sys.path.insert(0, "packages/lab-sdk")
from scoring import dynamic_points, score_solve
assert dynamic_points(500, 0) == 500
assert dynamic_points(500, 1) == 450
assert dynamic_points(500, 99) == 100  # floor
assert score_solve(400, 0, hint_cost=0, remediation_done=True) > 400
assert score_solve(400, 0, hint_cost=50) < 400
print("scoring OK")
