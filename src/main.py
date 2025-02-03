import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database.manager import DatabaseManager

def main():
    """
    Main entry point of the Staff Scheduler application.
    """
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Initialize the database
    db_manager = DatabaseManager("scheduler.db")
    db_manager.initialize_database()
    
    # Create and show the main window with database manager
    window = MainWindow(db_manager)
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()