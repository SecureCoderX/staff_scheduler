from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QCalendarWidget, QLabel)
from PyQt6.QtCore import Qt, QDate

class ScheduleTab(QWidget):
    """
    Schedule tab of the application.
    Displays and manages the weekly schedule view.
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize the schedule tab interface."""
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Add top control bar
        control_bar = QHBoxLayout()
        
        # Add calendar widget for date selection
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.calendar.clicked.connect(self.date_selected)
        
        # Add buttons for schedule management
        self.prev_week_btn = QPushButton("Previous Week")
        self.next_week_btn = QPushButton("Next Week")
        self.generate_btn = QPushButton("Generate Schedule")
        
        control_bar.addWidget(self.prev_week_btn)
        control_bar.addWidget(self.next_week_btn)
        control_bar.addStretch()
        control_bar.addWidget(self.generate_btn)
        
        # Add the control bar to main layout
        layout.addLayout(control_bar)
        
        # Create schedule grid (placeholder)
        self.schedule_grid = QWidget()
        schedule_layout = QVBoxLayout(self.schedule_grid)
        
        # Add shift type labels
        shifts = ["Graves", "Swings", "Days"]
        for shift in shifts:
            shift_label = QLabel(shift)
            shift_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    padding: 10px;
                    background-color: #f8fafc;
                    border-radius: 4px;
                }
            """)
            schedule_layout.addWidget(shift_label)
        
        # Add the schedule grid to main layout
        layout.addWidget(self.schedule_grid)
    
    def date_selected(self, date):
        """Handle date selection in the calendar."""
        # TODO: Update schedule view for selected date
        pass