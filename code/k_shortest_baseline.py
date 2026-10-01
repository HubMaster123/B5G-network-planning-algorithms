"""
k-Shortest Paths Baseline for Redundant Pathways
Shared baseline for fair comparison with GA / Hybrid
Cost = sum of unique edge costs across all demands
"""

import time
import pandas as pd
import networkx as nx
from itertools import islice


def run_k_shortest_baseline(G, demands, k=3):
    """
    Returns
    -------
    total_cost : float
        Deployment cost using unique edges across all demands
    runtime : float
    details : DataFrame
        Optional per-demand info (for debugging)
    """
    print("🚀 Running k-Shortest Paths Baseline...")
    start = time.time()

    all_edges = set()
    rows = []

    for s, t, _ in demands:
        try:
            paths = list(islice(nx.shortest_simple_paths(G, s, t, weight='cost'), k))
            demand_edges = set()
            for p in paths:
                for u, v in zip(p, p[1:]):
                    e = tuple(sorted([u, v]))
                    demand_edges.add(e)
                    all_edges.add(e)
            demand_cost = sum(G[u][v]['cost'] for u, v in demand_edges)
            rows.append({
                'demand': f"{s}→{t}",
                'method': 'k-shortest',
                'num_paths': len(paths),
                'demand_unique_cost': round(demand_cost, 2)
            })
        except Exception:
            rows.append({
                'demand': f"{s}→{t}",
                'method': 'k-shortest',
                'num_paths': 0,
                'demand_unique_cost': None
            })

    total_cost = sum(G[u][v]['cost'] for u, v in all_edges)
    runtime = time.time() - start
    print(f"✅ k-Shortest completed in {runtime:.4f}s | Total unique-edge cost: {total_cost:,.0f}")

    return total_cost, runtime, pd.DataFrame(rows)


if __name__ == "__main__":
    from GA_redundant_paths import G, demands
    total, runtime, df = run_k_shortest_baseline(G, demands, k=3)
    print(df)
    print(f"Total unique-edge cost: {total:,.0f}")