from datetime import datetime, date
import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from ..models.schedule import SchedulePeriod, ShiftAssignment, ScheduleStatus, ShiftType
from ..models.rules import SchedulingRule, RuleType
import json

class ShiftPreference(Enum):
    GRAVES = "graves"
    SWINGS = "swings"
    DAYS = "days"
    NO_PREFERENCE = "no_preference"

@dataclass
class Employee:
    id: Optional[int]
    first_name: str
    last_name: str
    email: str
    hire_date: datetime
    shift_preference: ShiftPreference
    fixed_days_off: List[int]  # 0 = Monday, 6 = Sunday
    is_active: bool
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize the database manager with the specified database path."""
        self.db_path = db_path
        
    def initialize_database(self) -> None:
        """Initialize or update the complete database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign key support
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # Create or update employees table - already exists but shown for completeness
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hire_date TEXT NOT NULL,
                    shift_preference TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create schedule_periods table - manages complete schedules
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL,  -- draft, published, archived
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES employees (id),
                    CHECK (start_date <= end_date),
                    CHECK (status IN ('draft', 'published', 'archived'))
                )
            ''')
            
            # Create shift_assignments table - individual shift assignments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shift_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,
                    shift_date TEXT NOT NULL,
                    shift_type TEXT NOT NULL,  -- graves, swings, days
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES schedule_periods (id),
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    CHECK (shift_type IN ('graves', 'swings', 'days')),
                    UNIQUE (employee_id, shift_date)  -- No double booking
                )
            ''')
            
            # Create employee_availability table - recurring availability patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    max_shifts_per_week INTEGER DEFAULT 5,
                    min_hours_between_shifts INTEGER DEFAULT 12,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    CHECK (max_shifts_per_week BETWEEN 1 AND 7),
                    CHECK (min_hours_between_shifts >= 8)
                )
            ''')
            
            # Create preferred_shifts table - many-to-many relationship
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferred_shifts (
                    employee_id INTEGER,
                    shift_type TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    PRIMARY KEY (employee_id, shift_type),
                    CHECK (shift_type IN ('graves', 'swings', 'days'))
                )
            ''')
            
            # Create scheduling_rules table - configurable scheduling constraints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduling_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    parameters TEXT NOT NULL,  -- JSON formatted parameters
                    is_active BOOLEAN DEFAULT TRUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (priority BETWEEN 1 AND 100)
                )
            ''')
            
            # Create time_off_requests table - already exists but enhanced
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_off_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    request_type TEXT NOT NULL,  -- vacation, sick_leave, training, personal
                    status TEXT NOT NULL,      -- pending, approved, denied, cancelled
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    CHECK (start_date <= end_date),
                    CHECK (request_type IN ('vacation', 'sick_leave', 'training', 'personal')),
                    CHECK (status IN ('pending', 'approved', 'denied', 'cancelled'))
                )
            ''')
            
            # Create triggers to update timestamps
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_employee_timestamp 
                AFTER UPDATE ON employees
                BEGIN
                    UPDATE employees 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_schedule_timestamp 
                AFTER UPDATE ON schedule_periods
                BEGIN
                    UPDATE schedule_periods 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            # Add indexes for common queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_shift_assignments_date 
                ON shift_assignments (shift_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_time_off_dates 
                ON time_off_requests (start_date, end_date)
            ''')
            
            conn.commit()

    def add_employee(self, employee: Employee) -> int:
        """Add a new employee to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO employees (
                        first_name, last_name, email, hire_date,
                        shift_preference, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    employee.first_name,
                    employee.last_name,
                    employee.email,
                    employee.hire_date.isoformat(),
                    employee.shift_preference.value,
                    employee.is_active
                ))
                
                employee_id = cursor.lastrowid
                
                # Add fixed days off
                for day in employee.fixed_days_off:
                    cursor.execute('''
                        INSERT INTO fixed_days_off (employee_id, day_of_week)
                        VALUES (?, ?)
                    ''', (employee_id, day))
                
                conn.commit()
                return employee_id
                
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise ValueError(f"Employee data integrity error: {str(e)}")

    def update_employee(self, employee: Employee) -> None:
        """Update an existing employee's information."""
        if employee.id is None:
            raise ValueError("Employee ID is required for updates")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE employees
                    SET first_name = ?, last_name = ?, email = ?,
                        hire_date = ?, shift_preference = ?, is_active = ?
                    WHERE id = ?
                ''', (
                    employee.first_name,
                    employee.last_name,
                    employee.email,
                    employee.hire_date.isoformat(),
                    employee.shift_preference.value,
                    employee.is_active,
                    employee.id
                ))
                
                # Update fixed days off
                cursor.execute('DELETE FROM fixed_days_off WHERE employee_id = ?',
                             (employee.id,))
                
                for day in employee.fixed_days_off:
                    cursor.execute('''
                        INSERT INTO fixed_days_off (employee_id, day_of_week)
                        VALUES (?, ?)
                    ''', (employee.id, day))
                
                conn.commit()
                
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise ValueError(f"Employee update error: {str(e)}")

    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """Retrieve an employee by their ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, first_name, last_name, email, hire_date,
                       shift_preference, is_active
                FROM employees
                WHERE id = ?
            ''', (employee_id,))
            
            employee_data = cursor.fetchone()
            if not employee_data:
                return None
                
            # Get fixed days off
            cursor.execute('''
                SELECT day_of_week
                FROM fixed_days_off
                WHERE employee_id = ?
                ORDER BY day_of_week
            ''', (employee_id,))
            
            fixed_days_off = [row[0] for row in cursor.fetchall()]
            
            return Employee(
                id=employee_data[0],
                first_name=employee_data[1],
                last_name=employee_data[2],
                email=employee_data[3],
                hire_date=datetime.fromisoformat(employee_data[4]),
                shift_preference=ShiftPreference(employee_data[5]),
                fixed_days_off=fixed_days_off,
                is_active=bool(employee_data[6])
            )

    def get_all_employees(self, active_only: bool = True) -> List[Employee]:
        """Retrieve all employees, optionally filtering for active only."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, first_name, last_name, email, hire_date,
                       shift_preference, is_active
                FROM employees
            '''
            
            if active_only:
                query += ' WHERE is_active = 1'
                
            cursor.execute(query)
            employees = []
            
            for row in cursor.fetchall():
                employee_id = row[0]
                
                # Get fixed days off for each employee
                cursor.execute('''
                    SELECT day_of_week
                    FROM fixed_days_off
                    WHERE employee_id = ?
                    ORDER BY day_of_week
                ''', (employee_id,))
                
                fixed_days_off = [day[0] for day in cursor.fetchall()]
                
                employees.append(Employee(
                    id=employee_id,
                    first_name=row[1],
                    last_name=row[2],
                    email=row[3],
                    hire_date=datetime.fromisoformat(row[4]),
                    shift_preference=ShiftPreference(row[5]),
                    fixed_days_off=fixed_days_off,
                    is_active=bool(row[6])
                ))
                
            return employees
        
    def create_schedule_period(self, schedule_period: SchedulePeriod) -> int:
        """
        Save a new schedule period and its associated shift assignments to the database.
        All operations are performed within a single transaction for data consistency.
        Returns the ID of the newly created schedule period.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # Insert the schedule period
                cursor.execute('''
                    INSERT INTO schedule_periods (
                        start_date, end_date, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    schedule_period.start_date.isoformat(),
                    schedule_period.end_date.isoformat(),
                    schedule_period.status.value,
                    schedule_period.created_at.isoformat(),
                    schedule_period.updated_at.isoformat()
                ))
                
                # Get the new schedule period ID
                schedule_id = cursor.lastrowid
                
                # Insert all shift assignments
                for shift in schedule_period.shifts:
                    cursor.execute('''
                        INSERT INTO shift_assignments (
                            schedule_id, employee_id, shift_date,
                            shift_type, notes
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        schedule_id,
                        shift.employee_id,
                        shift.date.isoformat(),
                        shift.shift_type.value,
                        shift.notes
                    ))
                
                conn.commit()
                return schedule_id
                
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(f"Failed to create schedule: {str(e)}")

    def get_schedule_period(self, schedule_id: int) -> Optional[SchedulePeriod]:
        """
        Retrieve a complete schedule period including all shift assignments.
        Returns None if the schedule period doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get the schedule period details
            cursor.execute('''
                SELECT start_date, end_date, status, created_at, updated_at
                FROM schedule_periods
                WHERE id = ?
            ''', (schedule_id,))
            
            period_data = cursor.fetchone()
            if not period_data:
                return None
                
            # Get all shift assignments for this schedule
            cursor.execute('''
                SELECT id, employee_id, shift_date, shift_type, notes
                FROM shift_assignments
                WHERE schedule_id = ?
                ORDER BY shift_date, shift_type
            ''', (schedule_id,))
            
            shifts = []
            for shift_data in cursor.fetchall():
                shifts.append(ShiftAssignment(
                    id=shift_data[0],
                    employee_id=shift_data[1],
                    date=date.fromisoformat(shift_data[2]),
                    shift_type=ShiftType(shift_data[3]),
                    schedule_id=schedule_id,
                    notes=shift_data[4]
                ))
            
            return SchedulePeriod(
                id=schedule_id,
                start_date=date.fromisoformat(period_data[0]),
                end_date=date.fromisoformat(period_data[1]),
                status=ScheduleStatus(period_data[2]),
                created_at=datetime.fromisoformat(period_data[3]),
                updated_at=datetime.fromisoformat(period_data[4]),
                shifts=shifts
            )

    def get_schedule_periods(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[ScheduleStatus] = None
    ) -> List[SchedulePeriod]:
        """
        Retrieve all schedule periods matching the given criteria.
        Supports filtering by date range and status.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT id FROM schedule_periods WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND start_date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND end_date <= ?"
                params.append(end_date.isoformat())
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
                
            query += " ORDER BY start_date DESC"
            
            cursor.execute(query, params)
            schedule_ids = [row[0] for row in cursor.fetchall()]
            
            return [
                self.get_schedule_period(schedule_id)
                for schedule_id in schedule_ids
            ]

    def update_schedule_status(
        self,
        schedule_id: int,
        new_status: ScheduleStatus
    ) -> None:
        """
        Update the status of a schedule period (e.g., from draft to published).
        Also updates the updated_at timestamp.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE schedule_periods
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_status.value, schedule_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Schedule {schedule_id} not found")
                    
                conn.commit()
                
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(f"Failed to update schedule status: {str(e)}")

    def delete_schedule_period(self, schedule_id: int) -> None:
        """
        Delete a schedule period and all its associated shift assignments.
        Cannot delete published schedules for data integrity.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # Check if schedule is published
                cursor.execute('''
                    SELECT status FROM schedule_periods WHERE id = ?
                ''', (schedule_id,))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Schedule {schedule_id} not found")
                    
                if ScheduleStatus(result[0]) == ScheduleStatus.PUBLISHED:
                    raise ValueError("Cannot delete published schedules")
                
                # Delete shift assignments first (foreign key constraint)
                cursor.execute('''
                    DELETE FROM shift_assignments WHERE schedule_id = ?
                ''', (schedule_id,))
                
                # Delete the schedule period
                cursor.execute('''
                    DELETE FROM schedule_periods WHERE id = ?
                ''', (schedule_id,))
                
                conn.commit()
                
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(f"Failed to delete schedule: {str(e)}")

    def get_employee_schedule(
        self,
        employee_id: int,
        start_date: date,
        end_date: date
    ) -> List[ShiftAssignment]:
        """
        Get all shift assignments for a specific employee within a date range.
        Useful for displaying individual schedules and checking availability.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sa.id, sa.shift_date, sa.shift_type,
                    sa.schedule_id, sa.notes
                FROM shift_assignments sa
                JOIN schedule_periods sp ON sa.schedule_id = sp.id
                WHERE sa.employee_id = ?
                AND sa.shift_date BETWEEN ? AND ?
                AND sp.status != 'draft'
                ORDER BY sa.shift_date, sa.shift_type
            ''', (
                employee_id,
                start_date.isoformat(),
                end_date.isoformat()
            ))
            
            return [
                ShiftAssignment(
                    id=row[0],
                    employee_id=employee_id,
                    date=date.fromisoformat(row[1]),
                    shift_type=ShiftType(row[2]),
                    schedule_id=row[3],
                    notes=row[4]
                )
                for row in cursor.fetchall()
            ]

    def get_active_scheduling_rules(self) -> List[SchedulingRule]:
        """
        Retrieve all active scheduling rules from the database.
        Rules are returned in priority order (highest priority first).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, rule_type, priority, parameters,
                    description, is_active
                FROM scheduling_rules
                WHERE is_active = 1
                ORDER BY priority DESC
            ''')
            
            return [
                SchedulingRule(
                    id=row[0],
                    rule_type=RuleType(row[1]),
                    priority=row[2],
                    parameters=json.loads(row[3]),
                    description=row[4],
                    is_active=bool(row[5])
                )
                for row in cursor.fetchall()
            ]