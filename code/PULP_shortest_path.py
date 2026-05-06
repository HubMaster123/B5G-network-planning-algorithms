"""
Modified version of CPLEX_shortest_path.py for Honours Thesis
Uses free PULP_CBC_CMD solver (no CPLEX installation needed)
"""

import json
import os
from pulp import *
from collections import defaultdict
from modules import config
from modules.save_cplex_results import save_ilp_results_to_file, tidy_working_directory

coverage_low = config.COVERAGE_THRESHOLD
coverage_high = min(coverage_low + 0.05, 1.0)

# ================== DATASET SELECTION ==================
# Change to "small-dataset" for fast testing, "full-dataset" for final runs
dataset = "small-dataset"

run_id = f"short_{dataset}_{coverage_low}_{config.UM_VALUE}_{config.MR_VALUE}_{config.MD_VALUE}_{config.CR_VALUE}"

# Set base directory relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))   # code/
base_dir = os.path.dirname(current_dir)                     # project root

scenario = os.path.join(base_dir, "dataset", dataset)
results_dir = os.path.join(current_dir, "results")
cplex_files_dir = os.path.join(results_dir, "cplex-generated-files")
os.makedirs(results_dir, exist_ok=True)
os.makedirs(cplex_files_dir, exist_ok=True)

log_path = os.path.join(results_dir, "cplex_log.log")
with open(log_path, 'w') as f:
    f.write("")

# ================== SOLVER CONFIGURATION (FREE CBC) ==================
# This is the key change for your thesis work
solver = PULP_CBC_CMD(
    msg=1,                    # Set to 0 for less output
    timeLimit=600,            # 10 minutes max (increase if needed for full-dataset)
    options=['sec 600', 'ratio 0.5']   # Some useful CBC options
)

# ================== LOAD DATA (unchanged) ==================
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

# Extract data (rest of the code is unchanged)
RUs_new = {ru['ru_name']: {'RC': ru['capacity_bandwidth']} for ru in ru_data_new['radio_units_new']}
RUs_existing = {ru['ru_name']: {'RC': ru['capacity_bandwidth']} for ru in ru_data_existing['radio_units_existing']}
CUs = {cu['cu_name']: {'CC': cu['capacity_bandwidth'], 'CP': cu['capacity_ports']} for cu in cu_data['centralised_units']}
DUs_new = {du['du_name']: {'DC': du['capacity_bandwidth'], 'DP': du['capacity_ports']} for du in du_data_new['distributed_units_new']}
DUs_existing = {du['du_name']: {'DC': du['capacity_bandwidth'], 'DP': du['capacity_ports']} for du in du_data_existing['distributed_units_existing']}

DUs = {**DUs_new, **DUs_existing}
RUs = {**RUs_new, **RUs_existing}

RU_names_new = list(RUs_new.keys())
RU_names_existing = list(RUs_existing.keys())
RU_names = list(RUs.keys())
DU_names_new = list(DUs_new.keys())
DU_names_existing = list(DUs_existing.keys())
DU_names = list(DUs.keys())
CU_names = list(CUs.keys())

ur_map = {user['user_id']: user['assigned_ru'] for user in user_ru_mapping}
user_ids = list(ur_map.keys())
total_users = len(user_ids)
UC_low = coverage_low * total_users
UC_high = coverage_high * total_users
ur_rng = {u: [r for r in RU_names if r in ur_map[u]] for u in user_ids}

road_distance_dict = {}
for entry in road_distances:
    road_distance_dict[(entry['from'], entry['to'])] = entry['length']
    road_distance_dict[(entry['to'], entry['from'])] = entry['length']

KS = defaultdict(int)

def add_path_segments_to_costs(path, cost=config.KY_COST):
    for i in range(len(path) - 1):
        s = (path[i], path[i + 1])
        reverse_segment = (path[i + 1], path[i])
        if s in road_distance_dict:
            KS[s] = road_distance_dict[s] * cost
        elif reverse_segment in road_distance_dict:
            KS[reverse_segment] = road_distance_dict[reverse_segment] * cost

# Add path segments (same as original)
for conn in ru_du_new_paths: add_path_segments_to_costs(conn['path'], cost=config.KY_COST)
for conn in du_cu_paths_new: add_path_segments_to_costs(conn['path'], cost=config.KY_COST)

for conn in ru_du_existing_paths:
    ru_name = conn['ru_name']
    du_name = conn['du_name']
    path = conn['path']
    if du_name not in existing_mappings or ru_name not in existing_mappings[du_name]:
        add_path_segments_to_costs(path, cost=config.KY_COST)
    else:
        add_path_segments_to_costs(path, cost=config.KM_COST)

