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

class CorridorNode:
    def __init__(self, id: str, x: float, y: float, floor: 'Floor'):
        self.id = id  # Unique identifier
        self.x = x
        self.y = y
        self.floor = floor
        self.connections: List['CorridorNode'] = []

    def __repr__(self):
        return f"CorridorNode {self.id} @ Level {self.floor.level}"

class Corridor:
    def __init__(self, id: str, floor: 'Floor', nodes: List[CorridorNode]):
        self.id = id
        self.floor = floor
        self.nodes = nodes  # Ordered list of CorridorNodes along the corridor

    def __repr__(self):
        return f"Corridor {self.id} @ Level {self.floor.level}"

class Floor:
    def __init__(self, level: int):
        self.level = level
        self.shops: Dict[str, Shop] = {}  # name: Shop object
        self.connectors: Dict[str, Connector] = {}  # name: Connector object
        self.corridors: Dict[str, Corridor] = {}  # id: Corridor object
        self.corridor_nodes: Dict[str, CorridorNode] = {}  # id: CorridorNode object

    def __repr__(self):
        return f"Floor {self.level}"

class Mall:
    def __init__(self):
        self.floors: Dict[int, Floor] = {}  # level: Floor object
        self.graph: Dict[str, List[Tuple[str, float]]] = {}  # node_id: [(connected_node_id, weight)]

    def add_floor(self, floor: Floor):
        self.floors[floor.level] = floor

    def get_node_id(self, entity: Union[Shop, Connector, CorridorNode], floor_level: Optional[int] = None) -> str:
        if isinstance(entity, Shop):
            return f"{entity.name} @ Level {entity.floor.level}"
        elif isinstance(entity, Connector):
            if floor_level is None:
                raise ValueError("floor_level must be provided for Connector")
            return f"Connector:{entity.name} @ Level {floor_level}"
        elif isinstance(entity, CorridorNode):
            return f"CorridorNode:{entity.id} @ Level {entity.floor.level}"
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

    def get_entity_by_node_id(self, node_id: str) -> Optional[Union[Shop, Connector, CorridorNode]]:
        if "Connector:" in node_id:
            name, level = node_id.replace("Connector:", "").split(" @ Level ")
            level = int(level)
            floor = self.floors.get(level)
            if floor:
                return floor.connectors.get(name)
        elif "CorridorNode:" in node_id:
            id, level = node_id.replace("CorridorNode:", "").split(" @ Level ")
            level = int(level)
            floor = self.floors.get(level)
            if floor:
                return floor.corridor_nodes.get(id)
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
        # Add corridor nodes and their connections
        for floor in self.floors.values():
            floor_level = floor.level
            # Add corridor nodes to graph
            for node in floor.corridor_nodes.values():
                node_id = self.get_node_id(node)
                self.graph.setdefault(node_id, [])
                # Connect to other corridor nodes
                for connected_node in node.connections:
                    connected_node_id = self.get_node_id(connected_node)
                    weight = calculate_weight(node, connected_node)
                    self.graph[node_id].append((connected_node_id, weight))
            # Add shops and connect them to corridor nodes
            for shop in floor.shops.values():
                shop_node_id = self.get_node_id(shop)
                self.graph.setdefault(shop_node_id, [])
                # Connect to nearest corridor node
                nearest_node = self.find_nearest_corridor_node(shop, floor)
                if nearest_node:
                    corridor_node_id = self.get_node_id(nearest_node)
                    weight = calculate_weight(shop, nearest_node)
                    self.graph[shop_node_id].append((corridor_node_id, weight))
                    self.graph.setdefault(corridor_node_id, []).append((shop_node_id, weight))
            # Add connectors and connect them to corridor nodes
            for connector in floor.connectors.values():
                connector_node_id = self.get_node_id(connector, floor_level)
                self.graph.setdefault(connector_node_id, [])
                # Connect to nearest corridor node
                nearest_node = self.find_nearest_corridor_node(connector, floor)
                if nearest_node:
                    corridor_node_id = self.get_node_id(nearest_node)
                    weight = calculate_weight(connector, nearest_node)
                    self.graph[connector_node_id].append((corridor_node_id, weight))
                    self.graph.setdefault(corridor_node_id, []).append((connector_node_id, weight))
                # Connect connectors across floors
                for other_floor in connector.floors:
                    other_level = other_floor.level
                    if other_level != floor_level:
                        other_node_id = self.get_node_id(connector, other_level)
                        weight = connector.get_vertical_weight(floor_level, other_level)
                        if connector.is_accessible_between_floors(floor_level, other_level):
                            self.graph[connector_node_id].append((other_node_id, weight))
        # No need to add reverse edges since they are added in both directions

    def find_nearest_corridor_node(self, entity: Union[Shop, Connector], floor: Floor) -> Optional[CorridorNode]:
        min_distance = float('inf')
        nearest_node = None
        for node in floor.corridor_nodes.values():
            distance = calculate_weight(entity, node)
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        return nearest_node

    def __repr__(self):
        return f"Mall with Floors: {list(self.floors.keys())}"

def calculate_weight(entity1: Union[Shop, Connector, CorridorNode], entity2: Union[Shop, Connector, CorridorNode]) -> float:
    # Euclidean distance between two entities
    dx = entity1.x - entity2.x
    dy = entity1.y - entity2.y
    distance = math.hypot(dx, dy)
    return distance
