# reasoning/reflexion.py
import os, json
from .llm_client import llm_complete
from .schema_validator import enforce_assignment_schema, create_schema_enforcement_prompt, create_fallback_plan

MEM_PATH = "memory.json"

def make_reflexion_plan(context, strategy: str = "reflexion", scratchpad: str = ""):
    """
    Entry point used by planner.make_plan(...):
      returns dict with commands
    """
    return reflexion_with_memory(context, scratchpad)

def reflexion_with_memory(context: dict, scratchpad: str = "") -> dict:
    """
    Reflexion reasoning framework with memory and critique.
    
    This approach:
    1. Loads previous rules and critiques from memory
    2. Generates a plan considering past mistakes
    3. Critiques the current plan
    4. Updates memory with new insights
    """
    
    # Load previous rules and critiques
    memory = load_rules()
    previous_rules = memory.get("rules", [])
    
    # Build the prompt incorporating memory
    system_prompt = """You are a crisis response coordinator using Reflexion reasoning. 
    
Your task is to analyze the crisis situation, learn from previous mistakes, and generate an improved response plan.

REFLEXION PROCESS:
1. Consider previous rules and critiques from past operations
2. Analyze current crisis state
3. Generate a plan avoiding past mistakes
4. Output the plan as JSON

AVAILABLE ACTIONS:
- move: Move an agent to a specific position [x, y]
- pickup_survivor: Pick up a survivor (medics only)
- drop_at_hospital: Drop a survivor at a hospital (medics only)
- extinguish_fire: Extinguish a fire (trucks only)
- clear_rubble: Clear rubble (trucks only)
- recharge: Recharge battery at depot (drones only)
- resupply: Resupply water/tools at depot (trucks only)

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
- Learn from previous mistakes and apply improved strategies"""

    # Create the user prompt with current context and memory
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

PREVIOUS RULES AND CRITIQUES:
{format_memory(previous_rules)}

Now generate an improved plan considering past mistakes and applying learned rules:"""

    # Add schema enforcement to prompt
    full_prompt = system_prompt + "\n\n" + create_schema_enforcement_prompt() + "\n\n" + user_prompt
    
    # Get LLM response
    try:
        response = llm_complete(full_prompt, temperature=0.1)
        
        # Use assignment schema validation
        plan, is_valid, error_msg = enforce_assignment_schema(response)
        
        if is_valid and plan:
            print(f"✅ Reflexion: Valid plan generated with {len(plan.get('commands', []))} commands")
            # Update memory with critique of this plan
            critique = critique_plan(context, plan, scratchpad)
            update_memory(memory, critique)
            return plan
        else:
            print(f"❌ Reflexion: Invalid JSON schema: {error_msg}")
            # Try one retry with schema reminder
            retry_prompt = full_prompt + f"\n\nPREVIOUS RESPONSE WAS INVALID: {error_msg}\n\nPlease output ONLY valid JSON matching the exact schema above."
            
            retry_response = llm_complete(retry_prompt, temperature=0.1)
            retry_plan, retry_valid, retry_error = enforce_assignment_schema(retry_response)
            
            if retry_valid and retry_plan:
                print(f"✅ Reflexion: Valid plan generated on retry with {len(retry_plan.get('commands', []))} commands")
                critique = critique_plan(context, retry_plan, scratchpad)
                update_memory(memory, critique)
                return retry_plan
            else:
                print(f"❌ Reflexion: Retry failed: {retry_error}, using fallback")
                return create_fallback_plan()
            
    except Exception as e:
        print(f"Error in Reflexion planning: {e}")
        return create_fallback_plan()

def critique_plan(context: dict, plan: dict, scratchpad: str) -> str:
    """Critique the generated plan and suggest improvements."""
    
    critique_prompt = """As a crisis response critic, analyze this plan and identify potential issues.

CURRENT SITUATION:
{context}

GENERATED PLAN:
{plan}

PREVIOUS ACTIONS:
{scratchpad}

CRITIQUE: Identify 2-3 potential issues with this plan and suggest 2-3 concrete improvements.
Focus on coordination, efficiency, and avoiding common mistakes.

Output your critique as clear, actionable feedback:"""

    try:
        critique = llm_complete(
            critique_prompt.format(
                context=json.dumps(context, indent=2),
                plan=json.dumps(plan, indent=2),
                scratchpad=scratchpad if scratchpad else "None"
            ),
            temperature=0.2
        )
        return critique
    except Exception as e:
        return f"Plan critique failed: {e}"

def load_rules():
    """Load previous rules and critiques from memory file."""
    if os.path.exists(MEM_PATH):
        try:
            with open(MEM_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {"rules": []}
    return {"rules": []}

def update_memory(memory: dict, new_critique: str):
    """Update memory with new critique and save to file."""
    memory.setdefault("rules", []).append(new_critique)
    # Keep only the last 10 rules to prevent memory from growing too large
    memory["rules"] = memory["rules"][-10:]
    save_rules(memory)

def save_rules(mem):
    """Save memory to file."""
    try:
        with open(MEM_PATH, "w") as f:
            json.dump(mem, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

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

def format_memory(rules):
    """Format memory rules for the prompt"""
    if not rules:
        return "None (first run)"
    
    formatted = []
    for i, rule in enumerate(rules[-3:], 1):  # Show last 3 rules
        formatted.append(f"{i}. {rule[:200]}...")  # Truncate long rules
    
    return "\n".join(formatted)