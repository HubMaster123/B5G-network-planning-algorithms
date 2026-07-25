import networkx as nx
import pandas as pd
import random
import os

random.seed(42)

# Generate a larger random graph (300 nodes, reasonable density)
n_nodes = 300
G = nx.random_geometric_graph(n_nodes, radius=0.15)   # good for telecom-like connectivity

# Add realistic attributes
for u, v in G.edges():
    length = round(random.uniform(1, 50), 2)
    G[u][v]['length'] = length
    G[u][v]['cost'] = round(length * 1000, 2)      # your current scaling
    G[u][v]['weight'] = G[u][v]['cost']
    G[u][v]['failure_prob'] = round(random.uniform(0.005, 0.03), 4)
    G[u][v]['capacity'] = 1000.0

# Save as CSV in new folder
output_dir = "large_simplified_graph"
os.makedirs(output_dir, exist_ok=True)
output_file = f"{output_dir}/graph_edges.csv"

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

print(f"✅ Created large simplified graph:")
print(f"   Nodes : {G.number_of_nodes()}")
print(f"   Edges : {G.number_of_edges()}")
print(f"   Saved to: {output_file}")