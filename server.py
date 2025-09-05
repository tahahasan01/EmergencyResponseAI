# server.py
#!/usr/bin/env python3
"""
WebSocket server for CrisisSim GUI visualization.
"""

import asyncio
import websockets
import json
from pathlib import Path

# Store connected clients
_clients = set()

async def handler(websocket):
    """Handle WebSocket connections."""
    _clients.add(websocket)
    try:
        async for message in websocket:
            # Handle incoming messages if needed
            pass
    finally:
        _clients.remove(websocket)

async def push_state(state_data):
    """Push state to all connected clients."""
    if _clients:
        message = json.dumps(state_data)
        await asyncio.gather(
            *[client.send(message) for client in _clients],
            return_exceptions=True
        )

async def main():
    """Start WebSocket server."""
    async with websockets.serve(handler, "localhost", 8000):
        print("🌐 WebSocket server running at ws://localhost:8000")
        print("📊 Open index.html in a browser to view the simulation")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())