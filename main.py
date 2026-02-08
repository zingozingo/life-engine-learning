"""Life Engine Learning - Travel Concierge

A multi-level agent architecture learning project.
Run with: uv run python main.py [level]
"""
import sys

LEVELS = {
    "1": "Level 1: Monolith - Everything hardcoded in one prompt",
    "2": "Level 2: Skills + Generic Tools - Progressive disclosure",
    "3": "Level 3: Query Classification - Explicit routing",
    "4": "Level 4: Adaptive Routing - Proactive/reactive fetching",
    "5": "Level 5: MCP Tool Servers - Distributed tool infrastructure",
}


def main():
    print("\n🧳 Travel Concierge - Life Engine Learning")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nAvailable engines:")
        for key, desc in LEVELS.items():
            print(f"  {key} → {desc}")
        print("\nUsage: uv run python main.py <level>")
        return

    level = sys.argv[1]
    if level not in LEVELS:
        print(f"Unknown level: {level}. Choose 1-5.")
        return

    print(f"\n{LEVELS[level]}")
    print("🚧 Not yet implemented. Coming soon!")


if __name__ == "__main__":
    main()
