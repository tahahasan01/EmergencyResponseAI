# reasoning/planner.py
#!/usr/bin/env python3
"""
Main planner that routes to different reasoning strategies.
"""

from typing import Dict, Any
import importlib.util
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import functions with error handling
def import_module(module_name, function_name, default_function):
    """Import a function from a module with fallback."""
    try:
        module = __import__(f"reasoning.{module_name}", fromlist=[function_name])
        return getattr(module, function_name)
    except ImportError as e:
        print(f"Warning: {module_name} not available: {e}")
        return default_function

# Create fallback functions
def fallback_react_plan(context, strategy="react", scratchpad=""):
    return {"commands": []}

def fallback_reflexion_plan(context, strategy="reflexion", scratchpad=""):
    return {"commands": []}

def fallback_plan_execute_plan(context, strategy="plan_execute", scratchpad=""):
    return {"commands": []}

def fallback_fallback_plan(context):
    return {"commands": []}

# Import actual functions or use fallbacks
try:
    from reasoning.react import make_react_plan
except ImportError:
    make_react_plan = fallback_react_plan

try:
    from reasoning.reflexion import make_reflexion_plan
except ImportError:
    make_reflexion_plan = fallback_reflexion_plan

try:
    from reasoning.plan_execute import make_plan_execute_plan
except ImportError:
    make_plan_execute_plan = fallback_plan_execute_plan

try:
    from reasoning.fallback_planner import make_fallback_plan
except ImportError:
    make_fallback_plan = fallback_fallback_plan

try:
    from reasoning.cot import make_cot_plan
except ImportError:
    make_cot_plan = fallback_react_plan

def make_plan(state: Dict[str, Any], strategy: str = "react", scratchpad: str = "") -> Dict[str, Any]:
    """
    Route to the appropriate planning strategy based on the strategy parameter.
    
    Available strategies:
    - react: ReAct (Reason + Act interleaving)
    - reflexion: Reflexion (error reflection + retry)
    - plan_execute: Plan-and-Execute
    - fallback: Simple fallback planner for testing
    
    scratchpad: Previous planning context for memory-based strategies
    """
    
    strategy = strategy.lower()
    
    try:
        if strategy == "react":
            return make_react_plan(state, strategy, scratchpad)
        elif strategy == "reflexion":
            return make_reflexion_plan(state, strategy, scratchpad)
        elif strategy == "plan_execute":
            return make_plan_execute_plan(state, strategy, scratchpad)
        elif strategy == "cot":
            # Chain-of-Thought
            return make_cot_plan(state, strategy, scratchpad)
        else:
            # Default to fallback if unknown strategy
            print(f"Using fallback planner for strategy: {strategy}")
            return make_fallback_plan(state)
            
    except Exception as e:
        print(f"Error in {strategy} planning: {e}, using fallback")
        return make_fallback_plan(state)

def get_available_strategies() -> list:
    """Get list of available reasoning strategies."""
    return ["react", "reflexion", "plan_execute", "cot", "fallback"]
