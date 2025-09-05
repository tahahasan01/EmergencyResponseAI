# reasoning/plan_execute.py
import json
from .llm_client import llm_complete
from .schema_validator import enforce_assignment_schema, create_schema_enforcement_prompt, create_fallback_plan

def make_plan_execute_plan(context, strategy: str = "plan_execute", scratchpad: str = ""):
    """
    Entry point used by planner.make_plan(...):
      returns dict with commands
    """
    return plan_and_execute(context, scratchpad)

def plan_and_execute(context: dict, scratchpad: str = "") -> dict:
    """
    Plan-and-Execute reasoning framework for crisis response.
    
    This approach separates the planning into two phases:
    1. HIGH-LEVEL PLANNING: Analyze situation and create strategic plan
    2. EXECUTION PLANNING: Convert strategic plan into specific agent commands
    """
    
    # Phase 1: High-level strategic planning
    strategy_prompt = """You are a crisis response strategist. Your job is to create a high-level strategic plan.

ANALYZE the current crisis situation and create a strategic plan with these components:

1. IMMEDIATE THREATS: What are the most urgent dangers?
2. RESOURCE ALLOCATION: How should agents be assigned to tasks?
3. PRIORITY SEQUENCE: What should be addressed first, second, third?
4. COORDINATION STRATEGY: How can agents work together efficiently?

Output your strategic plan as a clear, structured response (not JSON)."""

    strategy_context = f"""Current crisis situation:

Grid: {context.get('grid', {})}
Depot: {context.get('depot', [])}

Agents:
{format_agents(context.get('agents', []))}

Hospitals: {context.get('hospitals', [])}
Fires: {context.get('fires', [])}
Rubble: {context.get('rubble', [])}
Survivors: {format_survivors(context.get('survivors', []))}

Previous actions: {scratchpad if scratchpad else 'None'}

Create your strategic plan:"""

    try:
        strategy_response = llm_complete(strategy_prompt + "\n\n" + strategy_context, temperature=0.1)
    except Exception as e:
        print(f"Error in strategy planning: {e}")
        strategy_response = "Focus on immediate threats and coordinate agent actions."

    # Phase 2: Convert strategy to specific commands
    execution_prompt = """You are a crisis response executor. Convert the strategic plan into specific agent commands.

STRATEGIC PLAN:
{strategy}

AVAILABLE ACTIONS:
- move: Move an agent to a specific position [x, y]
- pickup_survivor: Pick up a survivor (medics only)
- drop_at_hospital: Drop a survivor at a hospital (medics only)
- extinguish_fire: Extinguish a fire (trucks only)
- clear_rubble: Clear rubble (trucks only)
- recharge: Recharge battery at depot (drones only)
- resupply: Resupply water/tools at depot (trucks only)

CURRENT SITUATION:
{current_context}

OUTPUT FORMAT: You must output valid JSON with exactly this structure:
{{
  "commands": [
    {{"agent_id": "2", "type": "move", "to": [5, 7]}},
    {{"agent_id": "3", "type": "act", "action_name": "pickup_survivor"}},
    {{"agent_id": "4", "type": "act", "action_name": "drop_at_hospital"}},
    {{"agent_id": "1", "type": "act", "action_name": "extinguish_fire"}},
    {{"agent_id": "5", "type": "act", "action_name": "clear_rubble"}}
  ]
}}

Valid action_name values: pickup_survivor, drop_at_hospital, extinguish_fire, clear_rubble, recharge, resupply

IMPORTANT: 
- Only output the JSON, no other text
- Ensure all agent_id values match actual agents in the context
- Use valid action names from the list above
- Coordinates must be within the grid bounds
- Execute the strategic plan with specific, actionable commands"""

    execution_context = f"""Grid: {context.get('grid', {})}
Depot: {context.get('depot', [])}

Agents:
{format_agents(context.get('agents', []))}

Hospitals: {context.get('hospitals', [])}
Fires: {context.get('fires', [])}
Rubble: {context.get('rubble', [])}
Survivors: {format_survivors(context.get('survivors', []))}

Previous actions: {scratchpad if scratchpad else 'None'}

Now execute the strategic plan with specific commands:"""

    # Add schema enforcement to execution prompt
    full_execution_prompt = execution_prompt.format(
        strategy=strategy_response,
        current_context=execution_context
    ) + "\n\n" + create_schema_enforcement_prompt()
    
    try:
        execution_response = llm_complete(full_execution_prompt, temperature=0.1)
        
        # Use assignment schema validation
        plan, is_valid, error_msg = enforce_assignment_schema(execution_response)
        
        if is_valid and plan:
            print(f"✅ Plan-Execute: Valid plan generated with {len(plan.get('commands', []))} commands")
            return plan
        else:
            print(f"❌ Plan-Execute: Invalid JSON schema: {error_msg}")
            # Try one retry with schema reminder
            retry_prompt = full_execution_prompt + f"\n\nPREVIOUS RESPONSE WAS INVALID: {error_msg}\n\nPlease output ONLY valid JSON matching the exact schema above."
            
            retry_response = llm_complete(retry_prompt, temperature=0.1)
            retry_plan, retry_valid, retry_error = enforce_assignment_schema(retry_response)
            
            if retry_valid and retry_plan:
                print(f"✅ Plan-Execute: Valid plan generated on retry with {len(retry_plan.get('commands', []))} commands")
                return retry_plan
            else:
                print(f"❌ Plan-Execute: Retry failed: {retry_error}, using fallback")
                return create_fallback_plan()
            
    except Exception as e:
        print(f"Error in execution planning: {e}")
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
    """Format survivors list for the prompt"""
    if not survivors:
        return "None"
    
    formatted = []
    for survivor in survivors:
        deadline = survivor.get('deadline', 'unknown')
        formatted.append(f"- Survivor {survivor['id']} at {survivor['pos']}, deadline: {deadline}")
    
    return "\n".join(formatted)