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
        # Get the tools list to find our tool
        tools = await mcp_server.list_tools()
        # Find the matching tool
        for tool in tools:
            if tool.name == tool_name:
                # Use the low-level client session to call the tool
                result = await mcp_server._client.call_tool(tool_name, arguments)
                # Extract text content from result
                if result.content:
                    return '\n'.join(
                        item.text for item in result.content
                        if hasattr(item, 'text')
                    )
                return str(result)
        return f'Tool {tool_name} not found'


async def main():
    result = await agent.run("List all files in this directory")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
