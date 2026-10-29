"""Préparation commune : un vrai serveur MCP en HTTP, comme celui de la banque (voir apps/mcp-tools/tests)."""

import asyncio
import socket
import threading
import time

import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from app.serveur import app


@pytest.fixture(scope="session")
def url_du_serveur():
    """Lance le vrai serveur MCP (uvicorn) sur un port libre, le temps des tests."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    serveur = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=serveur.run, daemon=True).start()
    while not serveur.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    serveur.should_exit = True


@pytest.fixture
def mcp(url_du_serveur):
    """Parle au serveur comme agent-api : client MCP officiel, sans en-tête de client (la FAQ est publique)."""

    def appeler(nom, arguments=None):
        async def faire():
            async with Client(streamable_http_client(url_du_serveur)) as c:
                return await c.call_tool(nom, arguments or {})

        return asyncio.run(faire())

    def lister():
        async def faire():
            async with Client(streamable_http_client(url_du_serveur)) as c:
                return (await c.list_tools()).tools

        return asyncio.run(faire())

    appeler.lister = lister
    return appeler
