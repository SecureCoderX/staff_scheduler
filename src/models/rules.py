from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

class RuleType(Enum):
    """
    Different types of scheduling rules that must be enforced.
    Each rule type has its own validation logic.
    """
    MIN_STAFF = "min_staff"              # Minimum staff per shift
    CONSECUTIVE_DAYS = "consecutive_days" # Required consecutive days off
    SHIFT_SPACING = "shift_spacing"       # Minimum hours between shifts
    SKILL_REQUIREMENT = "skill"           # Required skills for shifts
    MAX_SHIFTS = "max_shifts"            # Maximum shifts per period

@dataclass
class SchedulingRule:
    """
    Represents a specific scheduling rule or constraint.
    Rules are used to validate and generate valid schedules.
    """
    id: Optional[int]
    rule_type: RuleType
    priority: int  # Higher number = higher priority
    parameters: Dict[str, Any]  # Flexible parameters for different rule types
    is_active: bool = True
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validates the rule configuration after initialization."""
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be between 1 and 100")
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validates that the rule has all required parameters for its type."""
        required_params = {
            RuleType.MIN_STAFF: {"shift_type", "min_count"},
            RuleType.CONSECUTIVE_DAYS: {"min_days"},
            RuleType.SHIFT_SPACING: {"min_hours"},
            RuleType.SKILL_REQUIREMENT: {"shift_type", "required_skills"},
            RuleType.MAX_SHIFTS: {"period_days", "max_count"}
        }
        
        if not all(param in self.parameters 
                  for param in required_params[self.rule_type]):
            raise ValueError(f"Missing required parameters for {self.rule_type}")