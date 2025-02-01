import networkx as nx
import matplotlib.pyplot as plt

# Create a directed graph
G = nx.DiGraph()

# Add agents as nodes (blue color)
agents = [
    "global_planification",
    "weather_monitor",
    "stock_resources_manager",
    "route_optimizer",
    "notifications_alerts_manager"
]

tasks = [
    "weather_data_collection",
    "traffic_data_integration",
    "resource_monitoring",
    "route_optimization",
    "stakeholder_communication"
]

# Add nodes with different colors for agents and tasks
agent_nodes = [(agent, {"color": "lightblue"}) for agent in agents]
task_nodes = [(task, {"color": "lightgreen"}) for task in tasks]
G.add_nodes_from(agent_nodes)
G.add_nodes_from(task_nodes)

# Add edges based on the crew.py workflow
edges = [
    ("weather_monitor", "weather_data_collection"),
    ("weather_data_collection", "traffic_data_integration"),
    ("stock_resources_manager", "resource_monitoring"),
    ("route_optimizer", "route_optimization"),
    ("notifications_alerts_manager", "stakeholder_communication")
]

G.add_edges_from(edges)

# Set up the plot
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=1, iterations=50)

# Draw nodes
node_colors = [G.nodes[node]["color"] for node in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000)

# Draw edges
nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)

# Draw labels
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

# Save the plot
plt.savefig("flow_diagram.svg", format="svg", bbox_inches="tight")
plt.close()
