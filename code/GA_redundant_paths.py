"""
GA for Redundant Pathways in Telecommunication Networks
Variable-length chromosome + basic regenerative operators
For Honours Thesis - Liam Suter
"""

import sys
import os
import json
import random
import pandas as pd
import networkx as nx
from deap import base, creator, tools, algorithms

# ====================== PATH FIX ======================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ====================== LOAD GRAPH ======================
def load_graph(csv_path="../dataset/simplified_graph/graph_edges.csv"):
    df = pd.read_csv(csv_path)
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(
            str(row['source']),
            str(row['target']),
            weight=float(row['weight']),
            cost=float(row['cost']),
            length=float(row['length']),
            failure_prob=float(row.get('failure_prob', 0.01))
        )
    print(f"✅ Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


G = load_graph()

# ====================== DEMANDS (Source-Target + k redundant paths) ======================
demands = [
    ("node_0", "node_79", 2),
    ("node_14", "node_53", 2),
    ("node_27", "node_68", 3),
    ("node_3", "node_77", 2),
    ("node_11", "node_69", 2),
    ("node_22", "node_55", 3),
    ("node_30", "node_70", 2),
    ("node_8", "node_48", 2),
    ("node_19", "node_65", 2),
    ("node_37", "node_72", 3),
]

# ====================== VARIABLE-LENGTH CHROMOSOME ======================
def create_individual():
    """Each individual = list of path lists (one group per demand)"""
    individual = []
    for s, t, k in demands:
        paths = []
        for _ in range(k):
            try:
                path = nx.shortest_path(G, s, t, weight='weight')
            except nx.NetworkXNoPath:
                path = [s, t]  # fallback
            paths.append(path)
        individual.append(paths)
    return individual


def evaluate(individual):
    """Fitness = total cost + penalty for overlapping paths"""
    total_cost = 0.0
    overlap_penalty = 0.0
    used_edges = set()

    for paths in individual:
        local_edges = set()
        for path in paths:
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge = tuple(sorted([u, v]))
                cost = G[u][v]['cost']
                total_cost += cost

                if edge in local_edges:
                    overlap_penalty += 5000  # heavy penalty for non-disjoint
                local_edges.add(edge)
        used_edges.update(local_edges)

    return (total_cost + overlap_penalty,)


# ====================== DEAP SETUP ======================
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("individual", tools.initIterate, creator.Individual, create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)


# ====================== MAIN ======================
def main():
    random.seed(42)
    pop = toolbox.population(n=60)
    hof = tools.HallOfFame(5)
    
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("min", min)
    stats.register("avg", lambda x: sum(x)/len(x) if x else 0)

    print("🚀 Starting GA for Redundant Pathways Optimisation...\n")
    
    algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.3, ngen=150,
                       stats=stats, halloffame=hof, verbose=True)

    # Save best solution
    best = hof[0]
    best_cost = best.fitness.values[0]
    
    print("\n" + "="*60)
    print("✅ EVOLUTION FINISHED")
    print(f"Best total cost: {best_cost:,.0f}")
    print("="*60)

    result = {
        "best_cost": float(best_cost),
        "individual": best,
        "demands": demands
    }
    
    os.makedirs("results", exist_ok=True)
    with open("results/best_redundant_paths.json", "w") as f:
        json.dump(result, f, indent=2)

    print("💾 Best solution saved to results/best_redundant_paths.json")


if __name__ == "__main__":
    main()