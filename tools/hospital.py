# tools/hospital.py
"""
Hospital triage system with capacity limits and queue management.
"""

from typing import List, Dict, Any
from collections import deque

class Hospital:
    """Hospital with limited capacity and triage system."""
    
    def __init__(self, pos: List[int], capacity: int = 3, triage_policy: str = "fifo"):
        self.pos = pos
        self.capacity = capacity
        self.triage_policy = triage_policy
        self.queue = deque()
        self.patients = []
        
    def admit_patient(self, survivor: Dict[str, Any]) -> bool:
        """Attempt to admit a patient to the hospital."""
        if len(self.patients) < self.capacity:
            self.patients.append(survivor)
            return True
        
        # Add to queue if hospital is full
        self.queue.append(survivor)
        return False
    
    def discharge_patient(self) -> Dict[str, Any]:
        """Discharge a patient (when rescued)."""
        if self.patients:
            return self.patients.pop(0)
        return None
    
    def process_queue(self) -> None:
        """Process the waiting queue."""
        while self.queue and len(self.patients) < self.capacity:
            # Get next patient based on triage policy
            if self.triage_policy == "deadline":
                # Find patient with lowest deadline
                min_deadline_idx = 0
                for i, patient in enumerate(self.queue):
                    if patient.get('deadline', float('inf')) < self.queue[min_deadline_idx].get('deadline', float('inf')):
                        min_deadline_idx = i
                
                # Move to hospital
                patient = self.queue[min_deadline_idx]
                del self.queue[min_deadline_idx]
                self.patients.append(patient)
            else:  # FIFO
                patient = self.queue.popleft()
                self.patients.append(patient)
    
    def get_queue_length(self) -> int:
        """Get the current queue length."""
        return len(self.queue)
    
    def get_overflow_events(self) -> int:
        """Count how many patients were turned away due to overflow."""
        # This would need to be tracked separately
        return 0