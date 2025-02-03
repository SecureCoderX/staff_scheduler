from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCalendarWidget,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox, QMenu,
    QDialog, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from ...database.manager import DatabaseManager
from ...models.schedule import (
    SchedulePeriod, ShiftType, ScheduleStatus, ShiftAssignment
)
from ..dialogs import GenerateScheduleDialog, EditShiftsDialog

class ScheduleTab(QWidget):
    """Schedule tab of the application. Displays and manages weekly schedules."""
    
    schedule_updated = pyqtSignal()  # Emitted when schedule changes
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_week_start: Optional[date] = None
        self.current_schedule: Optional[SchedulePeriod] = None
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the schedule tab interface."""
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Add top control bar
        control_bar = QHBoxLayout()
        
        # Add calendar widget for date selection
        calendar_layout = QVBoxLayout()
        calendar_layout.addWidget(QLabel("Select Week:"))
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames
        )
        self.calendar.clicked.connect(self._week_selected)
        calendar_layout.addWidget(self.calendar)
        
        # Add schedule view mode selector
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("View:"))
        self.prev_week_btn = QPushButton("◀")
        self.prev_week_btn.setMaximumWidth(30)
        self.prev_week_btn.clicked.connect(self._previous_week)
        
        self.next_week_btn = QPushButton("▶")
        self.next_week_btn.setMaximumWidth(30)
        self.next_week_btn.clicked.connect(self._next_week)
        
        self.generate_btn = QPushButton("Generate Schedule")
        self.generate_btn.clicked.connect(self._generate_schedule)
        
        view_layout.addWidget(self.prev_week_btn)
        view_layout.addWidget(self.next_week_btn)
        view_layout.addStretch()
        view_layout.addWidget(self.generate_btn)
        
        calendar_layout.addLayout(view_layout)
        control_bar.addLayout(calendar_layout)
        
        # Schedule status and actions
        status_layout = QVBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)
        
        self.publish_btn = QPushButton("Publish Schedule")
        self.publish_btn.clicked.connect(self._publish_schedule)
        self.publish_btn.setEnabled(False)
        status_layout.addWidget(self.publish_btn)
        
        control_bar.addLayout(status_layout)
        
        # Add the control bar to main layout
        layout.addLayout(control_bar)
        
        # Create schedule grid
        self.schedule_grid = QTableWidget()
        self.schedule_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.schedule_grid.customContextMenuRequested.connect(self._show_context_menu)
        self._initialize_schedule_grid()
        
        layout.addWidget(self.schedule_grid)
        
        # Load current week's schedule
        self._week_selected(QDate.currentDate())
        
    def _initialize_schedule_grid(self) -> None:
        """Set up the schedule display grid."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                "Friday", "Saturday", "Sunday"]
        
        self.schedule_grid.setColumnCount(len(days))
        self.schedule_grid.setHorizontalHeaderLabels(days)
        
        # Three rows for each shift type
        self.schedule_grid.setRowCount(len(ShiftType) * 2)
        vertical_headers = []
        for shift_type in ShiftType:
            vertical_headers.extend([
                shift_type.value.title(),
                "Staff"
            ])
        self.schedule_grid.setVerticalHeaderLabels(vertical_headers)
        
        # Set column widths
        for col in range(len(days)):
            self.schedule_grid.setColumnWidth(col, 150)
            
    def _week_selected(self, selected_date: QDate) -> None:
        """Handle week selection in the calendar."""
        # Convert to Python date and find the Monday of this week
        py_date = selected_date.toPyDate()
        monday = py_date - timedelta(days=py_date.weekday())
        
        if monday != self.current_week_start:
            self.current_week_start = monday
            self._load_week_schedule()
            
    def _load_week_schedule(self) -> None:
        """Load and display the schedule for the current week."""
        if not self.current_week_start:
            return
            
        week_end = self.current_week_start + timedelta(days=6)
        
        try:
            # Get schedule for this week
            schedules = self.db_manager.get_schedule_periods(
                start_date=self.current_week_start,
                end_date=week_end
            )
            
            if schedules:
                self.current_schedule = schedules[0]
                self.status_label.setText(
                    f"Schedule Status: {self.current_schedule.status.value}"
                )
                self.publish_btn.setEnabled(
                    self.current_schedule.status == ScheduleStatus.DRAFT
                )
            else:
                self.current_schedule = None
                self.status_label.setText("No schedule found")
                self.publish_btn.setEnabled(False)
                
            self._update_schedule_grid()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Schedule",
                f"Failed to load schedule: {str(e)}"
            )
            
    def _update_schedule_grid(self) -> None:
        """Update the schedule grid with current data."""
        if not self.current_schedule or not self.current_week_start:
            self._clear_schedule_grid()
            return
            
        # Group shifts by date and type
        shifts_by_date: Dict[date, Dict[ShiftType, List[str]]] = {}
        current = self.current_week_start
        
        while current <= self.current_week_start + timedelta(days=6):
            shifts_by_date[current] = {
                shift_type: [] for shift_type in ShiftType
            }
            current += timedelta(days=1)
            
        # Populate shift assignments
        for shift in self.current_schedule.shifts:
            if shift.date in shifts_by_date:
                employee = self.db_manager.get_employee(shift.employee_id)
                if employee:
                    shifts_by_date[shift.date][shift.shift_type].append(
                        employee.full_name
                    )
                    
        # Update grid
        for col, current_date in enumerate(sorted(shifts_by_date.keys())):
            row = 0
            for shift_type in ShiftType:
                # Status cell
                status_item = QTableWidgetItem("✓")
                if len(shifts_by_date[current_date][shift_type]) < shift_type.min_staff_required:
                    status_item = QTableWidgetItem("⚠")
                    status_item.setBackground(QColor(255, 200, 200))
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.schedule_grid.setItem(row, col, status_item)
                
                # Staff list cell
                staff_text = "\n".join(shifts_by_date[current_date][shift_type])
                staff_item = QTableWidgetItem(staff_text)
                staff_item.setFlags(staff_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.schedule_grid.setItem(row + 1, col, staff_item)
                
                row += 2
                
        self.schedule_grid.resizeRowsToContents()
        
    def _clear_schedule_grid(self) -> None:
        """Clear all data from the schedule grid."""
        for row in range(self.schedule_grid.rowCount()):
            for col in range(self.schedule_grid.columnCount()):
                self.schedule_grid.setItem(row, col, QTableWidgetItem(""))
                
    def _previous_week(self) -> None:
        """Move to the previous week."""
        if self.current_week_start:
            new_date = self.current_week_start - timedelta(days=7)
            self.calendar.setSelectedDate(QDate.fromString(
                new_date.isoformat(), Qt.DateFormat.ISODate
            ))
            
    def _next_week(self) -> None:
        """Move to the next week."""
        if self.current_week_start:
            new_date = self.current_week_start + timedelta(days=7)
            self.calendar.setSelectedDate(QDate.fromString(
                new_date.isoformat(), Qt.DateFormat.ISODate
            ))
            
    def _generate_schedule(self) -> None:
        """Generate a new schedule for the current week."""
        if not self.current_week_start:
            return
            
        try:
            dialog = GenerateScheduleDialog(
                self.db_manager,
                self.current_week_start,
                self.current_week_start + timedelta(days=6)
            )
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_week_schedule()
                self.schedule_updated.emit()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Schedule Generation Error",
                f"Failed to generate schedule: {str(e)}"
            )
            
    def _publish_schedule(self) -> None:
        """Publish the current draft schedule."""
        if not self.current_schedule:
            return
            
        try:
            self.db_manager.update_schedule_status(
                self.current_schedule.id,
                ScheduleStatus.PUBLISHED
            )
            
            self._load_week_schedule()
            self.schedule_updated.emit()
            
            QMessageBox.information(
                self,
                "Schedule Published",
                "The schedule has been published successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Publication Error",
                f"Failed to publish schedule: {str(e)}"
            )
            
    def _show_context_menu(self, position) -> None:
        """Show context menu for schedule grid."""
        if not self.current_schedule:
            return
            
        if self.current_schedule.status != ScheduleStatus.DRAFT:
            return
            
        item = self.schedule_grid.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        edit_action = QAction("Edit Shifts", self)
        edit_action.triggered.connect(
            lambda: self._edit_shifts(item.row(), item.column())
        )
        menu.addAction(edit_action)
        
        menu.exec(self.schedule_grid.mapToGlobal(position))
        
    def _edit_shifts(self, row: int, col: int) -> None:
        """Open dialog to edit shifts for the selected day."""
        if not self.current_week_start:
            return
            
        shift_date = self.current_week_start + timedelta(days=col)
        shift_type = list(ShiftType)[row // 2]  # Integer division
        
        dialog = EditShiftsDialog(
            self.db_manager,
            self.current_schedule,
            shift_date,
            shift_type
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_week_schedule()
            self.schedule_updated.emit()