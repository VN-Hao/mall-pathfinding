import argparse
from data_loader import load_mall_from_json
from pathfinding import find_shortest_path, generate_instructions
from visualization import visualize_mall

def main():
    parser = argparse.ArgumentParser(description="Mall Navigation")
    parser.add_argument("start_shop", help="Name of the starting shop")
    parser.add_argument("end_shop", help="Name of the destination shop")
    parser.add_argument("--accessible", action="store_true", help="Require accessible routes")
    args = parser.parse_args()

    mall = load_mall_from_json('mall_data.json')

    # Find the shortest path
    path = find_shortest_path(
        mall,
        args.start_shop,
        args.end_shop,
        accessibility_required=args.accessible
    )

    # Output the result
    if isinstance(path, list):
        print(f"Shortest path from {args.start_shop} to {args.end_shop}:")
        for step in path:
            print(" ->", step)
        instructions = generate_instructions(mall, path)
        print("\nTurn-by-turn Instructions:")
        for instruction in instructions:
            print(instruction)
        visualize_mall(mall, path)
    else:
        print(path)

if __name__ == "__main__":
    main()