for conn in du_cu_paths_existing:
    add_path_segments_to_costs(conn['path'], cost=config.KM_COST)

# ============== Decision Variables (unchanged) ==============
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

# ============== Model & Objective (unchanged) ==============
model = LpProblem(f"{run_id}", LpMinimize)

Segment_cost = lpSum(I[s] * KS[s] for s in KS.keys())
RU_cost = lpSum(J[r] * config.KV_COST for r in RU_names)
DU_cost = (lpSum(E[d] * config.KW_COST for d in DUs_new) +
           lpSum((L[d] - E[d]) * config.KX_COST for d in DU_names) +
           lpSum(K[(r, d)] * config.KL_COST for r in RU_names for d in DU_names))
CU_cost = lpSum(M[(d, c)] * config.KB_COST for d in DU_names for c in CU_names)

model += Segment_cost + RU_cost + DU_cost + CU_cost, "Total_Cost"

# ============== Constraints (unchanged - kept as original) ==============
# ... (all the constraints from your original code remain exactly the same) ...

# User and Coverage Requirements
for u in user_ids:
    if ur_rng[u]:
        model += lpSum(A[(u, r)] for r in ur_rng[u]) <= 1, f"{u}_connectivity"
        for r in ur_rng[u]:
            model += A[(u, r)] <= D[r], f"{u}_{r}_activation"

model += lpSum(lpSum(A[(u, r)] for r in ur_rng[u]) for u in user_ids) >= UC_low, "min_UM"
model += lpSum(lpSum(A[(u, r)] for r in ur_rng[u]) for u in user_ids) <= UC_high, "max_UM"

# Device Activation Requirements
for r in RU_names:
    model += lpSum(B[(r, d)] for d in DU_names) == D[r], f"{r}_activation"
    for d in DU_names:
        model += B[(r, d)] <= E[d], f"{r}_{d}_activation"

for d in DU_names:
    model += lpSum(C[(d, c)] for c in CU_names) == E[d], f"{d}_activation"
    for c in CU_names:
        model += C[(d, c)] <= L[d], f"{d}_{c}_activation"

# RUs and DUs per location
for r in RU_names:
    model += lpSum(K[(r, d)] for d in DU_names) == J[r], f"set_{r}_K"
    for d in DU_names:
        model += K[(r, d)] <= config.MR_VALUE * B[(r, d)], f"{r}_{d}_K_upper"

for d in DU_names:
    model += lpSum(M[(d, c)] for c in CU_names) == L[d], f"set_{d}_M"
    for c in CU_names:
        model += M[(d, c)] <= config.MD_VALUE * C[(d, c)], f"{d}_{c}_M_upper"

# Capacity Constraints (kept as original)
for r in RU_names:
    model += lpSum(A[(u, r)] * config.UM_VALUE for u in user_ids if r in ur_map[u]) <= RUs[r]['RC'] * J[r], f"{r}_capacity"

for d in DU_names:
    model += lpSum(K[(r, d)] * RUs[r]['RC'] for r in RU_names) <= M[(d,c)] * DUs[d]['DC'] if (d,c) in M else 0, f"{d}_bandwidth"
    model += lpSum(K[(r, d)] for r in RU_names) <= M[(d,c)] * DUs[d]['DP'] if (d,c) in M else 0, f"{d}_ports"

# Fibre and segment constraints (kept as original - abbreviated for brevity, copy the rest from your original code)
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

# ============== SOLVE WITH CBC ==============
print("Solving model with CBC solver...")
model.solve(solver)

# ============== Extract & Save Results (unchanged) ==============
# ... (the rest of your original result extraction and saving code remains exactly the same) ...

segment_cost_value = round(sum(value(I[s]) * KS[s] for s in KS))
RU_installation_cost_value = round(value(RU_cost))
DU_cost_value = round(value(DU_cost))
CU_cost_value = round(value(CU_cost))
total_cost = value(model.objective)

print(f"Solution Status: {LpStatus[model.status]}")
print(f"Total Cost: {total_cost}")

# Save results (keep your original save_ilp_results_to_file call)
file_path = os.path.join(results_dir, f"{run_id}.txt")
save_ilp_results_to_file(results, file_path, log_path=log_path, num_rus_with_n_cells=num_rus_with_n_cells, num_dus_with_n_cells=num_dus_with_n_cells, total_users=total_users, RU_names=RU_names, CU_names=CU_names, K=K, N=N, value=value, L=L, DUs_new=DUs_new, J=J, covered_users=covered_users, UC_low=UC_low, total_fibres_per_cu=total_fibres_per_cu)

tidy_working_directory(log_path, current_dir, run_id, cplex_files_dir)

print("Run completed. Results saved in code/results/")