import asyncio
from pathlib import Path

from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from skill_loader import discover_skills, load_skill_instructions, build_skills_prompt

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

SKILLS_DIR = Path("skills")

skills = discover_skills(SKILLS_DIR)
skills_prompt = build_skills_prompt(skills)

mcp_server = MCPServerStdio(
    "npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/Users/stevenromero/Development/Learning/life-engine-learning"],
)

agent = Agent(
    "anthropic:claude-sonnet-4-5",
    system_prompt=skills_prompt,
)


@agent.tool_plain
def load_skill(skill_name: str) -> str:
    """Load detailed instructions for a skill by name."""
    return load_skill_instructions(skill_name, SKILLS_DIR)


@agent.tool_plain
async def call_mcp_tool(server: str, tool_name: str, arguments: dict) -> str:
    """Call a tool on an MCP server."""
    async with mcp_server:
        result = await mcp_server.call_tool(tool_name, arguments)
    return str(result)


async def main():
    result = await agent.run("List all files in this directory")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
