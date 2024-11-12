import json
import difflib
from models import Mall, Floor, Shop, Connector, Corridor, CorridorNode
from typing import Dict

def load_mall_from_json(file_path: str) -> Mall:
    with open(file_path, 'r') as f:
        data = json.load(f)
    mall = Mall()
    floor_objects: Dict[int, Floor] = {}
    connectors: Dict[str, Connector] = {}

    # Create floors
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = Floor(level=level)
        mall.add_floor(floor)
        floor_objects[level] = floor

    # Create connectors
    for connector_data in data.get('connectors', []):
        name = connector_data['name']
        connector = Connector(
            name=name,
            connector_type=connector_data.get('type', 'elevator'),
            accessible=connector_data.get('accessible', True),
            direction=connector_data.get('direction', 'both'),
            x=connector_data.get('x', 0),
            y=connector_data.get('y', 0)
        )
        connectors[name] = connector

    # Assign connectors to floors
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = floor_objects[level]
        for conn_name in floor_data.get('connectors', []):
            connector = connectors.get(conn_name)
            if connector:
                connector.floors.append(floor)
                floor.connectors[conn_name] = connector

    # First, load all corridor nodes
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = floor_objects[level]
        for corridor_data in floor_data.get('corridors', []):
            for node_data in corridor_data['nodes']:
                node = CorridorNode(
                    id=node_data['id'],
                    x=node_data['x'],
                    y=node_data['y'],
                    floor=floor
                )
                floor.corridor_nodes[node.id] = node

    # Then, process corridors and their connections
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = floor_objects[level]
        for corridor_data in floor_data.get('corridors', []):
            corridor_nodes = [floor.corridor_nodes[node_data['id']] for node_data in corridor_data['nodes']]
            corridor = Corridor(
                id=corridor_data['id'],
                floor=floor,
                nodes=corridor_nodes
            )
            floor.corridors[corridor.id] = corridor
            # Connect corridor nodes
            for conn in corridor_data.get('connections', []):
                from_node = floor.corridor_nodes.get(conn['from'])
                to_node = floor.corridor_nodes.get(conn['to'])
                if from_node and to_node:
                    from_node.connections.append(to_node)
                    to_node.connections.append(from_node)
                else:
                    print(f"Warning: Could not find nodes {conn['from']} or {conn['to']} on floor {floor.level}")

    # Create shops
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = floor_objects[level]
        for shop_data in floor_data.get('shops', []):
            shop = Shop(
                name=shop_data['name'],
                floor=floor,
                x=shop_data.get('x', 0),
                y=shop_data.get('y', 0)
            )
            floor.shops[shop.name] = shop

    # Build the graph
    mall.build_graph()
    return mall

def add_connection(entity, connected_entity, level):
    if isinstance(entity, Shop):
        entity.connections.append(connected_entity)
    elif isinstance(entity, Connector):
        entity.connections[level].append(connected_entity)
