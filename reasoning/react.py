# reasoning/react.py
import json
import os
from .llm_client import llm_complete
from .schema_validator import enforce_assignment_schema, create_schema_enforcement_prompt, create_fallback_plan

def make_react_plan(context, strategy: str = "react", scratchpad: str = ""):
    """
    Entry point used by planner.make_plan(...):
      returns dict with commands
    """
    return react_with_tools(context, scratchpad)

def react_with_tools(context: dict, scratchpad: str = "") -> dict:
    """
    LLM-based ReAct (Reasoning + Acting) planner.
    
    Uses the LLM API to generate plans based on the current crisis situation.
    The LLM reasons about the current state and generates appropriate commands
    for all agents following the required JSON schema.
    """
    
    # Build the prompt for the LLM
    system_prompt = """You are a crisis response coordinator. Your job is to analyze the current situation and generate commands for emergency response agents.

AVAILABLE ACTIONS:
- move: Move an agent to a specific position [x, y]
- pickup_survivor: Pick up a survivor (medics only)
- drop_at_hospital: Drop a survivor at a hospital (medics only)
- extinguish_fire: Extinguish a fire (trucks only)
- clear_rubble: Clear rubble (trucks only)
- recharge: Recharge battery at depot (drones only)
- resupply: Resupply water/tools at depot (trucks only)

AGENT TYPES:
- medic: Can pick up survivors and carry them to hospitals
- truck: Can extinguish fires and clear rubble
- drone: Can patrol and assist with coordination

CRITICAL PRIORITIES:
1. SURVIVORS WITH LOW DEADLINES (< 50 ticks) are TOP PRIORITY
2. Move medics DIRECTLY toward survivors in danger
3. Clear paths to survivors if blocked by rubble
4. Extinguish fires near survivors
5. Coordinate multiple agents for efficiency

MOVEMENT STRATEGY:
- Calculate shortest path to target
- Avoid obstacles (rubble, fires)
- Use grid coordinates [x, y] where 0 ≤ x < width, 0 ≤ y < height
- Move agents 1 step at a time toward their targets

OUTPUT FORMAT: You must output valid JSON with exactly this structure:
{
  "commands": [
    {"agent_id": "2", "type": "move", "to": [5, 7]},
    {"agent_id": "3", "type": "act", "action_name": "pickup_survivor"},
    {"agent_id": "4", "type": "act", "action_name": "drop_at_hospital"},
    {"agent_id": "1", "type": "act", "action_name": "extinguish_fire"},
    {"agent_id": "1", "type": "act", "action_name": "recharge"},
    {"agent_id": "5", "type": "act", "action_name": "clear_rubble"}
  ]
}

Valid action_name values: pickup_survivor, drop_at_hospital, extinguish_fire, clear_rubble, recharge, resupply

IMPORTANT: 
- Only output the JSON, no other text
- Ensure all agent_id values match actual agents in the context
- Use valid action names from the list above
- Coordinates must be within the grid bounds
- ALWAYS move medics toward survivors with low deadlines
- Think strategically about priorities: survivors in danger, fires spreading, blocked roads"""

    # Create the user prompt with current context
    user_prompt = f"""Current crisis situation:

Grid: {context.get('grid', {})}
Depot: {context.get('depot', [])}

Agents:
{format_agents(context.get('agents', []))}

Hospitals: {format_hospitals(context.get('hospitals', []))}
Fires: {format_fires(context.get('fires', []))}
Rubble: {format_rubble(context.get('rubble', []))}
Survivors: {format_survivors(context.get('survivors', []))}

Previous actions: {scratchpad if scratchpad else 'None'}

URGENT TASK: Generate a rescue plan for this tick.

ANALYSIS REQUIRED:
1. Identify survivors with lowest deadlines (most urgent)
2. Calculate which medics are closest to urgent survivors
3. Plan movement paths avoiding obstacles
4. Assign medics to specific survivors
5. Use trucks to clear rubble blocking paths
6. Use drones to assist with coordination

MOVEMENT PLAN:
- For each medic: calculate next step toward assigned survivor
- For each truck: move toward rubble blocking survivor access
- For each drone: move toward areas needing coordination

Output your plan as JSON with specific movement commands:"""

    # Add schema enforcement to prompt
    full_prompt = system_prompt + "\n\n" + create_schema_enforcement_prompt() + "\n\n" + user_prompt
    
    # Get LLM response
    try:
        response = llm_complete(full_prompt, temperature=0.1)
        
        # Use assignment schema validation
        plan, is_valid, error_msg = enforce_assignment_schema(response)
        
        if is_valid and plan:
            print(f"✅ Valid plan generated with {len(plan.get('commands', []))} commands")
            return plan
        else:
            print(f"❌ Invalid JSON schema: {error_msg}")
            # Try one retry with schema reminder
            retry_prompt = full_prompt + f"\n\nPREVIOUS RESPONSE WAS INVALID: {error_msg}\n\nPlease output ONLY valid JSON matching the exact schema above."
            
            retry_response = llm_complete(retry_prompt, temperature=0.1)
            retry_plan, retry_valid, retry_error = enforce_assignment_schema(retry_response)
            
            if retry_valid and retry_plan:
                print(f"✅ Valid plan generated on retry with {len(retry_plan.get('commands', []))} commands")
                return retry_plan
            else:
                print(f"❌ Retry failed: {retry_error}, using fallback")
                return create_fallback_plan()
            
    except Exception as e:
        print(f"Error in ReAct planning: {e}")
        return create_fallback_plan()

