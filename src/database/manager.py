from datetime import datetime
import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

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
        """Initialize the database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hire_date TEXT NOT NULL,
                    shift_preference TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
            ''')
            
            # Create fixed days off table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fixed_days_off (
                    employee_id INTEGER,
                    day_of_week INTEGER,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    PRIMARY KEY (employee_id, day_of_week)
                )
            ''')
            
            # Create time off requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_off_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
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