import plotly.graph_objs as go
from plotly.offline import plot
from typing import Optional, List
from models import Mall, Shop, Connector
import networkx as nx

def visualize_mall(mall: Mall, path: Optional[List[str]] = None):
    G = nx.Graph()
    pos = {}
    labels = {}
    floor_levels = set()

    # Collect floor levels
    for floor in mall.floors.values():
        floor_levels.add(floor.level)
    floor_levels = sorted(floor_levels)

    # Build the graph and positions
    for node_id in mall.graph:
        G.add_node(node_id)
        entity = mall.get_entity_by_node_id(node_id)

        if entity:
            # Get floor level
            if isinstance(entity, Shop):
                floor_level = entity.floor.level
            elif isinstance(entity, Connector):
                floor_level = int(node_id.split(' @ Level ')[-1])
            else:
                continue

            # Calculate positions
            x = entity.x
            y = entity.y
            z = floor_level  # Use z-axis for floor levels

            pos[node_id] = (x, y, z)

            label = node_id.replace('Connector:', '')
            labels[node_id] = label

    # Add edges to the graph
    for node_id, neighbors in mall.graph.items():
        for neighbor_id, _ in neighbors:
            G.add_edge(node_id, neighbor_id)

    # Create edge traces
    edge_traces = []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_trace = go.Scatter3d(
            x=[x0, x1, None],
            y=[y0, y1, None],
            z=[z0, z1, None],
            mode='lines',
            line=dict(color='gray', width=2),
            hoverinfo='none'
        )
        edge_traces.append(edge_trace)

    # Create node traces
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_color = []
    node_symbol = []

    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_text.append(labels[node])

        if path and node in path:
            node_color.append('red')
        elif "Connector:" in node:
            node_color.append('blue')
        else:
            node_color.append('green')

        if "Connector:" in node:
            node_symbol.append('square')
        else:
            node_symbol.append('circle')

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        marker=dict(
            size=8,
            color=node_color,
            symbol=node_symbol,
            line=dict(width=1, color='black')
        ),
        hoverinfo='text'
    )

    # Create layout
    layout = go.Layout(
        title='Mall Navigation (3D Visualization)',
        showlegend=False,
        scene=dict(
            xaxis_title='X Position',
            yaxis_title='Y Position',
            zaxis_title='Floor Level',
            zaxis=dict(
                tickvals=floor_levels,
                ticktext=[f'Floor {level}' for level in floor_levels]
            )
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )

    # Combine traces
    data = edge_traces + [node_trace]

    fig = go.Figure(data=data, layout=layout)

    # Display the figure
    plot(fig, filename='mall_navigation.html')
