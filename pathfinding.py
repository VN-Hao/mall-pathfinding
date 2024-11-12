import heapq
import math
from typing import List, Dict, Tuple, Optional, Union
from models import Mall, Shop, Connector, CorridorNode

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
            if isinstance(entity, Shop):
                end_level = entity.floor.level
            elif isinstance(entity, Connector):
                parts = end_node.split(' @ Level ')
                end_level = int(parts[-1])
            elif isinstance(entity, CorridorNode):
                end_level = entity.floor.level
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
            parts = node_id.split(' @ Level ')
            entity_level = int(parts[-1])
        elif isinstance(entity, CorridorNode):
            entity_level = entity.floor.level
        else:
            return float('inf')  # Unknown entity type

        min_distance = float('inf')
        for x, y, level in end_positions.values():
            level_difference = abs(entity_level - level)
            dx = entity.x - x
            dy = entity.y - y
            distance = math.hypot(dx, dy) + (level_difference * 10)
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

def generate_instructions(mall: Mall, path: List[str]) -> List[str]:
    instructions = []
    previous_entity = None
    previous_direction = None
    previous_floor = None

    for i in range(len(path) - 1):
        current_node_id = path[i]
        next_node_id = path[i + 1]
        current_entity = mall.get_entity_by_node_id(current_node_id)
        next_entity = mall.get_entity_by_node_id(next_node_id)

        if not current_entity or not next_entity:
            continue

        # Get floor levels
        if isinstance(current_entity, (Shop, CorridorNode)):
            current_floor = current_entity.floor.level
        elif isinstance(current_entity, Connector):
            current_floor = int(current_node_id.split(' @ Level ')[-1])
        else:
            current_floor = None

        if isinstance(next_entity, (Shop, CorridorNode)):
            next_floor = next_entity.floor.level
        elif isinstance(next_entity, Connector):
            next_floor = int(next_node_id.split(' @ Level ')[-1])
        else:
            next_floor = None

        # Announce floor change
        if previous_floor is not None and current_floor != previous_floor:
            instructions.append(f"You are now on Floor {current_floor}.")

        # Calculate direction
        dx = next_entity.x - current_entity.x
        dy = next_entity.y - current_entity.y
        direction = math.degrees(math.atan2(dy, dx))

        if previous_entity:
            # Calculate previous direction
            pdx = current_entity.x - previous_entity.x
            pdy = current_entity.y - previous_entity.y
            prev_direction = math.degrees(math.atan2(pdy, pdx))
            angle_difference = (direction - prev_direction + 360) % 360

            if angle_difference < 30 or angle_difference > 330:
                turn = "Continue straight"
            elif 30 <= angle_difference < 150:
                turn = "Turn left"
            elif 210 < angle_difference <= 330:
                turn = "Turn right"
            else:
                turn = "Make a U-turn"

            # Simplify entity descriptions
            next_description = describe_entity(next_entity)
            instructions.append(f"{turn} towards {next_description}")
        else:
            # First instruction
            current_description = describe_entity(current_entity)
            next_description = describe_entity(next_entity)
            instructions.append(f"Start at {current_description}, head towards {next_description}")

        previous_entity = current_entity
        previous_floor = current_floor

    # Add final instruction
    last_entity = mall.get_entity_by_node_id(path[-1])
    if last_entity:
        last_description = describe_entity(last_entity)
        instructions.append(f"You have arrived at {last_description}.")

    return instructions

def describe_entity(entity: Union[Shop, Connector, CorridorNode]) -> str:
    if isinstance(entity, Shop):
        return f"{entity.name}"
    elif isinstance(entity, Connector):
        return f"{entity.name} ({entity.connector_type})"
    elif isinstance(entity, CorridorNode):
        return "the corridor"
    else:
        return "an unknown location"

