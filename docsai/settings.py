"""
Backward compatibility shim for docsai.settings

This file imports from config.settings to maintain backward compatibility.
New code should use 'config.settings' directly.
"""

import warnings

warnings.warn(
    "Importing from 'docsai.settings' is deprecated. "
    "Use 'config.settings' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new config structure
from config.settings import *  # noqa
