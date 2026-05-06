"""
B5G Network Planning Model using PuLP
Updated: Uses CPLEX_PY (Python API) with CBC fallback - works on Windows without cplex.exe
"""

import json
import os
from pulp import *
from collections import defaultdict

from modules import config
from modules.save_cplex_results import save_ilp_results_to_file, tidy_working_directory

# ========================== Parameters ==========================
coverage_low = config.COVERAGE_THRESHOLD
coverage_high = min(coverage_low + 0.05, 1.0)

dataset = "small-dataset"   # change to "full-dataset" when ready

run_id = f"short_{dataset}_{coverage_low}_{config.UM_VALUE}_{config.MR_VALUE}_{config.MD_VALUE}_{config.CR_VALUE}"

# ========================== Paths ==========================
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)

scenario = os.path.join(base_dir, "dataset", dataset)
results_dir = os.path.join(current_dir, "results")
cplex_files_dir = os.path.join(results_dir, "cplex-generated-files")

os.makedirs(results_dir, exist_ok=True)
os.makedirs(cplex_files_dir, exist_ok=True)

log_path = os.path.join(results_dir, "cplex_log.log")
with open(log_path, 'w') as f:
    f.write("")

# ========================== Solver (Fixed for Windows) ==========================
print("=== Setting up solver ===")
# Force CBC (open-source, unlimited size, reliable fallback)
cplex_solver = PULP_CBC_CMD(
    msg=True, 
    logPath=log_path,
    timeLimit=1800,      # 30 minutes max
    options=['sec 1800', 'ratio 0.05']  # allow 5% gap for faster solve
)
print("✅ Using CBC solver (unlimited size)")

# ========================== Load Data (unchanged) ==========================
with open(os.path.join(scenario, 'radio_units_new.json')) as f: ru_data_new = json.load(f)
with open(os.path.join(scenario, 'radio_units_exist.json')) as f: ru_data_existing = json.load(f)
with open(os.path.join(scenario, 'distributed_units_new.json')) as f: du_data_new = json.load(f)
with open(os.path.join(scenario, 'distributed_units_exist.json')) as f: du_data_existing = json.load(f)
with open(os.path.join(scenario, 'centralised_units.json')) as f: cu_data = json.load(f)
with open(os.path.join(scenario, 'ru_du_path_new.json')) as f: ru_du_new_paths = json.load(f)
with open(os.path.join(scenario, 'ru_du_path_exist.json')) as f: ru_du_existing_paths = json.load(f)
with open(os.path.join(scenario, 'ru_du_path_exist_graph.json')) as f: ru_du_existing_paths_graph = json.load(f)
with open(os.path.join(scenario, 'du_cu_path_new.json')) as f: du_cu_paths_new = json.load(f)
with open(os.path.join(scenario, 'du_cu_path_exist.json')) as f: du_cu_paths_existing = json.load(f)
with open(os.path.join(scenario, 'road_distances.json')) as f: road_distances = json.load(f)
with open(os.path.join(scenario, 'user_map.json')) as f: user_ru_mapping = json.load(f)
with open(os.path.join(scenario, 'ru_du_existing_mappings.json')) as f: existing_mappings = json.load(f)

# ... [All your data extraction code remains exactly the same] ...
RUs_new = {ru['ru_name']: {'RC': ru['capacity_bandwidth']} for ru in ru_data_new['radio_units_new']}
RUs_existing = {ru['ru_name']: {'RC': ru['capacity_bandwidth']} for ru in ru_data_existing['radio_units_existing']}
RUs = {**RUs_new, **RUs_existing}

CUs = {cu['cu_name']: {'CC': cu['capacity_bandwidth'], 'CP': cu['capacity_ports']} for cu in cu_data['centralised_units']}

DUs_new = {du['du_name']: {'DC': du['capacity_bandwidth'], 'DP': du['capacity_ports']} for du in du_data_new['distributed_units_new']}
DUs_existing = {du['du_name']: {'DC': du['capacity_bandwidth'], 'DP': du['capacity_ports']} for du in du_data_existing['distributed_units_existing']}
DUs = {**DUs_new, **DUs_existing}

RU_names = list(RUs.keys())
DU_names = list(DUs.keys())
CU_names = list(CUs.keys())

ur_map = {user['user_id']: user['assigned_ru'] for user in user_ru_mapping}
user_ids = list(ur_map.keys())
total_users = len(user_ids)
UC_low = coverage_low * total_users
UC_high = coverage_high * total_users
ur_rng = {u: [r for r in RU_names if r in ur_map.get(u, [])] for u in user_ids}

road_distance_dict = {}
for entry in road_distances:
    road_distance_dict[(entry['from'], entry['to'])] = entry['length']
    road_distance_dict[(entry['to'], entry['from'])] = entry['length']

KS = defaultdict(int)

def add_path_segments_to_costs(path, cost=config.KY_COST):
    for i in range(len(path) - 1):
        s = (path[i], path[i + 1])
        rev = (path[i + 1], path[i])
        if s in road_distance_dict:
            KS[s] = road_distance_dict[s] * cost
        elif rev in road_distance_dict:
            KS[rev] = road_distance_dict[rev] * cost

