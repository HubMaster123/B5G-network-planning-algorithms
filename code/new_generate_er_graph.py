"""
Erdős–Rényi graph generator for thesis experiments.
Saves a CSV in the same format as the existing datasets.
"""

import os
import random
import pandas as pd
import networkx as nx


def generate_er_graph(n=100, p=0.06, seed=42, cost_scale=1000):
    """Connected G(n, p) graph with cost/weight/length attributes."""
    rng = random.Random(seed)
    graph = nx.erdos_renyi_graph(n, p, seed=seed)

    # ER graphs may be disconnected; add edges until connected
    while not nx.is_connected(graph):
        u, v = rng.sample(list(graph.nodes()), 2)
        graph.add_edge(u, v)

    graph = nx.relabel_nodes(graph, {i: f"node_{i}" for i in graph.nodes()})

    for u, v in graph.edges():
        length = rng.uniform(0.5, 20.0)
        cost = length * cost_scale
        graph[u][v]["length"] = length
        graph[u][v]["cost"] = cost
        graph[u][v]["weight"] = cost
        graph[u][v]["capacity"] = 1000
        graph[u][v]["failure_prob"] = rng.uniform(0.005, 0.03)

    print(f"ER graph: n={n}, p={p}, seed={seed}, "
          f"{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    return graph


def save_er_graph(graph, path):
    rows = []
    for u, v, data in graph.edges(data=True):
        rows.append({
            "source": u,
            "target": v,
            "length": data["length"],
            "cost": data["cost"],
            "weight": data["weight"],
            "capacity": data.get("capacity", 1000),
            "failure_prob": data["failure_prob"],
        })
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Saved {path}")


def load_er_csv(path):
    df = pd.read_csv(path)
    graph = nx.Graph()
    for _, row in df.iterrows():
        graph.add_edge(
            str(row["source"]),
            str(row["target"]),
            length=float(row["length"]),
            cost=float(row["cost"]),
            weight=float(row["weight"]),
            capacity=float(row.get("capacity", 1000)),
            failure_prob=float(row.get("failure_prob", 0.01)),
        )
    return graph