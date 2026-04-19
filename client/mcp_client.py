import asyncio
import sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

_LOG_PATH = Path("logs/mcp_server.log")

class MCPClient:
    def __init__(self, server_script: str) -> None:
        self._params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
        )
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._errlog = _LOG_PATH.open("a", encoding="utf-8")

    def get_ollama_tools(self) -> list[dict]:
        async def _fetch():
            async with stdio_client(self._params, errlog=self._errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return [
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.inputSchema,
                            },
                        }
                        for tool in result.tools
                    ]

        return asyncio.run(_fetch())

    def call_tool(self, name: str, arguments: dict) -> str:
        async def _call():
            async with stdio_client(self._params, errlog=self._errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name, arguments)
                    return "\n".join(
                        block.text
                        for block in result.content
                        if hasattr(block, "text")
                    )

        return asyncio.run(_call())