for conn in ru_du_new_paths: add_path_segments_to_costs(conn['path'], config.KY_COST)
for conn in du_cu_paths_new: add_path_segments_to_costs(conn['path'], config.KY_COST)

for conn in ru_du_existing_paths:
    ru_name = conn['ru_name']
    du_name = conn['du_name']
    path = conn['path']
    if du_name in existing_mappings and ru_name in existing_mappings[du_name]:
        add_path_segments_to_costs(path, config.KM_COST)
    else:
        add_path_segments_to_costs(path, config.KY_COST)

for conn in du_cu_paths_existing:
    add_path_segments_to_costs(conn['path'], config.KM_COST)

# ========================== Decision Variables (unchanged) ==========================
A = LpVariable.dicts("A", ((u, r) for u in user_ids for r in ur_map[u]), cat=LpBinary)
B = LpVariable.dicts("B", [(r, d) for r in RU_names for d in DU_names], cat=LpBinary)
C = LpVariable.dicts("C", [(d, c) for d in DU_names for c in CU_names], cat=LpBinary)
D = LpVariable.dicts("D", RU_names, cat=LpBinary)
E = LpVariable.dicts("E", DU_names, cat=LpBinary)
I = LpVariable.dicts("I", KS.keys(), cat=LpBinary)
J = LpVariable.dicts("J", RU_names, lowBound=0, upBound=config.MR_VALUE, cat='Integer')
K = LpVariable.dicts("K", [(r, d) for r in RU_names for d in DU_names], lowBound=0, upBound=config.MR_VALUE, cat="Integer")
L = LpVariable.dicts("L", DU_names, lowBound=0, upBound=config.MD_VALUE, cat="Integer")
M = LpVariable.dicts("M", [(d, c) for d in DU_names for c in CU_names], lowBound=0, upBound=config.MD_VALUE, cat="Integer")
N = LpVariable.dicts("N", [(d, c) for d in DU_names for c in CU_names], lowBound=0, cat='Integer')

# ========================== Model & Objective ==========================
model = LpProblem(f"{run_id}", LpMinimize)

Segment_cost = lpSum(I[s] * KS[s] for s in KS.keys())
RU_cost = lpSum(J[r] * config.KV_COST for r in RU_names)
DU_cost = (lpSum(E[d] * config.KW_COST for d in DUs_new) +
           lpSum((L[d] - E[d]) * config.KX_COST for d in DU_names) +
           lpSum(K[(r, d)] * config.KL_COST for r in RU_names for d in DU_names))
CU_cost = lpSum(M[(d, c)] * config.KB_COST for d in DU_names for c in CU_names)

model += Segment_cost + RU_cost + DU_cost + CU_cost, "Total_Cost"

# ========================== Constraints (your original) ==========================
for u in user_ids:
    if ur_rng[u]:
        model += lpSum(A[(u, r)] for r in ur_rng[u]) <= 1, f"{u}_connectivity"
        for r in ur_rng[u]:
            model += A[(u, r)] <= D[r], f"{u}_{r}_activation"

model += lpSum(lpSum(A[(u, r)] for r in ur_rng[u]) for u in user_ids) >= UC_low, "min_coverage"
model += lpSum(lpSum(A[(u, r)] for r in ur_rng[u]) for u in user_ids) <= UC_high, "max_coverage"

for r in RU_names:
    model += lpSum(B[(r, d)] for d in DU_names) == D[r], f"{r}_activation"
    for d in DU_names:
        model += B[(r, d)] <= E[d], f"{r}_{d}_activation"

for d in DU_names:
    model += lpSum(C[(d, c)] for c in CU_names) == E[d], f"{d}_activation"
    for c in CU_names:
        model += C[(d, c)] <= L[d], f"{d}_{c}_activation"

for r in RU_names:
    model += lpSum(K[(r, d)] for d in DU_names) == J[r], f"set_{r}_K"
    for d in DU_names:
        model += K[(r, d)] <= config.MR_VALUE * B[(r, d)], f"{r}_{d}_K_upper"

for d in DU_names:
    model += lpSum(M[(d, c)] for c in CU_names) == L[d], f"set_{d}_M"
    for c in CU_names:
        model += M[(d, c)] <= config.MD_VALUE * C[(d, c)], f"{d}_{c}_M_upper"

for r in RU_names:
    model += lpSum(A[(u, r)] * config.UM_VALUE for u in user_ids if r in ur_map[u]) <= RUs[r]['RC'] * J[r], f"{r}_capacity"

for d in DU_names:
    model += lpSum(K[(r, d)] * RUs[r]['RC'] for r in RU_names) <= M[(d,c)] * DUs[d]['DC'] if (d,c) in M else 0, f"{d}_bandwidth"
    model += lpSum(K[(r, d)] for r in RU_names) <= M[(d,c)] * DUs[d]['DP'] if (d,c) in M else 0, f"{d}_ports"

