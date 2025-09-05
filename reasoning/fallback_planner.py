"""
Fallback planner for testing when LLM is not available.
"""

import json
import random

def make_fallback_plan(context: dict) -> dict:
    """
    Create a simple fallback plan for testing.
    This moves agents toward survivors in a simple way.
    """
    commands = []
    
    agents = context.get('agents', [])
    survivors = context.get('survivors', [])
    
    if not survivors or not agents:
        return {"commands": []}
    
    # For each agent, move toward the closest survivor
    for agent in agents:
        agent_id = agent['id']
        agent_pos = agent['pos']
        agent_kind = agent['kind']
        
        # Find closest survivor
        closest_survivor = None
        min_distance = float('inf')
        
        for survivor in survivors:
            survivor_pos = survivor['pos']
            distance = abs(agent_pos[0] - survivor_pos[0]) + abs(agent_pos[1] - survivor_pos[1])
            
            if distance < min_distance:
                min_distance = distance
                closest_survivor = survivor
        
        if closest_survivor:
            target_pos = closest_survivor['pos']
            
            # Calculate next step toward target
            dx = target_pos[0] - agent_pos[0]
            dy = target_pos[1] - agent_pos[1]
            
            # Move in the direction with largest difference
            if abs(dx) > abs(dy):
                new_x = agent_pos[0] + (1 if dx > 0 else -1)
                new_y = agent_pos[1]
            else:
                new_x = agent_pos[0]
                new_y = agent_pos[1] + (1 if dy > 0 else -1)
            
            # Ensure within bounds
            grid = context.get('grid', {})
            width = grid.get('width', 20)
            height = grid.get('height', 20)
            
            new_x = max(0, min(new_x, width - 1))
            new_y = max(0, min(new_y, height - 1))
            
            commands.append({
                "agent_id": agent_id,
                "type": "move",
                "to": [new_x, new_y]
            })
    
    return {"commands": commands}
