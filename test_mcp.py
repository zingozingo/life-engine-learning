import asyncio

from dotenv import load_dotenv
import logfire
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

server = MCPServerStdio("uv", args=["run", "mcp_math_server.py"])


async def main():
    agent = Agent("anthropic:claude-sonnet-4-5", mcp_servers=[server])

    async with agent.run_mcp_servers():
        result = await agent.run("What is 7 plus 5?")

    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
