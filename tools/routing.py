# tools/routing.py
"""
Routing utilities for pathfinding and navigation.
"""

from typing import List, Tuple, Set
from collections import deque

class Router:
    """Pathfinding and navigation utilities."""
    
    @staticmethod
    def bfs(start: Tuple[int, int], goal: Tuple[int, int], 
            obstacles: Set[Tuple[int, int]], width: int, height: int) -> List[Tuple[int, int]]:
        """
        Breadth-first search for pathfinding.
        Returns a path from start to goal, avoiding obstacles.
        """
        queue = deque([(start, [])])
        visited = set([start])
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == goal:
                return path + [(x, y)]
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < width and 0 <= ny < height and 
                    (nx, ny) not in obstacles and 
                    (nx, ny) not in visited):
                    
                    queue.append(((nx, ny), path + [(x, y)]))
                    visited.add((nx, ny))
        
        return []  # No path found
    
    @staticmethod
    def get_next_step_toward(start: Tuple[int, int], goal: Tuple[int, int], 
                            obstacles: Set[Tuple[int, int]], width: int, height: int) -> Tuple[int, int]:
        """
        Get the next step toward a goal, avoiding obstacles.
        """
        path = Router.bfs(start, goal, obstacles, width, height)
        if len(path) > 1:
            return path[1]  # Next step after current position
        return start  # Stay in place if no path found
    
    @staticmethod
    def distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two points."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])