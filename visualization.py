import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D, art3d
from typing import Optional, List, Dict
from models import Mall, Shop, Connector, CorridorNode
import numpy as np

def visualize_mall(mall: Mall, path: Optional[List[str]] = None):
    # Create a 3D figure and axis
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Define floor height
    floor_height = 50  # Height of each floor in Z-axis units

    # Store texts for adjustment
    texts = []

    # Define colors for different elements
    floor_colors = ['#e6f2ff', '#ffe6e6', '#e6ffe6', '#f9e6ff', '#ffffe6']
    shop_color = 'green'
    corridor_color = 'gray'
    connector_color_accessible = 'blue'
    connector_color_inaccessible = 'red'

    # Iterate over each floor
    for floor_level, floor in mall.floors.items():
        z_base = floor_level * floor_height

        # Draw floor plane (optional)
        floor_size = 200  # Size of the floor plane
        xx, yy = np.meshgrid(
            np.linspace(0, floor_size, 2),
            np.linspace(0, floor_size, 2)
        )
        zz = np.full_like(xx, z_base)
        ax.plot_surface(xx, yy, zz, color=floor_colors[floor_level % len(floor_colors)], alpha=0.2)

        # Add floor label
        ax.text(
            -20,
            -20,
            z_base + floor_height / 2,
            f'Floor {floor_level}',
            fontsize=12,
            rotation=90,
            verticalalignment='center'
        )

        # Draw shops as cuboids
        for shop in floor.shops.values():
            x = shop.x
            y = shop.y
            z = z_base
            width = getattr(shop, 'width', 20)  # Default width
            depth = getattr(shop, 'depth', 15)  # Default depth
            height = getattr(shop, 'height', floor_height / 2)  # Default height

            # Define cuboid vertices
            cuboid = get_cuboid_data(
                x - width / 2,
                y - depth / 2,
                z,
                width,
                depth,
                height
            )
            # Create 3D polygon and add to plot
            ax.add_collection3d(art3d.Poly3DCollection(
                cuboid,
                facecolors=shop_color,
                edgecolors='black',
                linewidths=0.5,
                alpha=0.7
            ))

            # Add shop name
            ax.text(
                x,
                y,
                z + height + 2,
                shop.name,
                fontsize=8,
                ha='center',
                va='bottom'
            )

        # Draw corridors as lines
        for corridor in floor.corridors.values():
            for node in corridor.nodes:
                x = node.x
                y = node.y
                z = z_base
                # Draw corridor nodes as small spheres
                ax.scatter(x, y, z, color='orange', s=20)
                # Add connections
                for connected_node in node.connections:
                    x2 = connected_node.x
                    y2 = connected_node.y
                    z2 = z_base
                    ax.plot(
                        [x, x2],
                        [y, y2],
                        [z, z2],
                        color=corridor_color,
                        linewidth=2
                    )

        # Draw connectors
        for connector in floor.connectors.values():
            x = connector.x
            y = connector.y
            z = z_base
            color = connector_color_accessible if connector.accessible else connector_color_inaccessible
            shape = 's' if connector.connector_type == 'elevator' else '^'
            ax.scatter(x, y, z, marker=shape, color=color, s=50)
            # Add connector name
            ax.text(
                x,
                y,
                z + 5,
                connector.name,
                fontsize=8,
                ha='center',
                va='bottom'
            )

    # Highlight the path
    if path:
        path_positions = []
        for node_id in path:
            entity = mall.get_entity_by_node_id(node_id)
            if entity:
                if isinstance(entity, (Shop, CorridorNode)):
                    floor_level = entity.floor.level
                    x = entity.x
                    y = entity.y
                    z = floor_level * floor_height
                elif isinstance(entity, Connector):
                    floor_level = int(node_id.split(' @ Level ')[-1])
                    x = entity.x
                    y = connector.y
                    z = floor_level * floor_height
                else:
                    continue
                path_positions.append((x, y, z))
        if path_positions:
            xs, ys, zs = zip(*path_positions)
            ax.plot(xs, ys, zs, color='red', linewidth=3)

    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z (Floor Level)')
    ax.set_title('3D Mall Navigation Path')

    # Adjust the view angle for better visualization
    ax.view_init(elev=20, azim=-60)

    # Set plot limits
    max_floor = max(mall.floors.keys())
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)
    ax.set_zlim(0, (max_floor + 1) * floor_height)

    # Add legend
    shop_patch = patches.Patch(color=shop_color, label='Shop')
    corridor_patch = patches.Patch(color='orange', label='Corridor Node')
    connector_patch_accessible = patches.Patch(color=connector_color_accessible, label='Accessible Connector')
    connector_patch_inaccessible = patches.Patch(color=connector_color_inaccessible, label='Inaccessible Connector')
    path_line = plt.Line2D([0], [0], color='red', lw=3, label='Shortest Path')
    ax.legend(
        handles=[shop_patch, corridor_patch, connector_patch_accessible, connector_patch_inaccessible, path_line],
        loc='upper right'
    )

    plt.tight_layout()
    plt.show()

def get_cuboid_data(x, y, z, dx, dy, dz):
    # Returns vertices of a cuboid
    cuboid = [
        # Bottom face
        [(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z)],
        # Top face
        [(x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)],
        # Side faces
        [(x, y, z), (x + dx, y, z), (x + dx, y, z + dz), (x, y, z + dz)],
        [(x + dx, y, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x + dx, y, z + dz)],
        [(x + dx, y + dy, z), (x, y + dy, z), (x, y + dy, z + dz), (x + dx, y + dy, z + dz)],
        [(x, y + dy, z), (x, y, z), (x, y, z + dz), (x, y + dy, z + dz)]
    ]
    return cuboid
