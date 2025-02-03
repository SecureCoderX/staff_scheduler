from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QListWidget, QListWidgetItem)

class RulesTab(QWidget):
    """
    Rules tab of the application.
    Manages scheduling rules and constraints.
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize the rules tab interface."""
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Add control buttons
        button_layout = QHBoxLayout()
        self.add_rule_btn = QPushButton("Add Rule")
        self.edit_rule_btn = QPushButton("Edit Rule")
        self.remove_rule_btn = QPushButton("Remove Rule")
        
        button_layout.addWidget(self.add_rule_btn)
        button_layout.addWidget(self.edit_rule_btn)
        button_layout.addWidget(self.remove_rule_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Create rules list
        self.rules_list = QListWidget()
        
        # Add some default rules
        default_rules = [
            "Minimum 4 staff on graves and swings",
            "Only one staff member on days",
            "All staff members get two consecutive days off",
            "Some staff members have fixed days off"
        ]
        
        for rule in default_rules:
            item = QListWidgetItem(rule)
            self.rules_list.addItem(item)
        
        # Style the list
        self.rules_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e5edff;
                color: #2563eb;
            }
        """)
        
        layout.addWidget(self.rules_list)
        
        # Connect signals
        self.add_rule_btn.clicked.connect(self.add_rule)
        self.edit_rule_btn.clicked.connect(self.edit_rule)
        self.remove_rule_btn.clicked.connect(self.remove_rule)
    
    def add_rule(self):
        """Open dialog to add a new rule."""
        # TODO: Implement add rule dialog
        pass
    
    def edit_rule(self):
        """Open dialog to edit selected rule."""
        # TODO: Implement edit rule dialog
        pass
    
    def remove_rule(self):
        """Remove selected rule."""
        # TODO: Implement rule removal
        pass