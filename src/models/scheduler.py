from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .schedule import ShiftType, ShiftAssignment, SchedulePeriod, ScheduleStatus
from .availability import TimeOffRequest, TimeOffRequestStatus
from .rules import SchedulingRule, RuleType
from ..database.manager import Employee

@dataclass
class SchedulingScore:
    """Represents how well a schedule satisfies various constraints."""
    total_score: float
    unfilled_shifts: int
    preference_mismatches: int
    rule_violations: List[str]

class ScheduleGenerator:
    """Core scheduling engine that generates valid schedule periods."""
    
    def __init__(self, 
                 start_date: date,
                 end_date: date,
                 employees: List[Employee],
                 rules: List[SchedulingRule],
                 time_off_requests: List[TimeOffRequest]):
        """Initialize the schedule generator with necessary data."""
        self.start_date = start_date
        self.end_date = end_date
        self.employees = employees
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        self.time_off_requests = time_off_requests
        
        # Internal state tracking
        self._employee_availability = self._build_availability_map()
        self._shift_assignments: Dict[Tuple[date, ShiftType], List[int]] = defaultdict(list)
        self._employee_shifts: Dict[int, List[Tuple[date, ShiftType]]] = defaultdict(list)

    def _build_availability_map(self) -> Dict[Tuple[date, int], bool]:
        """Create a map of employee availability for each date."""
        availability = {}
        
        # Initialize all dates as available
        for current_date in self._date_range():
            for employee in self.employees:
                if not employee.is_active:
                    continue
                availability[(current_date, employee.id)] = True
                
        # Mark time off requests as unavailable
        for request in self.time_off_requests:
            if request.status != TimeOffRequestStatus.APPROVED:
                continue
                
            current = request.start_date
            while current <= request.end_date:
                availability[(current, request.employee_id)] = False
                current += timedelta(days=1)
                
        # Mark fixed days off as unavailable
        for employee in self.employees:
            if not employee.is_active:
                continue
            for current in self._date_range():
                if current.weekday() in employee.fixed_days_off:
                    availability[(current, employee.id)] = False
                    
        return availability

    def _date_range(self) -> List[date]:
        """Generate list of dates in the scheduling period."""
        dates = []
        current = self.start_date
        while current <= self.end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def generate_schedule(self) -> Tuple[Optional[SchedulePeriod], List[str]]:
        """
        Generate a complete schedule for the given period.
        Returns the schedule and any warning messages.
        """
        warnings = []
        
        # 1. Generate all required shifts
        required_shifts = self._generate_required_shifts()
        
        # 2. Initial assignment using greedy algorithm
        self._initial_assignment(required_shifts)
        
        # 3. Optimize schedule using local search
        self._optimize_schedule()
        
        # 4. Validate final schedule
        score = self._evaluate_schedule()
        
        if score.unfilled_shifts > 0:
            warnings.append(f"Unable to fill {score.unfilled_shifts} shifts")
            
        if score.rule_violations:
            warnings.extend(score.rule_violations)
            
        if score.preference_mismatches > 0:
            warnings.append(
                f"Schedule contains {score.preference_mismatches} shift preference mismatches"
            )
            
        # 5. Create SchedulePeriod object
        schedule = SchedulePeriod(
            id=None,
            start_date=self.start_date,
            end_date=self.end_date,
            status=ScheduleStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            shifts=self._create_shift_assignments()
        )
        
        return schedule, warnings

    def _generate_required_shifts(self) -> List[Tuple[date, ShiftType]]:
        """Generate list of all shifts that need to be filled."""
        required_shifts = []
        for current in self._date_range():
            for shift_type in ShiftType:
                for _ in range(shift_type.min_staff_required):
                    required_shifts.append((current, shift_type))
        return required_shifts

    def _initial_assignment(self, required_shifts: List[Tuple[date, ShiftType]]) -> None:
        """
        Make initial shift assignments using a greedy algorithm.
        Prioritize employee preferences and availability.
        """
        # Sort shifts by difficulty of assignment
        shifts_by_difficulty = self._sort_shifts_by_difficulty(required_shifts)
        
        for shift_date, shift_type in shifts_by_difficulty:
            # Get available employees sorted by suitability
            available_employees = self._get_available_employees(shift_date, shift_type)
            
            if not available_employees:
                continue
                
            # Assign the most suitable available employee
            employee_id = available_employees[0]
            self._assign_shift(employee_id, shift_date, shift_type)

    def _sort_shifts_by_difficulty(
        self, shifts: List[Tuple[date, ShiftType]]
    ) -> List[Tuple[date, ShiftType]]:
        """Sort shifts by how difficult they are to fill based on availability."""
        shift_scores = []
        for shift_date, shift_type in shifts:
            available = len(self._get_available_employees(shift_date, shift_type))
            shift_scores.append((available, (shift_date, shift_type)))
            
        # Sort by number of available employees (ascending)
        shift_scores.sort()
        return [shift for _, shift in shift_scores]

    def _get_available_employees(
        self, shift_date: date, shift_type: ShiftType
    ) -> List[int]:
        """Get list of employee IDs available for given shift, sorted by suitability."""
        available = []
        
        for employee in self.employees:
            if not employee.is_active:
                continue
                
            if not self._employee_availability[(shift_date, employee.id)]:
                continue
                
            if self._violates_constraints(employee.id, shift_date, shift_type):
                continue
                
            available.append(employee.id)
            
        # Sort by preference and previous assignments
        return sorted(
            available,
            key=lambda x: (
                self._preference_score(x, shift_type),
                -len(self._employee_shifts[x])
            )
        )

    def _violates_constraints(
        self, employee_id: int, shift_date: date, shift_type: ShiftType
    ) -> bool:
        """Check if assigning this shift would violate any scheduling rules."""
        for rule in self.rules:
            if not rule.is_active:
                continue
                
            if rule.rule_type == RuleType.CONSECUTIVE_DAYS:
                # Check consecutive days constraint
                consecutive_days = rule.parameters["min_days"]
                if self._would_violate_consecutive_days(
                    employee_id, shift_date, consecutive_days
                ):
                    return True
                    
            elif rule.rule_type == RuleType.MAX_SHIFTS:
                # Check maximum shifts constraint
                if self._would_exceed_max_shifts(
                    employee_id, rule.parameters["max_count"]
                ):
                    return True
                    
            elif rule.rule_type == RuleType.SHIFT_SPACING:
                # Check minimum hours between shifts
                if self._would_violate_shift_spacing(
                    employee_id, shift_date, shift_type,
                    rule.parameters["min_hours"]
                ):
                    return True
                    
        return False

    def _preference_score(self, employee_id: int, shift_type: ShiftType) -> int:
        """Calculate how well this shift matches employee preferences."""
        employee = next(e for e in self.employees if e.id == employee_id)
        return 1 if employee.shift_preference == shift_type else 0

    def _assign_shift(
        self, employee_id: int, shift_date: date, shift_type: ShiftType
    ) -> None:
        """Assign a shift to an employee."""
        self._shift_assignments[(shift_date, shift_type)].append(employee_id)
        self._employee_shifts[employee_id].append((shift_date, shift_type))

    def _optimize_schedule(self) -> None:
        """
        Improve the schedule using local search.
        Try to reduce constraint violations and improve preference matching.
        """
        improved = True
        iterations = 0
        max_iterations = 1000
        
        while improved and iterations < max_iterations:
            improved = False
            current_score = self._evaluate_schedule()
            
            # Try swapping shifts between employees
            for (date1, type1), employees1 in self._shift_assignments.items():
                for (date2, type2), employees2 in self._shift_assignments.items():
                    if date1 == date2 and type1 == type2:
                        continue
                        
                    for emp1 in employees1:
                        for emp2 in employees2:
                            if self._try_swap(emp1, date1, type1, emp2, date2, type2):
                                new_score = self._evaluate_schedule()
                                if new_score.total_score > current_score.total_score:
                                    improved = True
                                else:
                                    # Revert the swap
                                    self._try_swap(emp2, date1, type1, emp1, date2, type2)
                                    
            iterations += 1

    def _try_swap(
        self, emp1: int, date1: date, type1: ShiftType,
        emp2: int, date2: date, type2: ShiftType
    ) -> bool:
        """Attempt to swap shifts between two employees."""
        # Remove current assignments
        self._shift_assignments[(date1, type1)].remove(emp1)
        self._shift_assignments[(date2, type2)].remove(emp2)
        self._employee_shifts[emp1].remove((date1, type1))
        self._employee_shifts[emp2].remove((date2, type2))
        
        # Check if new assignments would be valid
        valid1 = not self._violates_constraints(emp2, date1, type1)
        valid2 = not self._violates_constraints(emp1, date2, type2)
        
        if valid1 and valid2:
            # Make new assignments
            self._assign_shift(emp2, date1, type1)
            self._assign_shift(emp1, date2, type2)
            return True
            
        # Restore original assignments
        self._assign_shift(emp1, date1, type1)
        self._assign_shift(emp2, date2, type2)
        return False

    def _evaluate_schedule(self) -> SchedulingScore:
        """Evaluate the current schedule against all constraints and preferences."""
        unfilled = 0
        mismatches = 0
        violations = []
        
        # Check shift coverage
        for current in self._date_range():
            for shift_type in ShiftType:
                assigned = len(self._shift_assignments[(current, shift_type)])
                if assigned < shift_type.min_staff_required:
                    unfilled += shift_type.min_staff_required - assigned
                    
        # Check preferences and rules
        for employee_id, shifts in self._employee_shifts.items():
            employee = next(e for e in self.employees if e.id == employee_id)
            
            # Count preference mismatches
            for _, shift_type in shifts:
                if shift_type != employee.shift_preference:
                    mismatches += 1
                    
            # Check rule violations
            for rule in self.rules:
                if not rule.is_active:
                    continue
                    
                if self._check_rule_violation(employee_id, rule):
                    violations.append(
                        f"Employee {employee.full_name} violates {rule.rule_type.value}"
                    )
                    
        # Calculate total score (lower is better)
        total_score = -(unfilled * 100 + mismatches * 10 + len(violations) * 50)
        
        return SchedulingScore(total_score, unfilled, mismatches, violations)

    def _create_shift_assignments(self) -> List[ShiftAssignment]:
        """Convert internal assignment tracking to ShiftAssignment objects."""
        assignments = []
        
        for (shift_date, shift_type), employees in self._shift_assignments.items():
            for employee_id in employees:
                assignments.append(ShiftAssignment(
                    id=None,
                    employee_id=employee_id,
                    date=shift_date,
                    shift_type=shift_type,
                    schedule_id=0  # Will be set when schedule is saved
                ))
                
        return assignments