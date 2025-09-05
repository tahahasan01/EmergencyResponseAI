#!/usr/bin/env python3
"""
JSON Schema validation for CrisisSim assignment-required format.

The assignment specifies exact JSON format that all planners must output:
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
"""

import json
from typing import Dict, List, Any, Optional, Tuple

# Valid action names as specified in the assignment
VALID_ACTION_NAMES = {
    "pickup_survivor",
    "drop_at_hospital", 
    "extinguish_fire",
    "clear_rubble",
    "recharge",
    "resupply"
}

# Valid command types
VALID_COMMAND_TYPES = {"move", "act"}

def validate_assignment_schema(plan_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a plan dictionary conforms to the assignment-specified JSON schema.
    
    Args:
        plan_dict: The plan dictionary to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    
    # Check top-level structure
    if not isinstance(plan_dict, dict):
        return False, "Plan must be a dictionary"
    
    if "commands" not in plan_dict:
        return False, "Plan must contain 'commands' field"
    
    commands = plan_dict["commands"]
    if not isinstance(commands, list):
        return False, "'commands' must be a list"
    
    # Validate each command
    for i, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            return False, f"Command {i} must be a dictionary"
        
        # Check required fields
        if "agent_id" not in cmd:
            return False, f"Command {i} missing required 'agent_id' field"
        
        if "type" not in cmd:
            return False, f"Command {i} missing required 'type' field"
        
        # Validate agent_id (should be string representation of number)
        agent_id = cmd["agent_id"]
        if not isinstance(agent_id, (str, int)):
            return False, f"Command {i} 'agent_id' must be string or int"
        
        # Validate type
        cmd_type = cmd["type"]
        if cmd_type not in VALID_COMMAND_TYPES:
            return False, f"Command {i} has invalid type '{cmd_type}'. Must be one of {VALID_COMMAND_TYPES}"
        
        # Validate type-specific fields
        if cmd_type == "move":
            if "to" not in cmd:
                return False, f"Command {i} with type 'move' missing 'to' field"
            
            to_pos = cmd["to"]
            if not isinstance(to_pos, list) or len(to_pos) != 2:
                return False, f"Command {i} 'to' field must be list of 2 integers [x, y]"
            
            if not all(isinstance(coord, int) for coord in to_pos):
                return False, f"Command {i} 'to' coordinates must be integers"
        
        elif cmd_type == "act":
            if "action_name" not in cmd:
                return False, f"Command {i} with type 'act' missing 'action_name' field"
            
            action_name = cmd["action_name"]
            if not isinstance(action_name, str):
                return False, f"Command {i} 'action_name' must be string"
            
            if action_name not in VALID_ACTION_NAMES:
                return False, f"Command {i} has invalid action_name '{action_name}'. Must be one of {VALID_ACTION_NAMES}"
    
    return True, "Valid"

def enforce_assignment_schema(response_text: str) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """
    Extract and validate JSON from LLM response according to assignment schema.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Tuple[Optional[Dict], bool, str]: (plan_dict, is_valid, error_message)
    """
    
    # Try to extract JSON from response
    try:
        # Look for JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end <= json_start:
            return None, False, "No JSON found in response"
        
        json_str = response_text[json_start:json_end]
        plan_dict = json.loads(json_str)
        
    except json.JSONDecodeError as e:
        return None, False, f"Invalid JSON: {e}"
    
    # Validate schema
    is_valid, error_msg = validate_assignment_schema(plan_dict)
    
    return plan_dict, is_valid, error_msg

def create_schema_enforcement_prompt() -> str:
    """
    Create a prompt section that enforces the assignment schema.
    """
    return f"""
REQUIRED JSON OUTPUT FORMAT (MUST MATCH EXACTLY):
{{
  "commands": [
    {{"agent_id": "2", "type": "move", "to": [5, 7]}},
    {{"agent_id": "3", "type": "act", "action_name": "pickup_survivor"}},
    {{"agent_id": "4", "type": "act", "action_name": "drop_at_hospital"}},
    {{"agent_id": "1", "type": "act", "action_name": "extinguish_fire"}},
    {{"agent_id": "1", "type": "act", "action_name": "recharge"}},
    {{"agent_id": "5", "type": "act", "action_name": "clear_rubble"}}
  ]
}}

VALIDATION RULES:
- Commands must be in a "commands" array
- Each command must have "agent_id" (string) and "type" (string)
- type "move" requires "to": [x, y] coordinates  
- type "act" requires "action_name" from: {', '.join(sorted(VALID_ACTION_NAMES))}
- agent_id must match existing agents in the context
- Coordinates must be integers within grid bounds

CRITICAL: Output ONLY valid JSON, no additional text or explanation.
"""

def create_fallback_plan() -> Dict[str, Any]:
    """
    Create a valid empty plan that conforms to assignment schema.
    """
    return {"commands": []}

def fix_common_schema_errors(plan_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to fix common schema violations to make plan valid.
    
    Args:
        plan_dict: Potentially invalid plan dictionary
        
    Returns:
        Dict[str, Any]: Fixed plan dictionary
    """
    
    if not isinstance(plan_dict, dict):
        return create_fallback_plan()
    
    if "commands" not in plan_dict:
        return create_fallback_plan()
    
    commands = plan_dict["commands"]
    if not isinstance(commands, list):
        return create_fallback_plan()
    
    fixed_commands = []
    
    for cmd in commands:
        if not isinstance(cmd, dict):
            continue
        
        # Ensure agent_id is string
        if "agent_id" in cmd:
            cmd["agent_id"] = str(cmd["agent_id"])
        else:
            continue  # Skip commands without agent_id
        
        # Validate type
        if "type" not in cmd or cmd["type"] not in VALID_COMMAND_TYPES:
            continue  # Skip invalid commands
        
        # Fix type-specific issues
        if cmd["type"] == "move":
            if "to" not in cmd or not isinstance(cmd["to"], list) or len(cmd["to"]) != 2:
                continue  # Skip invalid move commands
            
            # Ensure coordinates are integers
            try:
                cmd["to"] = [int(cmd["to"][0]), int(cmd["to"][1])]
            except (ValueError, TypeError, IndexError):
                continue  # Skip if can't convert to integers
        
        elif cmd["type"] == "act":
            if "action_name" not in cmd or cmd["action_name"] not in VALID_ACTION_NAMES:
                continue  # Skip invalid action commands
        
        fixed_commands.append(cmd)
    
    return {"commands": fixed_commands}

# Example usage and testing
if __name__ == "__main__":
    # Test valid plan
    valid_plan = {
        "commands": [
            {"agent_id": "102", "type": "move", "to": [5, 7]},
            {"agent_id": "103", "type": "act", "action_name": "pickup_survivor"},
            {"agent_id": "104", "type": "act", "action_name": "extinguish_fire"}
        ]
    }
    
    is_valid, error = validate_assignment_schema(valid_plan)
    print(f"Valid plan test: {is_valid}, {error}")
    
    # Test invalid plan
    invalid_plan = {
        "commands": [
            {"agent_id": 102, "type": "invalid_type", "to": [5, 7]},
            {"agent_id": "103", "type": "act", "action_name": "invalid_action"}
        ]
    }
    
    is_valid, error = validate_assignment_schema(invalid_plan)
    print(f"Invalid plan test: {is_valid}, {error}")
    
    # Test schema enforcement
    response = '''
    I think we should rescue the survivors. Here is my plan:
    {
      "commands": [
        {"agent_id": "102", "type": "move", "to": [3, 4]},
        {"agent_id": "103", "type": "act", "action_name": "pickup_survivor"}
      ]
    }
    That should work well.
    '''
    
    plan, valid, error = enforce_assignment_schema(response)
    print(f"Schema enforcement test: {valid}, {error}")
    print(f"Extracted plan: {plan}")
