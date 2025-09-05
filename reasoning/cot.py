# reasoning/cot.py
import json
from .llm_client import llm_complete
from .schema_validator import enforce_assignment_schema, create_schema_enforcement_prompt, create_fallback_plan

def make_cot_plan(context, strategy: str = "cot", scratchpad: str = ""):
    """
    Entry point used by planner.make_plan(...):
      returns dict with commands
    """
    return chain_of_thought_planning(context, scratchpad)

def chain_of_thought_planning(context: dict, scratchpad: str = "") -> dict:
    """
    Chain-of-Thought reasoning framework for crisis response.
    
    This approach breaks down the planning into explicit reasoning steps:
    1. Observe the current situation
    2. Think through the problem step by step
    3. Reason about priorities and constraints
    4. Plan specific actions
    5. Execute the plan
    """
    
    system_prompt = """You are a crisis response coordinator using Chain-of-Thought reasoning. 

Your task is to think through the crisis situation step by step and generate a response plan.

Use this EXPLICIT REASONING PROCESS:

STEP 1 - OBSERVE: What is the current state of the crisis?
STEP 2 - ANALYZE: What are the immediate threats and priorities?
STEP 3 - REASON: What constraints and resources do we have?
STEP 4 - PLAN: What specific actions should each agent take?
STEP 5 - EXECUTE: Convert the plan to JSON commands

AVAILABLE ACTIONS:
- move: Move an agent to a specific position [x, y]
- pickup_survivor: Pick up a survivor (medics only)
- drop_at_hospital: Drop a survivor at a hospital (medics only)
- extinguish_fire: Extinguish a fire (trucks only)
- clear_rubble: Clear rubble (trucks only)
- recharge: Recharge battery at depot (drones only)
- resupply: Resupply water/tools at depot (trucks only)

REASONING STRUCTURE:
First, work through each step explicitly with your reasoning.
Then end with the JSON output:

{
  "commands": [
    {"agent_id": "2", "type": "move", "to": [5, 7]},
    {"agent_id": "3", "type": "act", "action_name": "pickup_survivor"},
    {"agent_id": "4", "type": "act", "action_name": "drop_at_hospital"},
    {"agent_id": "1", "type": "act", "action_name": "extinguish_fire"}
  ]
}

Valid action_name values: pickup_survivor, drop_at_hospital, extinguish_fire, clear_rubble, recharge, resupply

IMPORTANT: 
- Show your step-by-step thinking before the JSON
- Ensure all agent_id values match actual agents in the context
- Use valid action names from the list above
- Coordinates must be within the grid bounds
- End with ONLY the JSON, no text after it"""

    user_prompt = f"""Current crisis situation:

Grid: {context.get('grid', {})}
Depot: {context.get('depot', [])}

Agents:
{format_agents(context.get('agents', []))}

Hospitals: {context.get('hospitals', [])}
Fires: {context.get('fires', [])}
Rubble: {context.get('rubble', [])}
Survivors: {format_survivors(context.get('survivors', []))}

Previous actions: {scratchpad if scratchpad else 'None'}

Now work through the Chain-of-Thought process:

STEP 1 - OBSERVE: What do I see in this crisis situation?
STEP 2 - ANALYZE: What are the most urgent priorities?
STEP 3 - REASON: What are my constraints and available resources?
STEP 4 - PLAN: What should each agent do this turn?
STEP 5 - EXECUTE: Convert to JSON commands"""

    # Add schema enforcement to prompt
    schema_prompt = create_schema_enforcement_prompt()
    full_prompt = system_prompt + "\n\n" + schema_prompt + "\n\n" + user_prompt
    
    try:
        response = llm_complete(full_prompt, temperature=0.1)
        
        # Use assignment schema validation
        plan, is_valid, error_msg = enforce_assignment_schema(response)
        
        if is_valid and plan:
            print(f"✅ CoT: Valid plan generated with {len(plan.get('commands', []))} commands")
            return plan
        else:
            print(f"❌ CoT: Invalid JSON schema: {error_msg}")
            # CoT often produces verbose output, try extracting just the JSON part
            json_start = response.rfind('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_only = response[json_start:json_end]
                retry_plan, retry_valid, retry_error = enforce_assignment_schema(json_only)
                
                if retry_valid and retry_plan:
                    print(f"✅ CoT: Valid plan extracted from verbose response with {len(retry_plan.get('commands', []))} commands")
                    return retry_plan
            
            print(f"❌ CoT: Could not extract valid JSON, using fallback")
            return create_fallback_plan()
            
    except Exception as e:
        print(f"Error in Chain-of-Thought planning: {e}")
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
        urgency = "🚨 CRITICAL" if deadline < 30 else "⚠️ URGENT" if deadline < 100 else "✅ STABLE"
        formatted.append(f"- Survivor {survivor['id']} at {survivor['pos']}, deadline: {deadline} ({urgency})")
    
    return "\n".join(formatted)
