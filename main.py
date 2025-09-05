# main_fixed.py
#!/usr/bin/env python3
"""
Main entry point for CrisisSim with fixed encoding.
"""

import argparse
import asyncio
import json
import sys
import io
import threading
import websockets

# Fix encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from env.world import CrisisModel, load_map_config
from reasoning.planner import make_plan

# WebSocket state push
_clients = set()
_ws_server = None

async def ws_handler(websocket):
    """Handle incoming WebSocket connections."""
    _clients.add(websocket)
    try:
        async for _ in websocket:  # keep connection alive
            pass
    finally:
        _clients.remove(websocket)

async def push_state(state_json: str):
    """Send state JSON to all connected clients."""
    if _clients:
        await asyncio.gather(
            *[client.send(state_json) for client in _clients],
            return_exceptions=True
        )

def start_ws_server():
    """Start the WebSocket server at ws://127.0.0.1:8000."""
    global _ws_server
    
    async def run_server():
        global _ws_server
        _ws_server = await websockets.serve(ws_handler, "127.0.0.1", 8000)
        print("WebSocket server running at ws://127.0.0.1:8000")
        print("Open index.html in a browser to view live simulation")
        await asyncio.Future()  # run forever

    # Run WebSocket server in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_server())

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    return thread

def run_episode(map_path, seed=42, ticks=300, provider="mock", strategy="react"):
    """Run a single simulation episode."""
    
    # Load map configuration
    if not map_path.endswith(".yaml"):
        map_path = f"configs/{map_path}.yaml"
    cfg = load_map_config(map_path)

    # Create model
    model = CrisisModel(
        width=cfg["width"],
        height=cfg["height"],
        rng_seed=seed,
        config=cfg,
        render=True
    )

    print(f"Starting CrisisSim with strategy={strategy}, provider={provider}, map={map_path}")
    print(f"Size: {cfg['width']}x{cfg['height']}")
    print(f"Survivors: {cfg.get('survivors', 'Unknown')}")
    print(f"Hospitals: {len(cfg.get('hospitals', []))}")
    print(f"Initial fires: {len(cfg.get('initial_fires', []))}")

    tick_count = 0

def next_id(self):
    if not hasattr(self, '_next_id'):
        self._next_id = 0
    self._next_id += 1
    return self._next_id
    
    # Create a separate event loop for state pushing
    push_loop = asyncio.new_event_loop()
    
    while model.running and tick_count < ticks:
        # Planning step
        ctx = model.summarize_state()
        try:
            # FIX: Remove the provider parameter from make_plan call
            plan = make_plan(ctx, strategy=strategy)
            model.set_plan(plan.get("commands", []))
        except Exception as e:
            print(f"Planning error: {e}")
            model.set_plan([])

        # Step simulation
        model.step()
        tick_count += 1

        # Push state to browser
        try:
            state_data = {
                "time": model.time,
                **model.summarize_state(),
                "metrics": {
                    "rescued": model.rescued,
                    "deaths": model.deaths,
                    "fires_extinguished": model.fires_extinguished,
                    "roads_cleared": model.roads_cleared,
                    "energy_used": model.energy_used
                }
            }
            payload = json.dumps(state_data)
            
            # Push state using the dedicated loop
            asyncio.set_event_loop(push_loop)
            push_loop.run_until_complete(push_state(payload))
            
        except Exception as e:
            print(f"Error pushing state: {e}")

        # Progress log
        if tick_count % 50 == 0:
            remaining = sum(1 for a in model.schedule.agents if a.__class__.__name__ == "Survivor")
            print(f"Tick {tick_count}: {model.rescued} rescued, {model.deaths} deaths, {remaining} survivors remaining")

        # Stop early if all survivors resolved
        if model.total_survivors and (model.rescued + model.deaths >= model.total_survivors):
            print("All survivors resolved!")
            break

    # Clean up the push loop
    push_loop.close()

    # Final results
    print(f"Simulation completed in {tick_count} ticks")
    print(f"Survivors rescued: {model.rescued}")
    print(f"Deaths: {model.deaths}")
    print(f"Fires extinguished: {model.fires_extinguished}")
    print(f"Roads cleared: {model.roads_cleared}")
    print(f"Energy used: {model.energy_used}")

    total_survivors = model.total_survivors or (model.rescued + model.deaths)
    success_rate = (model.rescued / total_survivors * 100) if total_survivors > 0 else 0.0
    print(f"Success rate: {success_rate:.1f}%")

    return {
        "rescued": model.rescued,
        "deaths": model.deaths,
        "avg_rescue_time": getattr(model, "avg_rescue_time", 0.0),
        "fires_extinguished": model.fires_extinguished,
        "roads_cleared": model.roads_cleared,
        "energy_used": model.energy_used,
        "tool_calls": model.tool_calls,
        "invalid_json": model.invalid_json,
        "replans": model.replans,
        "hospital_overflow_events": model.hospital_overflow_events,
        "ticks": tick_count,
        "total_survivors": total_survivors,
        "success_rate": success_rate,
    }

def main():
    parser = argparse.ArgumentParser(description="Run CrisisSim with WebSocket GUI")
    parser.add_argument("--map", default="map_small", help="Map config file (name or path)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--ticks", type=int, default=300, help="Max simulation ticks")
    parser.add_argument("--provider", default="mock", help="LLM provider (mock, groq, gemini)")
    parser.add_argument("--strategy", default="react", help="Planning strategy")
    args = parser.parse_args()

    # Start WebSocket server
    ws_thread = start_ws_server()
    
    # Give WebSocket server time to start
    import time
    time.sleep(1)

    results = run_episode(
        map_path=args.map,
        seed=args.seed,
        ticks=args.ticks,
        provider=args.provider,
        strategy=args.strategy,
    )

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()