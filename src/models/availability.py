from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional

class TimeOffRequestStatus(Enum):
    """
    Represents the status of a time-off request.
    Used to track the approval process.
    """
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"

class TimeOffRequestType(Enum):
    """
    Different types of time-off requests that affect scheduling.
    Each type might be handled differently in the scheduling process.
    """
    VACATION = "vacation"        # Planned time off
    SICK_LEAVE = "sick_leave"    # Unplanned absence
    TRAINING = "training"        # Required training or certification
    PERSONAL = "personal"        # Personal time off

class ShiftType(Enum):
    """
    Represents the type of shift.
    """
    DAY = "day"
    NIGHT = "night"

@dataclass
class TimeOffRequest:
    """
    Represents a request for time off from an employee.
    Tracks the request's status and any associated notes.
    """
    id: Optional[int]
    employee_id: int
    start_date: date
    end_date: date
    request_type: TimeOffRequestType
    status: TimeOffRequestStatus
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validates the time off request after initialization."""
        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")

@dataclass
class EmployeeAvailability:
    """
    Represents an employee's general availability pattern.
    Used for long-term scheduling preferences and constraints.
    """
    id: Optional[int]
    employee_id: int
    fixed_days_off: List[int]  # 0 = Monday, 6 = Sunday
    preferred_shifts: List[ShiftType]
    max_shifts_per_week: int = 5
    min_hours_between_shifts: int = 12
    
    def __post_init__(self):
        """Validates the availability data after initialization."""
        if not 0 <= len(self.fixed_days_off) <= 7:
            raise ValueError("Invalid number of fixed days off")
        if not 1 <= self.max_shifts_per_week <= 7:
            raise ValueError("Invalid maximum shifts per week")
        if self.min_hours_between_shifts < 8:
            raise ValueError("Must have at least 8 hours between shifts")