import pandas as pd
import random
import os

random.seed(42)

# Create folder
os.makedirs("simplified_graph", exist_ok=True)

# Generate 250 random edges
num_nodes = 80
nodes = [f"node_{i}" for i in range(num_nodes)]
edges = []
seen = set()

while len(edges) < 250:
    u = random.choice(nodes)
    v = random.choice(nodes)
    if u == v: 
        continue
    edge = tuple(sorted([u, v]))
    if edge in seen: 
        continue
    seen.add(edge)
    
    length = round(random.uniform(0.5, 25.0), 2)
    cost = round(length * 1000)
    
    edges.append({
        'source': u,
        'target': v,
        'weight': cost,
        'cost': cost,
        'length': length,
        'capacity': random.choice([500, 800, 1000, 1200]),
        'failure_prob': round(random.uniform(0.005, 0.03), 3)
    })

df = pd.DataFrame(edges)
df.to_csv("simplified_graph/graph_edges.csv", index=False)

print(f"✅ Successfully created graph_edges.csv with {len(df)} edges")
print("First 5 rows:")
print(df.head())