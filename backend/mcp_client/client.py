import asyncio
import json
import threading

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


class KaprukaMCPClient:
    def __init__(self, server_url: str):
        self._server_url = server_url
        self._session: ClientSession | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()
        self._running = True
        print(f"[MCP_CLIENT] Initialised with URL: {server_url}")

    def start(self):
        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._connect_and_serve())
            except Exception as e:
                print(f"[MCP_CLIENT] Connection failed: {e}")
                self._ready.set()

        t = threading.Thread(target=run, daemon=True, name="mcp-client")
        t.start()
        # Don't block — server can start while MCP connects in background
        print("[MCP_CLIENT] Starting background connection...")

    async def _connect_and_serve(self):
        async with streamablehttp_client(self._server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                while self._running:
                    await asyncio.sleep(1)

    def stop(self):
        self._running = False

    def call_tool(self, name: str, arguments: dict | None = None) -> str:
        if not self._session or not self._loop:
            raise RuntimeError("MCP client not connected")
        print(f"[MCP_CLIENT] call_tool({name}) args: {json.dumps(arguments)[:200]}")
        future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(name, arguments={"params": arguments} if arguments else {}),
            self._loop,
        )
        result = future.result()
        text = result.content[0].text if result.content else ""
        print(f"[MCP_CLIENT] Response ({len(text)} chars): {text[:150]}...")
        return text
