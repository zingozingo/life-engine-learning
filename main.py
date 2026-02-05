from datetime import datetime
from pathlib import Path

import httpx
import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent

from skill_loader import build_skills_prompt, discover_skills, load_skill_instructions

load_dotenv()

logfire.configure()  # Initialize Logfire
logfire.instrument_pydantic_ai()  # Auto-trace all Pydantic AI calls

SKILLS_DIR = Path("skills")
skills = discover_skills(SKILLS_DIR)
skills_prompt = build_skills_prompt(skills)

agent = Agent(
    "anthropic:claude-sonnet-4-5",
    instructions=f"""You are a helpful assistant with access to skills.

{skills_prompt}

When a user asks something that matches a skill, FIRST load that skill to get detailed instructions before responding.""",
)


@agent.tool_plain
def load_skill(skill_name: str) -> str:
    """Load detailed instructions for a skill. Call this before using any skill."""
    return load_skill_instructions(skill_name, SKILLS_DIR)


def read_skill_file(skill_name: str, file_path: str) -> str:
    """Read a specific file from a skill's directory."""
    full_path = SKILLS_DIR / skill_name / file_path
    if not full_path.exists():
        return f"File '{file_path}' not found in skill '{skill_name}'."
    return full_path.read_text()


@agent.tool_plain
def read_skill_resource(skill_name: str, file_path: str) -> str:
    """Read a reference file or resource from a skill. Use this when skill instructions mention additional resources."""
    return read_skill_file(skill_name, file_path)


@agent.tool_plain
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@agent.tool_plain
def http_request(method: str, url: str, params: dict | None = None) -> str:
    """
    Make an HTTP request to any URL.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: The full URL to request
        params: Optional query parameters as a dictionary

    Returns:
        The response body as text, or error message if failed.
    """
    try:
        response = httpx.request(method, url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        return f"HTTP Error: {str(e)}"


print("Chatbot ready! Type 'quit' to exit.\n")
print(f"Loaded {len(skills)} skills: {[s.name for s in skills]}\n")

conversation_history = []

while True:
    user_message = input("You: ")

    if user_message == "quit":
        print("Goodbye!")
        break

    result = agent.run_sync(user_message, message_history=conversation_history)
    conversation_history = result.all_messages()
    print(f"Assistant: {result.output}\n")
