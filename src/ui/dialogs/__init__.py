# This file makes the dialogs directory a Python package
from .employee_dialog import EmployeeDialog
from .schedule_dialogs import GenerateScheduleDialog, EditShiftsDialog

__all__ = [
    'EmployeeDialog',
    'GenerateScheduleDialog',
    'EditShiftsDialog'
]