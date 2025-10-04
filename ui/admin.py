"""
Admin module for the UI package.
"""

from importlib import import_module

import_module(".stock.admin", package=__package__)
import_module(".reservation.admin", package=__package__)
import_module(".customer.admin", package=__package__)