def format_agents(agents):
    """Format agents list for the prompt"""
    if not agents:
        return "None"
    
    formatted = []
    for agent in agents:
        agent_str = f"- {agent['kind']} (ID: {agent['id']}) at {agent['pos']}"
        if agent.get('battery') is not None:
            agent_str += f", battery: {agent['battery']}"
        if agent.get('water') is not None:
            agent_str += f", water: {agent['water']}"
        if agent.get('tools') is not None:
            agent_str += f", tools: {agent['tools']}"
        if agent.get('carrying'):
            agent_str += ", carrying survivor"
        formatted.append(agent_str)
    
    return "\n".join(formatted)

def format_survivors(survivors):
    """Format survivors list for the prompt with urgency indicators"""
    if not survivors:
        return "None"
    
    # Sort survivors by deadline (most urgent first)
    sorted_survivors = sorted(survivors, key=lambda s: s.get('deadline', 999))
    
    formatted = []
    for survivor in sorted_survivors:
        deadline = survivor.get('deadline', 'unknown')
        urgency = "🚨 URGENT" if deadline < 50 else "⚠️ WARNING" if deadline < 100 else "✅ SAFE"
        formatted.append(f"- Survivor {survivor['id']} at {survivor['pos']}, deadline: {deadline} ({urgency})")
    
    return "\n".join(formatted)

def format_hospitals(hospitals):
    """Format hospitals list for the prompt - handles any data structure"""
    if not hospitals:
        return "None"
    
    formatted = []
    for hospital in hospitals:
        pos = hospital.get('pos', 'unknown')
        
        # Safely get all values with fallbacks
        capacity = hospital.get('capacity', 'unknown')
        
        # Handle patients count
        patients_data = hospital.get('patients', 0)
        if hasattr(patients_data, '__len__') and not isinstance(patients_data, (str, int, float)):
            patients_count = len(patients_data)
        else:
            try:
                patients_count = int(patients_data)
            except (ValueError, TypeError):
                patients_count = 0
        
        # Handle queue count
        queue_data = hospital.get('queue', 0)
        if hasattr(queue_data, '__len__') and not isinstance(queue_data, (str, int, float)):
            queue_count = len(queue_data)
        else:
            try:
                queue_count = int(queue_data)
            except (ValueError, TypeError):
                queue_count = 0
        
        formatted.append(f"- Hospital at {pos}, capacity: {capacity}, patients: {patients_count}, queue: {queue_count}")
    
    return "\n".join(formatted)

def format_fires(fires):
    """Format fires list for the prompt"""
    if not fires:
        return "None"
    
    formatted = []
    for fire in fires:
        formatted.append(f"- Fire at {fire}")
    
    return "\n".join(formatted)

def format_rubble(rubble):
    """Format rubble list for the prompt"""
    if not rubble:
        return "None"
    
    formatted = []
    for rub in rubble:
        formatted.append(f"- Rubble at {rub}")
    
    return "\n".join(formatted)