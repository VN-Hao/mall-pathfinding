import math
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Union
import difflib

class Shop:
    def __init__(self, name: str, floor: 'Floor', x: float = 0, y: float = 0):
        self.name = name
        self.floor = floor  # Reference to the Floor object
        self.x = x  # X-coordinate
        self.y = y  # Y-coordinate
        self.connections: List[Union['Shop', 'Connector']] = []  # Adjacent shops or connectors

    def __repr__(self):
        return f"{self.name} @ Level {self.floor.level}"

class Connector:
    def __init__(
        self,
        name: str,
        connector_type: str = 'elevator',
        accessible: bool = True,
        direction: str = 'both',
        x: float = 0,
        y: float = 0
    ):
        self.name = name
        self.connector_type = connector_type  # 'elevator', 'escalator', 'stairs'
        self.accessible = accessible  # True if accessible (e.g., elevator)
        self.direction = direction  # 'up', 'down', 'both'
        self.x = x  # X-coordinate
        self.y = y  # Y-coordinate
        self.floors: List['Floor'] = []  # List of Floor objects it connects
        self.connections: Dict[int, List[Union['Shop', 'Connector']]] = defaultdict(list)  # floor_level: [connected shops]

    def __repr__(self):
        floor_levels = [floor.level for floor in self.floors]
        return f"{self.name} @ Levels {floor_levels}"

    def get_vertical_weight(self, from_level: int, to_level: int) -> float:
        # Weight for moving between floors, can be adjusted as needed
        return abs(to_level - from_level) * 5  # Example: 5 units per floor

    def is_accessible_between_floors(self, from_level: int, to_level: int) -> bool:
        # Check directionality and accessibility
        if self.connector_type == 'escalator':
            if self.direction == 'up' and to_level > from_level:
                return True
            elif self.direction == 'down' and to_level < from_level:
                return True
            elif self.direction == 'both':
                return True
            else:
                return False
        else:
            # Elevators and stairs
            return True

class Floor:
    def __init__(self, level: int):
        self.level = level
        self.shops: Dict[str, Shop] = {}  # name: Shop object
        self.connectors: Dict[str, Connector] = {}  # name: Connector object

    def __repr__(self):
        return f"Floor {self.level}"

class Mall:
    def __init__(self):
        self.floors: Dict[int, Floor] = {}  # level: Floor object
        self.graph: Dict[str, List[Tuple[str, float]]] = {}  # node_id: [(connected_node_id, weight)]

    def add_floor(self, floor: Floor):
        self.floors[floor.level] = floor

    def get_node_id(self, entity: Union[Shop, Connector], floor_level: Optional[int] = None) -> str:
        if isinstance(entity, Shop):
            return f"{entity.name} @ Level {entity.floor.level}"
        elif isinstance(entity, Connector):
            if floor_level is None:
                raise ValueError("floor_level must be provided for Connector")
            return f"Connector:{entity.name} @ Level {floor_level}"
        else:
            raise ValueError("Unknown entity type")

    def get_shop_node_ids(self, shop_name: str) -> List[str]:
        node_ids = []
        possible_names = set()
        for floor in self.floors.values():
            for shop in floor.shops.values():
                possible_names.add(shop.name)
                if shop.name.lower() == shop_name.lower():
                    node_id = self.get_node_id(shop)
                    node_ids.append(node_id)
        if not node_ids:
            print(f"Shop '{shop_name}' not found. Did you mean:")
            suggestions = difflib.get_close_matches(shop_name, possible_names)
            for suggestion in suggestions:
                print(f" - {suggestion}")
        return node_ids

    def get_entity_by_node_id(self, node_id: str) -> Optional[Union[Shop, Connector]]:
        if "Connector:" in node_id:
            name, level = node_id.replace("Connector:", "").split(" @ Level ")
            level = int(level)
            floor = self.floors.get(level)
            if floor:
                return floor.connectors.get(name)
        else:
            name, level = node_id.split(" @ Level ")
            level = int(level)
            floor = self.floors.get(level)
            if floor:
                return floor.shops.get(name)
        return None

    def get_connector_by_node_id(self, node_id: str) -> Optional[Connector]:
        if "Connector:" in node_id:
            name, level = node_id.replace("Connector:", "").split(" @ Level ")
            level = int(level)
            floor = self.floors.get(level)
            if floor:
                return floor.connectors.get(name)
        return None

    def build_graph(self):
        self.graph = {}
        # Add shops and their connections to the graph
        for floor in self.floors.values():
            floor_level = floor.level
            for shop in floor.shops.values():
                node_id = self.get_node_id(shop)
                self.graph.setdefault(node_id, [])
                for connected in shop.connections:
                    if isinstance(connected, Shop):
                        connected_id = self.get_node_id(connected)
                    elif isinstance(connected, Connector):
                        connected_id = self.get_node_id(connected, floor_level)
                    else:
                        continue
                    weight = calculate_weight(shop, connected, floor_level)
                    self.graph[node_id].append((connected_id, weight))
                # No need to add the reverse edge here; it will be added when processing the other node

            # Add connectors and their connections to the graph
            for connector in floor.connectors.values():
                node_id = self.get_node_id(connector, floor_level)
                self.graph.setdefault(node_id, [])
                for connected in connector.connections[floor_level]:
                    if isinstance(connected, Shop):
                        connected_id = self.get_node_id(connected)
                    elif isinstance(connected, Connector):
                        connected_id = self.get_node_id(connected, floor_level)
                    else:
                        continue
                    weight = calculate_weight(connector, connected, floor_level)
                    self.graph[node_id].append((connected_id, weight))
                # Connect connectors across floors
                for other_floor in connector.floors:
                    other_level = other_floor.level
                    if other_level != floor_level:
                        other_node_id = self.get_node_id(connector, other_level)
                        weight = connector.get_vertical_weight(floor_level, other_level)
                        if connector.is_accessible_between_floors(floor_level, other_level):
                            self.graph[node_id].append((other_node_id, weight))

    def __repr__(self):
        return f"Mall with Floors: {list(self.floors.keys())}"

def calculate_weight(entity1: Union[Shop, Connector], entity2: Union[Shop, Connector], floor_level: int) -> float:
    # Euclidean distance between two entities
    dx = entity1.x - entity2.x
    dy = entity1.y - entity2.y
    distance = math.hypot(dx, dy)
    return distance
