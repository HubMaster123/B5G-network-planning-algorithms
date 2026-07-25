"""
Generate 1000-Node Simplified Graph for Thesis Experiments
Liam Suter - Honours Thesis
"""

import networkx as nx
import pandas as pd
import random
import os

random.seed(42)  # Reproducible

# ====================== PARAMETERS ======================
n_nodes = 1000
target_edges = 8500          # ~ average degree ~17 (reasonable for telecom backbone)
output_dir = "../dataset/1000_node_simplified_graph"
output_file = f"{output_dir}/graph_edges.csv"

# ====================== GENERATE GRAPH ======================
print("Generating 1000-node graph...")

# Use random geometric graph for more realistic spatial distribution
G = nx.random_geometric_graph(n_nodes, radius=0.12, seed=42)

# If too few edges, add more using preferential attachment style
if G.number_of_edges() < target_edges:
    G = nx.barabasi_albert_graph(n_nodes, m=9, seed=42)  # Good scale-free properties

# Ensure we have enough edges
while G.number_of_edges() < target_edges:
    u = random.randint(0, n_nodes-1)
    v = random.randint(0, n_nodes-1)
    if u != v and not G.has_edge(u, v):
        G.add_edge(u, v)

print(f"Generated graph → {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ====================== ADD ATTRIBUTES ======================
for u, v in G.edges():
    length = round(random.uniform(5, 80), 2)          # km
    cost = round(length * 1200, 2)                    # cost scaling (you can adjust)
    G[u][v]['length'] = length
    G[u][v]['cost'] = cost
    G[u][v]['weight'] = cost                          # for shortest path
    G[u][v]['failure_prob'] = round(random.uniform(0.005, 0.025), 4)
    G[u][v]['capacity'] = 1000.0

# ====================== SAVE AS CSV ======================
os.makedirs(output_dir, exist_ok=True)

edges = []
for u, v in G.edges():
    edges.append({
        'source': str(u),
        'target': str(v),
        'weight': G[u][v]['weight'],
        'cost': G[u][v]['cost'],
        'length': G[u][v]['length'],
        'capacity': G[u][v]['capacity'],
        'failure_prob': G[u][v]['failure_prob']
    })

df = pd.DataFrame(edges)
df.to_csv(output_file, index=False)

print(f"\n✅ 1000-node graph successfully created!")
print(f"   Nodes : {G.number_of_nodes()}")
print(f"   Edges : {G.number_of_edges()}")
print(f"   Saved to: {output_file}")
print(f"   Average degree: {2*G.number_of_edges()/G.number_of_nodes():.2f}")