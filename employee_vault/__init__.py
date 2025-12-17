"""
Employee Vault - Modular Package
Complete employee management system
"""

__version__ = "4.0.2-MODULAR"

# Main modules can be imported from here
from . import config
from . import validators
from . import utils
from . import database
from . import models

__all__ = ['config', 'validators', 'utils', 'database', 'models']
