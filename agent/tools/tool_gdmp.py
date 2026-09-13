from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

_mcp_tools = None
async def get_amap_mcp_tools():
    global _mcp_tools
    if _mcp_tools is None:
        client = MultiServerMCPClient(
            {
                "amap-maps": {
                    "transport" :"streamable-http",
                    "url": "https://mcp.amap.com/mcp?key=204559b07a590786348b11ac11247c17"
                }
            }
        )
        _mcp_tools = await client.get_tools()
        print(f">>>> MCP工具初始化成功，可用工具：{len(_mcp_tools)}个")

    return _mcp_tools