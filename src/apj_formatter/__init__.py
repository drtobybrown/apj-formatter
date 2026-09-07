"""
apj-formatter: Publication-ready matplotlib formatting targeted for the Astrophysical Journal (ApJ).
"""

from apj_formatter.core import (
    DOUBLE_COL_WIDTH,
    MAX_PAGE_HEIGHT,
    SINGLE_COL_WIDTH,
    _Formatter,
    _set_apj_style,
    _smoke_test_latex,
    figure,
    formatter,
    get_apj_rcparams,
    get_figure_dimensions,
    is_latex_available,
    save_apj,
    set_style,
    style,
    subplots,
)

__version__ = "0.1.0"

__all__ = [
    "DOUBLE_COL_WIDTH",
    "MAX_PAGE_HEIGHT",
    "SINGLE_COL_WIDTH",
    "_Formatter",
    "_set_apj_style",
    "_smoke_test_latex",
    "figure",
    "formatter",
    "get_apj_rcparams",
    "get_figure_dimensions",
    "is_latex_available",
    "save_apj",
    "set_style",
    "style",
    "subplots",
]
