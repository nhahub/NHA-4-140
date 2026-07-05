import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioClientTransport, stdio_client
    from mcp.client.sse import sse_client
except ImportError:
    ClientSession = None
    StdioClientTransport = None
    stdio_client = None
    sse_client = None


class _InProcessServer:
    """Wraps an in-process MCP server so it exposes a call_tool interface
    without stdio subprocess overhead."""

    def __init__(self, name: str, call_tool_fn, tools: list[dict]):
        self.name = name
        self._call_tool_fn = call_tool_fn
        self.tool_map: dict[str, dict] = {}
        for t in tools:
            self.tool_map[t["name"]] = t

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        result = await self._call_tool_fn(tool_name, arguments)
        if result and len(result) > 0:
            first = result[0]
            # Handle both MCP SDK TextContent objects and plain dicts
            text = first.text if hasattr(first, "text") else first.get("text", str(first))
            try:
                return json.loads(text) if isinstance(text, str) else text
            except (json.JSONDecodeError, TypeError):
                return text
        return None


class MCPToolRegistry:
    """Registry of MCP servers and their tools.

    Acts as the single interface for all graph nodes to call external tools.
    Supports three transport modes:
    - in-process: server runs in same process (no overhead)
    - stdio: server runs as subprocess
    - SSE: remote server via HTTP
    """

    def __init__(self):
        self._in_process: dict[str, _InProcessServer] = {}
        self._sessions: dict[str, ClientSession] = {}
        self._tool_map: dict[str, tuple[str, dict]] = {}

    def register_in_process(self, name: str, call_tool_fn, tools_metadata: list[dict]) -> None:
        """Register an in-process MCP server (no stdio/SSE overhead).

        Args:
            name: Server name identifier.
            call_tool_fn: Async callable(name, arguments) -> list of response items.
            tools_metadata: List of dicts with 'name', 'inputSchema', 'description'.
        """
        bridge = _InProcessServer(name, call_tool_fn, tools_metadata)
        self._in_process[name] = bridge
        for t in tools_metadata:
            self._tool_map[t["name"]] = (name, t.get("inputSchema", {}))
        logger.info("MCP in-process server '%s' registered with %d tools", name, len(tools_metadata))

    async def register_stdio(self, name: str, command: str, args: list[str] | None = None) -> None:
        if StdioClientTransport is None:
            logger.warning("MCP SDK not installed, skipping stdio server '%s'", name)
            return
        try:
            transport = StdioClientTransport(command=command, args=args or [])
            read, write = await stdio_client(transport)
            session = ClientSession(read, write)
            await session.initialize()
            tools_result = await session.list_tools()
            self._sessions[name] = session
            for tool in tools_result.tools:
                self._tool_map[tool.name] = (name, tool.inputSchema or {})
            logger.info("MCP stdio server '%s' registered with %d tools", name, len(tools_result.tools))
        except Exception as e:
            logger.warning("Failed to register MCP stdio server '%s': %s", name, e)

    async def register_sse(self, name: str, url: str) -> None:
        if sse_client is None:
            logger.warning("MCP SDK not installed, skipping SSE server '%s'", name)
            return
        try:
            read, write = await sse_client(url)
            session = ClientSession(read, write)
            await session.initialize()
            tools_result = await session.list_tools()
            self._sessions[name] = session
            for tool in tools_result.tools:
                self._tool_map[tool.name] = (name, tool.inputSchema or {})
            logger.info("MCP SSE server '%s' registered with %d tools", name, len(tools_result.tools))
        except Exception as e:
            logger.warning("Failed to register MCP SSE server '%s': %s", name, e)

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool by name across any registered server."""
        entry = self._tool_map.get(tool_name)
        if entry is None:
            available = self.get_available_tools()
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")
        server_name, _ = entry

        # In-process first
        in_proc = self._in_process.get(server_name)
        if in_proc is not None:
            return await in_proc.call_tool(tool_name, arguments)

        # Remote session
        session = self._sessions.get(server_name)
        if session is None:
            raise RuntimeError(f"MCP server '{server_name}' for tool '{tool_name}' is not connected")
        try:
            result = await session.call_tool(tool_name, arguments)
            if result.content and len(result.content) > 0:
                text = result.content[0].text
                if isinstance(text, str):
                    try:
                        return json.loads(text)
                    except (json.JSONDecodeError, TypeError):
                        return text
                return text
            return None
        except Exception as e:
            logger.error("MCP tool '%s' call failed: %s", tool_name, e)
            raise

    def get_available_tools(self) -> list[str]:
        return list(self._tool_map.keys())

    def get_tool_schema(self, tool_name: str) -> dict | None:
        entry = self._tool_map.get(tool_name)
        return entry[1] if entry else None

    async def cleanup(self) -> None:
        for name, session in self._sessions.items():
            try:
                await session.close()
            except Exception:
                pass
        self._sessions.clear()
        self._tool_map.clear()
        self._in_process.clear()
        logger.info("MCP registry cleaned up")
