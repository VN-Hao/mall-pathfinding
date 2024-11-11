import heapq
import math
from typing import List, Dict, Tuple, Optional, Union
from models import Mall, Shop, Connector

def find_shortest_path(
    mall: Mall,
    start_shop_name: str,
    end_shop_name: str,
    accessibility_required: bool = False
) -> Union[List[str], str]:
    # Get all node IDs for the start and end shops
    start_nodes = mall.get_shop_node_ids(start_shop_name)
    end_nodes = set(mall.get_shop_node_ids(end_shop_name))

    if not start_nodes or not end_nodes:
        return "One or both shops are not in the mall."

    # Prepare positions for heuristic function
    end_positions = {}
    for end_node in end_nodes:
        entity = mall.get_entity_by_node_id(end_node)
        if entity:
            # Extract the floor level
            if isinstance(entity, Shop):
                end_level = entity.floor.level
            elif isinstance(entity, Connector):
                # Extract the level from the node_id
                parts = end_node.split(' @ Level ')
                end_level = int(parts[-1])
            else:
                continue  # Skip unknown entity types
            end_positions[end_node] = (entity.x, entity.y, end_level)

    def heuristic(node_id: str) -> float:
        entity = mall.get_entity_by_node_id(node_id)
        if not entity:
            return float('inf')

        # Extract the floor level
        if isinstance(entity, Shop):
            entity_level = entity.floor.level
        elif isinstance(entity, Connector):
            # For Connectors, extract the level from the node_id
            parts = node_id.split(' @ Level ')
            entity_level = int(parts[-1])
        else:
            return float('inf')  # Unknown entity type

        min_distance = float('inf')
        for x, y, level in end_positions.values():
            level_difference = abs(entity_level - level)
            dx = entity.x - x
            dy = entity.y - y
            distance = math.hypot(dx, dy) + (level_difference * 10)  # Adjust floor weight as needed
            if distance < min_distance:
                min_distance = distance
        return min_distance

    # A* Algorithm Initialization
    heap = []
    visited = {}
    for start_node in start_nodes:
        heapq.heappush(heap, (heuristic(start_node), 0, start_node, [start_node]))
        visited[start_node] = 0

    while heap:
        est_total_cost, cost_so_far, current_node, path = heapq.heappop(heap)

        if current_node in end_nodes:
            return path

        if visited[current_node] < cost_so_far:
            continue

        for neighbor, weight in mall.graph.get(current_node, []):
            # Check accessibility
            if accessibility_required:
                if "Connector:" in neighbor:
                    connector = mall.get_connector_by_node_id(neighbor)
                    if connector and not connector.accessible:
                        continue
            new_cost = cost_so_far + weight
            if neighbor not in visited or new_cost < visited[neighbor]:
                visited[neighbor] = new_cost
                total_estimated_cost = new_cost + heuristic(neighbor)
                heapq.heappush(heap, (total_estimated_cost, new_cost, neighbor, path + [neighbor]))

    return "No path found between the shops."
