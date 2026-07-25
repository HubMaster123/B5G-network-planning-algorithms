"""
k-Shortest Paths Baseline for Redundant Pathways
Clean, reusable baseline for comparison with GA
"""

import time
import pandas as pd
import networkx as nx
from itertools import islice


def run_k_shortest_baseline(G, demands, k=3):
    """Run k-Shortest Paths baseline and return results + runtime"""
    print("🚀 Running k-Shortest Paths Baseline...")
    start = time.time()
    results = []
    
    for s, t, _ in demands:
        try:
            # Get up to k shortest simple paths
            paths = list(islice(nx.shortest_simple_paths(G, s, t, weight='cost'), k))
            total_cost = sum(sum(G[u][v]['cost'] for u, v in zip(p, p[1:])) for p in paths)
            
            results.append({
                'demand': f"{s}→{t}",
                'method': 'k-shortest',
                'num_paths': len(paths),
                'total_cost': round(total_cost, 2)
            })
        except Exception:
            results.append({
                'demand': f"{s}→{t}", 
                'method': 'k-shortest', 
                'num_paths': 0, 
                'total_cost': 999999
            })
    
    runtime = time.time() - start
    print(f"✅ k-Shortest completed in {runtime:.4f}s")
    
    return pd.DataFrame(results), runtime


# For standalone testing
if __name__ == "__main__":
    from GA_redundant_paths import G, demands
    df, runtime = run_k_shortest_baseline(G, demands, k=3)
    print(df)
    print(f"Total Cost: {df['total_cost'].sum():,.0f}")