"""
Pure Genetic Algorithm for redundant pathways
Liam Suter - Honours Thesis

Selection : tournament; generational replacement
Crossover : two-point demand-group swap + mix r / (k-r) paths + repair
Mutation  : combined
            (A) cost-weighted L-shortest path replacement + repair
            (B) reset random demand(s) to exact k-shortest paths
Fitness   : unique-edge Total Cost + within-demand Overlap Penalty

Archive   : best unique-edge cost across seed, hall of fame, and final pop
"""

import sys
import os
import json
import random
import time
from itertools import islice

import pandas as pd
import networkx as nx
from deap import base, creator, tools, algorithms

from k_shortest_baseline import run_k_shortest_baseline
from new_generate_er_graph import generate_er_graph, save_er_graph

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# =============================================================================
# EXPERIMENTAL PARAMETERS
# =============================================================================
USE_ER = True
ER_N = 50
ER_P = 0.12
ER_SEED = 42

GRAPH_SIZE = "small"
NUM_DEMANDS = 20
K_PATHS = 3
POP_SIZE = 80
N_GENERATIONS = 120
CXPB = 0.75
MUTPB = 0.25
MUT_PATH_PB = 0.2
TOURNSIZE = 3
L_SHORTEST = 6
RANDOM_SEED = 42

YEN_MUT_PB = 0.3
PAIR_FRAC = 0.1


