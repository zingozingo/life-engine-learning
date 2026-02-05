import asyncio

from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

server = MCPServerStdio(
    "npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/Users/stevenromero/Development/Learning/life-engine-learning"],
)


async def main():
    agent = Agent("anthropic:claude-sonnet-4-5", mcp_servers=[server])

    async with agent.run_mcp_servers():
        result = await agent.run(
            "List all the files in this directory and tell me what each one does based on its name"
        )

    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
