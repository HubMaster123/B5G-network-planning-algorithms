import pandas as pd
import json
from modules.data_classes.dataclass_roads import RoadGraph   # your existing loader

# 1. Load your current small-dataset
road_graph = RoadGraph.load_from_json("../dataset/small-dataset/road_edges.json")  # adjust path

edges_list = []

for (u, v), segment in road_graph.segments.items():import json
import pandas as pd
import os

# Path to your small-dataset
input_file = "../dataset/small-dataset/road_edges.json"
output_dir = "simplified_graph"
os.makedirs(output_dir, exist_ok=True)
output_file = f"{output_dir}/graph_edges.csv"

# Load the raw JSON
with open(input_file, "r") as f:
    data = json.load(f)

# Extract edges
edges = []
for edge in data.get("road_edges", []):
    u = str(edge["from"])
    v = str(edge["to"])
    length = float(edge.get("length", 0))
    cost = length * 1000  # Simple cost = length * 1000 (adjust multiplier as needed)

    if u < v:  # Avoid duplicate undirected edges
        edges.append({
            'source': u,
            'target': v,
            'weight': cost,      # Used for pathfinding
            'cost': cost,
            'length': length,
            'capacity': 1000.0,
            'failure_prob': 0.01
        })

# Save to CSV
df = pd.DataFrame(edges)
df.to_csv(output_file, index=False)

print(f"✅ Created simple graph with {len(df)} edges")
print(df.head(10))
print(f"File saved at: {output_file}")
    if u < v:   # avoid duplicate edges
        edges_list.append({
            'source': str(u),
            'target': str(v),
            'weight': segment.cost,          # for pathfinding
            'cost': segment.cost,
            'length': segment.length,
            'capacity': 1000.0,              # placeholder - adjust later
            'failure_prob': 0.01             # default 1%
        })

# 2. Save
df = pd.DataFrame(edges_list)
df.to_csv("simplified_graph/graph_edges.csv", index=False)

print(f"✅ Saved {len(df)} edges to graph_edges.csv")
print(df.head())