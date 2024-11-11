import json
import difflib
from models import Mall, Floor, Shop, Connector
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

    # Create connections
    for floor_data in data['floors']:
        level = floor_data['level']
        floor = floor_objects[level]
        for conn in floor_data.get('connections', []):
            from_entity = floor.shops.get(conn['from']) or floor.connectors.get(conn['from'])
            to_entity = floor.shops.get(conn['to']) or floor.connectors.get(conn['to'])
            if from_entity and to_entity:
                add_connection(from_entity, to_entity, level)
                add_connection(to_entity, from_entity, level)

    # Build the graph
    mall.build_graph()
    return mall

def add_connection(entity, connected_entity, level):
    if isinstance(entity, Shop):
        entity.connections.append(connected_entity)
    elif isinstance(entity, Connector):
        entity.connections[level].append(connected_entity)