for r in RU_names:
    model += lpSum(K[(r, d)] * RUs[r]['RC'] for d in DU_names) <= config.FC_VALUE * J[r], f"fibre_{r}"

for d in DU_names:
    for c in CU_names:
        model += M[(d, c)] <= N[(d, c)] * config.CR_VALUE, f"{d}_{c}_M"
        model += lpSum(K[(r, d)] * RUs[r]['RC'] for r in RU_names) <= config.FC_VALUE * N[(d, c)], f"{d}_{c}_bandwidth_H"

for conn in ru_du_new_paths + ru_du_existing_paths:
    ru_name = conn['ru_name']
    du_name = conn['du_name']
    path = conn['path']
    for i in range(len(path) - 1):
        s = (path[i], path[i + 1])
        if s in KS:
            model += I[s] >= B[(ru_name, du_name)], f"seg_{s}_{ru_name}_{du_name}"

for conn in du_cu_paths_new + du_cu_paths_existing:
    du_name = conn['du_name']
    cu_name = conn['cu_name']
    path = conn['path']
    for i in range(len(path) - 1):
        s = (path[i], path[i + 1])
        if s in KS:
            model += I[s] >= C[(du_name, cu_name)], f"seg_{s}_{du_name}_{cu_name}"

# ========================== Solve ==========================
print("=== Solving the model ===")
model.solve(cplex_solver)

print(f"Status: {LpStatus[model.status]}")
print(f"Objective (Total Cost): {value(model.objective):,.2f}")

# ========================== Post-Solve Calculations ==========================
# These must be AFTER model.solve()

used_RU_capacity = {r: lpSum(A[(u, r)] * config.UM_VALUE for u in user_ids if r in ur_map[u]) for r in RU_names}
used_DU_capacity_bandwidth = {d: lpSum(K[(r, d)] * RUs[r]['RC'] for r in RU_names) for d in DU_names}
used_DU_capacity_ports = {d: lpSum(K[(r, d)] for r in RU_names) for d in DU_names}

# Summary statistics
num_rus_with_n_cells = {n: sum(1 for r in RU_names if round(value(J[r])) == n and value(D[r]) > 0)
                        for n in range(1, config.MR_VALUE + 1)}

num_dus_with_n_cells = {n: sum(1 for d in DU_names if round(value(L[d])) == n and value(E[d]) > 0)
                        for n in range(1, config.MD_VALUE + 1)}

segment_cost_value = round(sum(value(I[s]) * KS[s] for s in KS))
RU_installation_cost_value = round(value(RU_cost))
DU_cost_value = round(value(DU_cost))
CU_cost_value = round(value(CU_cost))
total_cost = value(model.objective)
num_selected_RUs = round(sum(value(D[r]) for r in RU_names))
num_selected_DUs = round(sum(value(E[d]) for d in DU_names))
total_segment_distance = round(sum(value(I[s]) * road_distance_dict.get(s, 0) for s in KS))

covered_users = sum(1 for u in user_ids if any(A[(u, r)].value() == 1 for r in ur_rng[u]))
user_coverage_percent = (covered_users / total_users) * 100

# Safe post-solve dictionaries
used_ru_capacity_dict = {r: round(value(used_RU_capacity[r])) 
                         for r in RU_names if value(D[r]) > 0}

used_du_capacity_dict = {d: {
    'bandwidth': round(value(used_DU_capacity_bandwidth[d])),
    'ports': round(value(used_DU_capacity_ports[d]))
} for d in DU_names if value(E[d]) > 0}

# Results dictionary
results = {
    "segment_cost_value": segment_cost_value,
    "RU_installation_cost_value": RU_installation_cost_value,
    "DU_cost_value": DU_cost_value,
    "CU_cost_value": CU_cost_value,
    "total_cost": total_cost,
    "num_selected_RUs": num_selected_RUs,
    "num_selected_DUs": num_selected_DUs,
    "total_segment_distance": total_segment_distance,
    "user_coverage_percent": user_coverage_percent,
    "total_users": total_users,
    "covered_users": covered_users,
}

# ========================== Save Results ==========================
file_path = os.path.join(results_dir, f"{run_id}.txt")

save_ilp_results_to_file(
    results, 
    file_path, 
    log_path=log_path,
    num_rus_with_n_cells=num_rus_with_n_cells,
    num_dus_with_n_cells=num_dus_with_n_cells,
    total_users=total_users,
    RU_names=RU_names,
    CU_names=CU_names,
    K=K,
    N=N,
    value=value,
    L=L,
    DUs_new=DUs_new,
    J=J,
    covered_users=covered_users,
    UC_low=UC_low,
    total_fibres_per_cu=total_fibres_per_cu if 'total_fibres_per_cu' in locals() else {}
)

tidy_working_directory(log_path, current_dir, run_id, cplex_files_dir)

print("\n✅ SUCCESS! Model solved and results saved.")
print(f"Results file : {file_path}")
print(f"Total Cost   : {total_cost:,.2f}")
print(f"Selected RUs : {num_selected_RUs}")
print(f"Selected DUs : {num_selected_DUs}")
print(f"Coverage     : {user_coverage_percent:.2f}%")