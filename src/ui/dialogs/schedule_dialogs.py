from datetime import date
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QCheckBox, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
import sqlite3

from src.models.scheduler import ScheduleGenerator

from ...database.manager import DatabaseManager
from ...models.schedule import SchedulePeriod, ShiftType
from ...models.availability import TimeOffRequestStatus

class GenerateScheduleDialog(QDialog):
    """Dialog for generating a new schedule."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        start_date: date,
        end_date: date,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.start_date = start_date
        self.end_date = end_date
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the dialog UI."""
        self.setWindowTitle("Generate Schedule")
        layout = QVBoxLayout(self)
        
        # Add date range display
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel(
            f"Generate schedule for week of {self.start_date.strftime('%B %d, %Y')}"
        ))
        layout.addLayout(date_layout)
        
        # Add generation options
        options_layout = QVBoxLayout()
        self.respect_preferences = QCheckBox("Respect shift preferences")
        self.respect_preferences.setChecked(True)
        options_layout.addWidget(self.respect_preferences)
        
        self.balance_shifts = QCheckBox("Balance shift assignments")
        self.balance_shifts.setChecked(True)
        options_layout.addWidget(self.balance_shifts)
        
        layout.addLayout(options_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(self._generate_schedule)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(generate_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def _generate_schedule(self) -> None:
        """Generate the schedule with selected options."""
        try:
            # Get required data
            employees = self.db_manager.get_all_employees(active_only=True)
            rules = self.db_manager.get_active_scheduling_rules()
            time_off = self.db_manager.get_time_off_requests(
                start_date=self.start_date,
                end_date=self.end_date,
                status=TimeOffRequestStatus.APPROVED
            )
            
            # Create schedule generator with options
            generator = ScheduleGenerator(
                start_date=self.start_date,
                end_date=self.end_date,
                employees=employees,
                rules=rules,
                time_off_requests=time_off,
                respect_preferences=self.respect_preferences.isChecked(),
                balance_workload=self.balance_shifts.isChecked()
            )
            
            # Generate schedule
            schedule, warnings = generator.generate_schedule()
            
            # Save to database
            schedule_id = self.db_manager.create_schedule_period(schedule)
            
            # Show warnings if any
            if warnings:
                QMessageBox.warning(
                    self,
                    "Schedule Generation Warnings",
                    "\n".join(warnings)
                )
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate schedule: {str(e)}"
            )

class EditShiftsDialog(QDialog):
    """Dialog for editing shift assignments."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        schedule: SchedulePeriod,
        shift_date: date,
        shift_type: ShiftType,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.schedule = schedule
        self.shift_date = shift_date
        self.shift_type = shift_type
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the dialog UI."""
        self.setWindowTitle(
            f"Edit {self.shift_type.value.title()} Shift - "
            f"{self.shift_date.strftime('%B %d, %Y')}"
        )
        layout = QVBoxLayout(self)
        
        # Add employee selection grid
        self.employee_grid = QGridLayout()
        
        # Get current assignments
        current_staff = []
        for shift in self.schedule.shifts:
            if (shift.date == self.shift_date and 
                shift.shift_type == self.shift_type):
                employee = self.db_manager.get_employee(shift.employee_id)
                if employee:
                    current_staff.append(employee.id)
                    
        # Add employee checkboxes
        row = 0
        col = 0
        max_cols = 2
        
        self.employee_boxes = {}
        for employee in self.db_manager.get_all_employees(active_only=True):
            checkbox = QCheckBox(employee.full_name)
            checkbox.setChecked(employee.id in current_staff)
            
            # Add visual indicator for employee preferences
            if employee.shift_preference == self.shift_type:
                checkbox.setStyleSheet("QCheckBox { color: green; }")
                
            self.employee_boxes[employee.id] = checkbox
            self.employee_grid.addWidget(checkbox, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        layout.addLayout(self.employee_grid)
        
        # Add staffing requirement note
        layout.addWidget(QLabel(
            f"Minimum required staff: {self.shift_type.min_staff_required}"
        ))
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def accept(self) -> None:
        """Validate and save the shift changes."""
        selected_employees = [
            emp_id for emp_id, checkbox in self.employee_boxes.items()
            if checkbox.isChecked()
        ]
        
        # Validate minimum staffing
        if len(selected_employees) < self.shift_type.min_staff_required:
            QMessageBox.warning(
                self,
                "Invalid Assignment",
                f"This shift requires at least "
                f"{self.shift_type.min_staff_required} staff members."
            )
            return
            
        try:
            # Update database
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove existing assignments
                cursor.execute('''
                    DELETE FROM shift_assignments
                    WHERE schedule_id = ?
                    AND shift_date = ?
                    AND shift_type = ?
                ''', (
                    self.schedule.id,
                    self.shift_date.isoformat(),
                    self.shift_type.value
                ))
                
                # Add new assignments
                for employee_id in selected_employees:
                    cursor.execute('''
                        INSERT INTO shift_assignments (
                            schedule_id, employee_id, shift_date,
                            shift_type, notes
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        self.schedule.id,
                        employee_id,
                        self.shift_date.isoformat(),
                        self.shift_type.value,
                        None
                    ))
                    
                conn.commit()
                
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Changes",
                f"Failed to save shift assignments: {str(e)}"
            )