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
    "2": "Level 2: Selective Loading - Skills loaded on demand via load_skill",
    "3": "Level 3: Explicit Routing - Query classification drives selection",
    "4": "Level 4: Adaptive Context - Proactive fetching and context engineering",
}


def show_menu():
    """Display the engine selection menu."""
    print("\nTravel Concierge - Life Engine Learning")
    print("=" * 50)
    print("\nAvailable engines:")
    for key, desc in LEVELS.items():
        print(f"  {key} -> {desc}")
    print("\nUsage: uv run python main.py <level>")


async def run_level_1():
    """Run the Level 1 Monolith engine."""
    from engines.level1_monolith import Level1Monolith

    print("\nTravel Concierge - Level 1: Monolith")
    print("=" * 50)
    print("All skills loaded in one giant prompt.")
    print("Type 'quit' to exit, 'prompt' to see the system prompt.\n")

    engine = Level1Monolith()
    message_history = []

    # Start a conversation that groups all queries in this chat session
    conversation_id = engine.logger.start_conversation()
    engine.set_conversation_id(conversation_id)

    # Show prompt size for demonstration
    prompt_len = len(engine.get_system_prompt())
    print(f"System prompt: {prompt_len:,} characters (~{prompt_len // 4:,} tokens)")
    print(f"Skills loaded: {', '.join(sorted(engine.skills.keys()))}\n")

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
            print(f"\nError: {e}\n")


async def run_level_2():
    """Run the Level 2 Skills engine."""
    from engines.level2_skills import Level2SkillsEngine

    print("\nTravel Concierge - Level 2: Skills + Progressive Disclosure")
    print("=" * 50)
    print("LLM sees skill summaries, loads details on demand.")
    print("Type 'quit' to exit, 'prompt' to see the system prompt.\n")

    engine = Level2SkillsEngine()
    message_history = []

    # Start a conversation that groups all queries in this chat session
    conversation_id = engine.logger.start_conversation()
    engine.set_conversation_id(conversation_id)

    # Show prompt size for demonstration
    prompt_len = len(engine.get_system_prompt())
    print(f"System prompt: {prompt_len:,} characters (~{prompt_len // 4:,} tokens)")
    print(f"Skills available: {', '.join(sorted(engine.skills.keys()))}\n")

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
            print(f"\nError: {e}\n")


def main():
    if len(sys.argv) < 2:
        show_menu()
        return

    level = sys.argv[1]
    if level not in LEVELS:
        print(f"Unknown level: {level}. Choose 1-4.")
        return

    if level == "1":
        asyncio.run(run_level_1())
    elif level == "2":
        asyncio.run(run_level_2())
    else:
        print(f"\n{LEVELS[level]}")
        print("Not yet implemented. Coming soon!")


if __name__ == "__main__":
    main()
