from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                            QDateEdit, QComboBox, QCheckBox, QPushButton,
                            QMessageBox, QWidget, QLabel, QGridLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional, List, Set
from ...database.manager import Employee, ShiftPreference

class EmployeeDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None,
                 employee: Optional[Employee] = None):
        super().__init__(parent)
        self.employee = employee
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the dialog UI components."""
        self.setWindowTitle("Employee Details")
        self.setModal(True)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Create form fields
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.email = QLineEdit()
        self.hire_date = QDateEdit()
        self.hire_date.setDisplayFormat("yyyy-MM-dd")
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        
        self.shift_preference = QComboBox()
        for pref in ShiftPreference:
            self.shift_preference.addItem(pref.value.title(), pref)
            
        # Days off selection grid
        days_widget = QWidget()
        days_layout = QGridLayout()
        self.days_off = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i, day in enumerate(days):
            checkbox = QCheckBox(day)
            self.days_off.append(checkbox)
            days_layout.addWidget(checkbox, 0, i)
            
        days_widget.setLayout(days_layout)
        
        self.is_active = QCheckBox("Active Employee")
        self.is_active.setChecked(True)
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                background-color: transparent;
                padding: 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton#save_btn {
                background-color: #2563eb;
                color: white;
                border: none;
            }
            QPushButton#save_btn:hover {
                background-color: #1d4ed8;
            }
            QPushButton#cancel_btn {
                background-color: #f3f4f6;
                border: 1px solid #e0e0e0;
            }
            QPushButton#cancel_btn:hover {
                background-color: #e5e7eb;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666;
                margin-right: 8px;
            }
        """)
            
        # Add fields to form layout
        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Email:", self.email)
        form_layout.addRow("Hire Date:", self.hire_date)
        form_layout.addRow("Shift Preference:", self.shift_preference)
        form_layout.addRow("Fixed Days Off:", days_widget)
        form_layout.addRow("Status:", self.is_active)
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Set up main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Populate fields if editing existing employee
        if self.employee:
            self.populate_fields()
            
    def populate_fields(self) -> None:
        """Populate dialog fields with existing employee data."""
        if not self.employee:
            return
            
        self.first_name.setText(self.employee.first_name)
        self.last_name.setText(self.employee.last_name)
        self.email.setText(self.employee.email)
        
        hire_date = QDate.fromString(
            self.employee.hire_date.strftime("%Y-%m-%d"),
            Qt.DateFormat.ISODate
        )
        self.hire_date.setDate(hire_date)
        
        index = self.shift_preference.findData(self.employee.shift_preference)
        self.shift_preference.setCurrentIndex(index)
        
        for day in self.employee.fixed_days_off:
            self.days_off[day].setChecked(True)
            
        self.is_active.setChecked(self.employee.is_active)
        
    def get_employee_data(self) -> Employee:
        """Collect and validate form data to create an Employee object."""
        # Basic validation
        if not self.first_name.text().strip():
            raise ValueError("First name is required")
        if not self.last_name.text().strip():
            raise ValueError("Last name is required")
        if not self.email.text().strip():
            raise ValueError("Email is required")
            
        # Collect fixed days off
        fixed_days_off = []
        for i, checkbox in enumerate(self.days_off):
            if checkbox.isChecked():
                fixed_days_off.append(i)
                
        # Create employee object
        return Employee(
            id=self.employee.id if self.employee else None,
            first_name=self.first_name.text().strip(),
            last_name=self.last_name.text().strip(),
            email=self.email.text().strip(),
            hire_date=datetime.strptime(
                self.hire_date.date().toString(Qt.DateFormat.ISODate),
                "%Y-%m-%d"
            ),
            shift_preference=self.shift_preference.currentData(),
            fixed_days_off=fixed_days_off,
            is_active=self.is_active.isChecked()
        )