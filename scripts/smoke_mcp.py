"""Real stdio handshake and tool call; no internet/model use."""
import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "root_paper_lab.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = [t.name for t in result.tools]
            assert len(names) == 7, names
            assert "collect_top_venue_papers" in names, names
            gate = await session.call_tool("analyze_root_paper", {
                "track": "ai", "pdf_manifest": "not-read", "question": "test", "llm": "unset", "embedding": "unset"})
            assert not gate.isError
            assert "needs_authorization" in str(gate.content)
            print(json.dumps({"handshake": "passed", "tools": names, "cost_gate": "passed"}))


asyncio.run(main())