# =============================================================================
# 1. GRAPH AND DEMANDS
# =============================================================================
def load_graph(size="small"):
    if size == "1000":
        folder, graph_name = "1000_node_simplified_graph", "1000-Node Simplified Graph"
    elif size == "large":
        folder, graph_name = "large_simplified_graph", "Large (300) Simplified Graph"
    else:
        folder, graph_name = "simplified_graph", "Small Simplified Graph"

    possible_paths = [
        f"../dataset/{folder}/graph_edges.csv",
        f"dataset/{folder}/graph_edges.csv",
        os.path.join(os.path.dirname(__file__), "..", "dataset", folder, "graph_edges.csv"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            csv_path = p
            break
    else:
        raise FileNotFoundError(f"Could not find graph_edges.csv for size='{size}'")

    df = pd.read_csv(csv_path)
    graph = nx.Graph()
    for _, row in df.iterrows():
        graph.add_edge(
            str(row["source"]), str(row["target"]),
            weight=float(row["weight"]),
            cost=float(row["cost"]),
            length=float(row["length"]),
            failure_prob=float(row.get("failure_prob", 0.01)),
        )
    print(f"Loaded {graph_name}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    return graph


def create_demands(graph, num_demands=10, k=3, seed=42):
    nodes = list(graph.nodes())
    rng = random.Random(seed)
    demands_list = []
    for _ in range(num_demands):
        s = rng.choice(nodes)
        t = rng.choice(nodes)
        while t == s:
            t = rng.choice(nodes)
        demands_list.append((s, t, k))
    return demands_list


if USE_ER:
    G = generate_er_graph(n=ER_N, p=ER_P, seed=ER_SEED)
    save_er_graph(
        G,
        os.path.join("dataset", "er_graphs", f"er_n{ER_N}_p{ER_P}_seed{ER_SEED}.csv"),
    )
else:
    G = load_graph(size=GRAPH_SIZE)

demands = create_demands(G, num_demands=NUM_DEMANDS, k=K_PATHS, seed=RANDOM_SEED)
print(f"Generated {len(demands)} demands.")


# =============================================================================
# 2. PATH HELPERS
# =============================================================================
def is_valid_path(graph, path):
    if path is None or len(path) < 2:
        return False
    return all(graph.has_edge(path[i], path[i + 1]) for i in range(len(path) - 1))


def path_key(path):
    return tuple(path) if path is not None else None


def generate_random_path(graph, source, target, max_length=30):
    path = [source]
    current = source
    visited = {source}
    while current != target and len(path) < max_length:
        neighbors = [n for n in graph.neighbors(current) if n not in visited]
        if not neighbors:
            break
        current = random.choice(neighbors)
        path.append(current)
        visited.add(current)
    return path if current == target else None


def cost_weighted_path(graph, s, t, L=L_SHORTEST):
    try:
        paths = list(islice(nx.shortest_simple_paths(graph, s, t, weight="weight"), L))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]
    costs = [
        sum(graph[u][v].get("weight", graph[u][v].get("cost", 1.0))
            for u, v in zip(p[:-1], p[1:]))
        for p in paths
    ]
    weights = [1.0 / (c + 1e-9) for c in costs]
    total = sum(weights)
    return random.choices(paths, weights=[w / total for w in weights], k=1)[0]


def new_diverse_path(graph, s, t, forbidden, L=L_SHORTEST):
    try:
        pool = list(islice(nx.shortest_simple_paths(graph, s, t, weight="weight"), L + 4))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pool = []
    random.shuffle(pool)
    for p in pool:
        if is_valid_path(graph, p) and p[0] == s and p[-1] == t and path_key(p) not in forbidden:
            return p
    for _ in range(8):
        p = generate_random_path(graph, s, t)
        if p and is_valid_path(graph, p) and p[0] == s and p[-1] == t and path_key(p) not in forbidden:
            return p
    try:
        p = nx.shortest_path(graph, s, t, weight="weight")
        if is_valid_path(graph, p) and path_key(p) not in forbidden:
            return p
        if is_valid_path(graph, p):
            return p
    except nx.NetworkXNoPath:
        pass
    return None


def ensure_k_paths(group, graph, s, t, k):
    cleaned = []
    seen = set()
    for p in group or []:
        if (
            is_valid_path(graph, p)
            and p[0] == s
            and p[-1] == t
            and path_key(p) not in seen
        ):
            cleaned.append(list(p))
            seen.add(path_key(p))
    while len(cleaned) < k:
        p = new_diverse_path(graph, s, t, seen)
        if p is None:
            break
        cleaned.append(list(p))
        seen.add(path_key(p))
    while len(cleaned) < k:
        try:
            p = nx.shortest_path(graph, s, t, weight="weight")
            cleaned.append(list(p))
        except nx.NetworkXNoPath:
            break
    return cleaned[:k]


def unique_edge_cost(individual, graph):
    edges = set()
    for group in individual:
        for path in group:
            if not is_valid_path(graph, path):
                continue
            for u, v in zip(path, path[1:]):
                edges.add(tuple(sorted((u, v))))
    return sum(graph[u][v]["cost"] for u, v in edges)


def yen_paths_for_demand(graph, s, t, k):
    try:
        paths = list(islice(nx.shortest_simple_paths(graph, s, t, weight="cost"), k))
    except Exception:
        paths = []
    return ensure_k_paths(paths, graph, s, t, k)


def k_shortest_individual(graph, demand_list, k=3):
    groups = []
    for s, t, kk in demand_list:
        n_paths = kk if kk else k
        groups.append(yen_paths_for_demand(graph, s, t, n_paths))
    return creator.Individual(groups)


def best_unique_individual(candidates, graph):
    valid = [ind for ind in candidates if ind is not None]
    return min(valid, key=lambda ind: unique_edge_cost(ind, graph))


# =============================================================================
# 3. FITNESS
# =============================================================================
def evaluate(individual):
    total_cost = 0.0
    overlap_penalty = 0.0
    unique_edges = set()
    for i, group in enumerate(individual):
        _s, _t, k = demands[i]
        if len(group) != k:
            overlap_penalty += 50000 * abs(k - len(group))
        group_edges = set()
        for path in group:
            if not is_valid_path(G, path) or path[0] != _s or path[-1] != _t:
                overlap_penalty += 20000
                continue
            path_edges = {
                tuple(sorted((path[j], path[j + 1])))
                for j in range(len(path) - 1)
            }
            for e in path_edges:
                if e not in unique_edges:
                    total_cost += G[e[0]][e[1]]["cost"]
                    unique_edges.add(e)
            overlap_penalty += len(path_edges & group_edges) * 10000
            group_edges.update(path_edges)
    return (total_cost + overlap_penalty,)


# =============================================================================
# 4. OPERATORS
# =============================================================================
def regenerative_repair(individual, graph, demand_list, L=L_SHORTEST):
    for i, (source, target, k) in enumerate(demand_list):
        individual[i] = ensure_k_paths(individual[i], graph, source, target, k)
    return individual


def draw_r(k):
    """How many paths come from parent A. Peaked at k/2; never 0 or k."""
    if k <= 1:
        return 1
    r = int(round(random.gauss(k / 2.0, max(0.5, k / 4.0))))
    return max(1, min(k - 1, r))


def path_edges(path):
    return {tuple(sorted((path[j], path[j + 1]))) for j in range(len(path) - 1)}


def pick_least_overlap(pool, used, graph):
    best, best_score, best_idx = None, float("inf"), -1
    for idx, path in enumerate(pool):
        if not is_valid_path(graph, path):
            continue
        score = len(path_edges(path) & used) * 1000 + len(path)
        if score < best_score:
            best, best_score, best_idx = path, score, idx
    if best is None and pool:
        return pool[0], 0
    return best, best_idx


def mix_parent_paths(group_a, group_b, k, graph, s, t):
    """
    Take r paths from A and k-r from B.
    Add one at a time, alternating parents, each time the unused path
    with least overlap against the child so far.
    """
    pool_a = [list(p) for p in (group_a or []) if is_valid_path(graph, p)]
    pool_b = [list(p) for p in (group_b or []) if is_valid_path(graph, p)]
    n_from_a = draw_r(k)
    n_from_b = k - n_from_a
    child, used = [], set()
    taken_a = taken_b = 0
    take_a = True

    while len(child) < k:
        use_a = (
            (take_a and taken_a < n_from_a and pool_a)
            or (taken_b >= n_from_b or not pool_b)
        ) and taken_a < n_from_a and pool_a
        if use_a:
            path, idx = pick_least_overlap(pool_a, used, graph)
            if path is None:
                break
            child.append(path)
            used |= path_edges(path)
            pool_a.pop(idx)
            taken_a += 1
        elif taken_b < n_from_b and pool_b:
            path, idx = pick_least_overlap(pool_b, used, graph)
            if path is None:
                break
            child.append(path)
            used |= path_edges(path)
            pool_b.pop(idx)
            taken_b += 1
        else:
            break
        take_a = not take_a

    return ensure_k_paths(child, graph, s, t, k)


def crossover_with_overlap_and_repair(ind1, ind2):
    """
    Two-point swap of demand groups, then within each demand:
    mix r paths from one parent and k-r from the other.
    Stops greedy least-overlap rebuilding a single feasible parent.
    """
    tools.cxTwoPoint(ind1, ind2)
    for i, (s, t, k) in enumerate(demands):
        g1 = [list(p) for p in ind1[i]]
        g2 = [list(p) for p in ind2[i]]
        ind1[i] = mix_parent_paths(g1, g2, k, G, s, t)
        ind2[i] = mix_parent_paths(g2, g1, k, G, s, t)
    regenerative_repair(ind1, G, demands)
    regenerative_repair(ind2, G, demands)
    return ind1, ind2


def mutate_and_repair(individual, indpb=MUT_PATH_PB, L=L_SHORTEST):
    for i, (source, target, k) in enumerate(demands):
        group = list(individual[i])
        for j in range(len(group)):
            if random.random() < indpb:
                new_path = cost_weighted_path(G, source, target, L=L)
                if new_path is not None:
                    group[j] = new_path
        individual[i] = ensure_k_paths(group, G, source, target, k)
    regenerative_repair(individual, G, demands)
    return (individual,)


def mutate_yen_pairs(individual, pair_frac=PAIR_FRAC):
    n = len(demands)
    n_mut = max(1, int(round(pair_frac * n)))
    idxs = random.sample(range(n), min(n_mut, n))
    for i in idxs:
        s, t, k = demands[i]
        individual[i] = yen_paths_for_demand(G, s, t, k)
    regenerative_repair(individual, G, demands)
    return (individual,)


def mutate_combined(individual):
    if random.random() < YEN_MUT_PB:
        return mutate_yen_pairs(individual, pair_frac=PAIR_FRAC)
    return mutate_and_repair(individual)


# =============================================================================
# 5. INITIAL POPULATION (pure GA)
# =============================================================================
def create_individual():
    individual = []
    for s, t, k in demands:
        paths = []
        for _ in range(k):
            if random.random() < 0.6:
                path = cost_weighted_path(G, s, t)
                if path is None:
                    try:
                        path = nx.shortest_path(G, s, t, weight="cost")
                    except Exception:
                        path = generate_random_path(G, s, t)
            else:
                path = generate_random_path(G, s, t)
                if not path or not is_valid_path(G, path):
                    path = cost_weighted_path(G, s, t)
                    if path is None:
                        try:
                            path = nx.shortest_path(G, s, t, weight="cost")
                        except Exception:
                            path = None
            if path is not None:
                paths.append(path)
        individual.append(ensure_k_paths(paths, G, s, t, k))
    return individual


# =============================================================================
# 6. DEAP WIRING
# =============================================================================
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("individual", tools.initIterate, creator.Individual, create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate)
toolbox.register("select", tools.selTournament, tournsize=TOURNSIZE)
toolbox.register("mate", crossover_with_overlap_and_repair)
toolbox.register("mutate", mutate_combined)


# =============================================================================
# 7. MAIN
# =============================================================================
def main():
    random.seed(RANDOM_SEED)
    pop = toolbox.population(n=POP_SIZE)
    pop[0] = k_shortest_individual(G, demands, k=K_PATHS)
    pop[0].fitness.values = toolbox.evaluate(pop[0])
    seed_ind = pop[0]
    seed_unique = unique_edge_cost(seed_ind, G)
    print("Seeded generation 0 with exact k-shortest individual")
    print(f"Seed unique-edge cost: {seed_unique:,.0f}")
    print(f"YEN_MUT_PB={YEN_MUT_PB} PAIR_FRAC={PAIR_FRAC}")

    hof = tools.HallOfFame(5)
    start = time.time()
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("min", min)
    stats.register("avg", lambda x: sum(x) / len(x) if x else 0)

    print("Starting pure GA")
    print(f"USE_ER={USE_ER} n={ER_N} p={ER_P} seed={ER_SEED}")
    print(f"N={POP_SIZE}, generations={N_GENERATIONS}, cxpb={CXPB}, mutpb={MUTPB}")

    algorithms.eaSimple(
        pop, toolbox,
        cxpb=CXPB, mutpb=MUTPB, ngen=N_GENERATIONS,
        stats=stats, halloffame=hof, verbose=True,
    )

    ga_time = time.time() - start
    best = best_unique_individual([seed_ind] + list(hof) + list(pop), G)
    best_fitness = best.fitness.values[0] if best.fitness.valid else None
    best_deployment_cost = unique_edge_cost(best, G)

    print("=" * 70)
    print("EVOLUTION FINISHED")
    print(f"Seed unique-edge cost:          {seed_unique:,.0f}")
    print(f"Best unique-edge cost recorded: {best_deployment_cost:,.0f}")
    if best_fitness is not None:
        print(f"Fitness of that individual:     {best_fitness:,.0f}")
    print("Path counts per demand:")
    for i, (s, t, k) in enumerate(demands):
        print(
            f"  {i}: {s} -> {t}  n_paths={len(best[i])}  "
            f"lens={[len(p) for p in best[i]]}"
        )
    print("=" * 70)

    total_k, k_time, _ = run_k_shortest_baseline(G, demands, k=K_PATHS)
    reduction = 0.0
    if total_k > 0:
        reduction = round(100 * (total_k - best_deployment_cost) / total_k, 1)
    summary = pd.DataFrame({
        "Method": ["k-Shortest", "Pure GA"],
        "Total_Cost": [total_k, best_deployment_cost],
        "Runtime_s": [round(k_time, 4), round(ga_time, 2)],
        "Cost_Reduction_%": [0, reduction],
        "YEN_MUT_PB": [None, YEN_MUT_PB],
        "PAIR_FRAC": [None, PAIR_FRAC],
    })
    print("\nFINAL RESULTS")
    print(summary.to_string(index=False))

    os.makedirs("results", exist_ok=True)
    summary.to_csv("results/pure_ga_comparison.csv", index=False)
    with open("results/best_redundant_paths.json", "w") as f:
        json.dump(
            {
                "best_fitness": float(best_fitness) if best_fitness is not None else None,
                "best_deployment_cost": float(best_deployment_cost),
                "seed_unique_cost": float(seed_unique),
                "yen_mut_pb": YEN_MUT_PB,
                "pair_frac": PAIR_FRAC,
                "individual": best,
                "demands": demands,
                "graph": {"use_er": USE_ER, "n": ER_N, "p": ER_P, "seed": ER_SEED},
            },
            f,
            indent=2,
        )
    print("Saved results/best_redundant_paths.json")


if __name__ == "__main__":
    main()