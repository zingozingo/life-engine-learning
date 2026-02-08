"""Life Engine Learning - Travel Concierge

A multi-level agent architecture learning project.
Run with: uv run python main.py [level]
"""

import asyncio
import sys

import logfire
from dotenv import load_dotenv

load_dotenv()

# Configure Logfire before any agent creation
logfire.configure()
logfire.instrument_pydantic_ai()

LEVELS = {
    "1": "Level 1: Monolith - Everything hardcoded in one prompt",
    "2": "Level 2: Skills + Generic Tools - Progressive disclosure",
    "3": "Level 3: Query Classification - Explicit routing",
    "4": "Level 4: Adaptive Routing - Proactive/reactive fetching",
    "5": "Level 5: MCP Tool Servers - Distributed tool infrastructure",
}


def show_menu():
    """Display the engine selection menu."""
    print("\n🧳 Travel Concierge - Life Engine Learning")
    print("=" * 50)
    print("\nAvailable engines:")
    for key, desc in LEVELS.items():
        print(f"  {key} → {desc}")
    print("\nUsage: uv run python main.py <level>")


async def run_level_1():
    """Run the Level 1 Monolith engine."""
    from engines.level1_monolith import Level1Monolith

    print("\n🧳 Travel Concierge - Level 1: Monolith")
    print("=" * 50)
    print("All skills loaded in one giant prompt.")
    print("Type 'quit' to exit, 'prompt' to see the system prompt.\n")

    engine = Level1Monolith()
    message_history = []

    # Show prompt size for demonstration
    prompt_len = len(engine.get_system_prompt())
    print(f"📊 System prompt: {prompt_len:,} characters (~{prompt_len // 4:,} tokens)")
    print(f"📚 Skills loaded: {', '.join(sorted(engine.skills.keys()))}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "prompt":
            print("\n" + "=" * 50)
            print("SYSTEM PROMPT:")
            print("=" * 50)
            print(engine.get_system_prompt())
            print("=" * 50 + "\n")
            continue

        # Run the engine
        try:
            response, message_history = await engine.run(user_input, message_history)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    if len(sys.argv) < 2:
        show_menu()
        return

    level = sys.argv[1]
    if level not in LEVELS:
        print(f"Unknown level: {level}. Choose 1-5.")
        return

    if level == "1":
        asyncio.run(run_level_1())
    else:
        print(f"\n{LEVELS[level]}")
        print("🚧 Not yet implemented. Coming soon!")


if __name__ == "__main__":
    main()
