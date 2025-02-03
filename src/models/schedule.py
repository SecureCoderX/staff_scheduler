from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict

class ShiftType(Enum):
    """
    Represents different types of shifts in the schedule.
    Each shift type has specific staffing requirements and time periods.
    """
    GRAVES = "graves"    # Night shift, requires 4 staff
    SWINGS = "swings"    # Evening shift, requires 4 staff
    DAYS = "days"        # Day shift, requires 1 staff
    
    @property
    def min_staff_required(self) -> int:
        """Returns the minimum number of staff required for this shift type."""
        return 4 if self in (ShiftType.GRAVES, ShiftType.SWINGS) else 1

class ScheduleStatus(Enum):
    """
    Represents the current state of a schedule in its lifecycle.
    Used to control what actions can be performed on the schedule.
    """
    DRAFT = "draft"           # Initial state, being worked on
    PUBLISHED = "published"   # Finalized and visible to staff
    ARCHIVED = "archived"     # Past schedule, maintained for records

@dataclass
class ShiftAssignment:
    """
    Represents a single shift assignment for one employee.
    Links an employee to a specific shift on a specific date.
    """
    id: Optional[int]
    employee_id: int
    date: date
    shift_type: ShiftType
    schedule_id: int
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validates the shift assignment data after initialization."""
        if self.date < date.today():
            raise ValueError("Cannot assign shifts in the past")

@dataclass
class SchedulePeriod:
    """
    Represents a complete schedule for a specific time period.
    Contains all shift assignments and tracks the schedule's status.
    """
    id: Optional[int]
    start_date: date
    end_date: date
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime
    shifts: List[ShiftAssignment]
    
    def __post_init__(self):
        """Validates the schedule period after initialization."""
        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")
        if self.start_date < date.today():
            raise ValueError("Cannot create schedule starting in the past")