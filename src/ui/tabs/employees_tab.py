from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QMessageBox)
from PyQt6.QtCore import Qt
from src.database.manager import DatabaseManager

class EmployeesTab(QWidget):
    """
    Employees tab of the application.
    Manages employee records and their scheduling preferences.
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.employees = []
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        """Initialize the employees tab interface."""
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Add control buttons
        button_layout = QHBoxLayout()
        self.add_employee_btn = QPushButton("Add Employee")
        self.edit_employee_btn = QPushButton("Edit Employee")
        self.remove_employee_btn = QPushButton("Remove Employee")
        
        button_layout.addWidget(self.add_employee_btn)
        button_layout.addWidget(self.edit_employee_btn)
        button_layout.addWidget(self.remove_employee_btn)
        button_layout.addStretch()
        
        for btn in [self.add_employee_btn, self.edit_employee_btn, self.remove_employee_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)  # Hand cursor on hover

        # Style specific buttons differently
        self.add_employee_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;  /* Blue for primary action */
            }
        """)
        self.edit_employee_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;  /* Amber for modification */
            }
        """)
        self.remove_employee_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;  /* Red for destructive action */
            }
        """)
                    
        layout.addLayout(button_layout)
                    
        # Create employee table
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(5)
        self.employee_table.setHorizontalHeaderLabels([
            "Name", "Status", "Preferred Shift", "Days Off", "Notes"
        ])
                    
        # Set column widths
        self.employee_table.horizontalHeader().setStretchLastSection(True)
                    
        layout.addWidget(self.employee_table)
                    
        # Connect signals
        self.add_employee_btn.clicked.connect(self.add_employee)
        self.edit_employee_btn.clicked.connect(self.edit_employee)
        self.remove_employee_btn.clicked.connect(self.remove_employee)
    
    def load_employees(self):
        """Temporary function to load sample employee data."""
        # We'll implement actual database loading later
        sample_data = [
            {
                'name': 'John Doe',
                'status': 'Active',
                'preferred_shift': 'Graves',
                'days_off': 'Saturday, Sunday',
                'notes': 'Team lead'
            },
            {
                'name': 'Jane Smith',
                'status': 'Active',
                'preferred_shift': 'Swings',
                'days_off': 'Sunday, Monday',
                'notes': 'Certified trainer'
            }
        ]
        self.employees = sample_data
        self.refresh_table()
    
    def refresh_table(self):
        """Update the table with current employee data."""
        self.employee_table.setRowCount(len(self.employees))
        
        for row, employee in enumerate(self.employees):
            for col, (key, value) in enumerate(employee.items()):
                item = QTableWidgetItem(str(value))
                self.employee_table.setItem(row, col, item)
    
    def add_employee(self):
        """Placeholder for adding an employee."""
        QMessageBox.information(self, "Info", "Add employee functionality coming soon!")
    
    def edit_employee(self):
        """Placeholder for editing an employee."""
        QMessageBox.information(self, "Info", "Edit employee functionality coming soon!")
    
    def remove_employee(self):
        """Placeholder for removing an employee."""
        QMessageBox.information(self, "Info", "Remove employee functionality coming soon!")