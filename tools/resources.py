# tools/resources.py
"""
Resource management for agents (battery, water, tools).
"""

from typing import Dict, Any

class ResourceManager:
    """Manage agent resources like battery, water, and tools."""
    
    @staticmethod
    def consume_battery(agent: Dict[str, Any], amount: int = 1) -> bool:
        """Consume battery from an agent."""
        if 'battery' not in agent:
            return True
            
        agent['battery'] -= amount
        return agent['battery'] > 0
    
    @staticmethod
    def consume_water(agent: Dict[str, Any], amount: int = 1) -> bool:
        """Consume water from a truck."""
        if agent.get('kind') != 'truck' or 'water' not in agent:
            return True
            
        agent['water'] -= amount
        return agent['water'] > 0
    
    @staticmethod
    def consume_tools(agent: Dict[str, Any], amount: int = 1) -> bool:
        """Consume tools from a truck."""
        if agent.get('kind') != 'truck' or 'tools' not in agent:
            return True
            
        agent['tools'] -= amount
        return agent['tools'] > 0
    
    @staticmethod
    def recharge_battery(agent: Dict[str, Any]) -> bool:
        """Recharge agent battery at depot."""
        if 'battery' not in agent:
            return False
            
        max_battery = agent.get('max_battery', 100)
        agent['battery'] = max_battery
        return True
    
    @staticmethod
    def resupply_water(agent: Dict[str, Any]) -> bool:
        """Resupply water for trucks."""
        if agent.get('kind') != 'truck' or 'water' not in agent:
            return False
            
        max_water = agent.get('max_water', 5)
        agent['water'] = max_water
        return True
    
    @staticmethod
    def resupply_tools(agent: Dict[str, Any]) -> bool:
        """Resupply tools for trucks."""
        if agent.get('kind') != 'truck' or 'tools' not in agent:
            return False
            
        max_tools = agent.get('max_tools', 3)
        agent['tools'] = max_tools
        return True