"""
Re-export approval constants for backward compatibility.

New code should import directly from:
    master_data_suite.constants.approval_status
"""

from servicesapp.overwrite.constants.approval_status import VALID_APPROVAL_ACTIONS

__all__ = ["VALID_APPROVAL_ACTIONS"]
