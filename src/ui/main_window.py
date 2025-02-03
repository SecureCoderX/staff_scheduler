from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QTabWidget)
from PyQt6.QtCore import Qt
from src.ui.tabs.schedule_tab import ScheduleTab
from src.ui.tabs.employees_tab import EmployeesTab
from src.ui.tabs.rules_tab import RulesTab

class MainWindow(QMainWindow):
    """Main window of the Staff Scheduler application."""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Staff Scheduler Pro")
        self.setMinimumSize(1200, 800)
        
        # Create the main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add the main tabs
        self.schedule_tab = ScheduleTab(self.db_manager)
        self.employees_tab = EmployeesTab(self.db_manager)
        self.rules_tab = RulesTab(self.db_manager)
        
        self.tabs.addTab(self.schedule_tab, "Schedule")
        self.tabs.addTab(self.employees_tab, "Employees")
        self.tabs.addTab(self.rules_tab, "Rules")
        
        self.layout.addWidget(self.tabs)
        
        # Set the modern style
        self.set_style()
    
    def set_style(self):
        """Apply modern styling to the application."""
        self.setStyleSheet("""
        QMainWindow {
            background-color: #f8fafc;  /* Lighter, more modern background */
        }
        QTabWidget::pane {
            border: none;  /* Remove border for cleaner look */
            background: white;
            border-radius: 8px;  /* Slightly larger radius */
            margin-top: 10px;    /* Add spacing below tabs */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);  /* Subtle shadow for depth */
        }
        QTabBar::tab {
            background: #f1f5f9;  /* Softer background */
            color: #64748b;      /* Muted text color */
            padding: 10px 25px;   /* Larger padding */
            margin: 0 2px;
            border-radius: 6px 6px 0 0;  /* Rounded top corners only */
            border: none;
            font-weight: 500;    /* Slightly bold text */
        }
        QTabBar::tab:hover {
            background: #e2e8f0;  /* Subtle hover effect */
        }
        QTabBar::tab:selected {
            background: #3b82f6;  /* Modern blue */
            color: white;
        }
        QPushButton {
            background-color: #3b82f6;  /* Modern blue */
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            min-width: 100px;
        }
        QPushButton:hover {
            background-color: #2563eb;  /* Darker blue on hover */
        }
        QPushButton:pressed {
            background-color: #1d4ed8;  /* Even darker when pressed */
        }
        QTableWidget {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: white;
            gridline-color: #f1f5f9;
        }
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f1f5f9;
        }
        QHeaderView::section {
            background-color: #f8fafc;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e2e8f0;
            font-weight: 600;
            color: #475569;
        }
        QScrollBar:vertical {
            border: none;
            background: #f1f5f9;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #cbd5e1;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #94a3b8;
        }
        """)