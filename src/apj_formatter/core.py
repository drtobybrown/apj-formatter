"""
Core styling and formatting functionality for Astrophysical Journal (ApJ) plots.
"""

from __future__ import annotations

import functools
import shutil
import subprocess
import tempfile
import textwrap
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams
import seaborn as sns

# --- Journal Geometry Constants ---------------------------------------------
SINGLE_COL_WIDTH: float = 3.5   # inches (~88.9 mm / 252 pt)
DOUBLE_COL_WIDTH: float = 7.1   # inches (~180.3 mm / 511 pt)
MAX_PAGE_HEIGHT: float = 9.0    # inches maximum journal page height
DEFAULT_ASPECT: float = 0.60    # standard height / width aspect ratio
DEFAULT_FONTSIZE_1COL: int = 10
DEFAULT_FONTSIZE_2COL: int = 10


@functools.lru_cache(maxsize=1)
def is_latex_available() -> bool:
    """
    Check if a working LaTeX installation with required packages is available.
    Cached after the first check to avoid subprocess overhead.
    """
    if not shutil.which("latex"):
        return False

    tex = textwrap.dedent(r"""
        \documentclass{article}
        \usepackage{type1cm,type1ec}
        \begin{document}lp\end{document}
    """)
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["latex", "-interaction=batchmode", "-halt-on-error", "test.tex"]
        try:
            (Path(tmp) / "test.tex").write_text(tex)
            subprocess.run(
                cmd,
                cwd=tmp,
                capture_output=True,
                check=True,
                text=True,
                timeout=3,
                stdin=subprocess.DEVNULL,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False


def _smoke_test_latex() -> None:
    """
    Smoke test LaTeX availability; raises RuntimeError if unavailable.
    """
    if not is_latex_available():
        raise RuntimeError(
            "LaTeX unavailable or missing font packages (type1cm/type1ec)."
        )


def get_figure_dimensions(
    columns: int = 1,
    *,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
) -> tuple[float, float]:
    """
    Calculate figure dimensions (width, height) in inches for single- or double-column ApJ figures.

    Parameters
    ----------
    columns : {1, 2}
        1 -> 3.5" single column; 2 -> 7.1" double column.
    aspect_ratio : float, default 0.60
        Height / width ratio.
    width_ratio : float, default 1.0
        Fraction of column width (e.g. 0.8 for 80% column width).

    Returns
    -------
    (width, height) in inches.
    """
    if columns == 1:
        width = SINGLE_COL_WIDTH * width_ratio
    elif columns == 2:
        width = DOUBLE_COL_WIDTH * width_ratio
    else:
        raise ValueError("columns must be 1 or 2")

    height = width * aspect_ratio
    if height > MAX_PAGE_HEIGHT:
        warnings.warn(
            f"Calculated figure height ({height:.2f}\") exceeds max ApJ page height ({MAX_PAGE_HEIGHT}\").",
            UserWarning,
            stacklevel=2,
        )
    return width, height


def get_apj_rcparams(
    columns: int = 1,
    *,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
    use_tex: bool = False,
    fontsize_pt: int | None = None,
) -> dict[str, Any]:
    """
    Generate dictionary of matplotlib rcParams for ApJ-ready figures.

    Parameters
    ----------
    columns : {1, 2}
        1 -> 3.5" single column; 2 -> 7.1" double column.
    aspect_ratio : float, default 0.60
        height / width of the figure.
    width_ratio : float, default 1.0
        width in units of column width.
    use_tex : bool, default False
        Use full LaTeX rendering. Falls back to STIX mathtext if LaTeX is unavailable.
    fontsize_pt : int or None, default None
        Override base font size (default: 10 pt).
    """
    width, height = get_figure_dimensions(
        columns=columns, aspect_ratio=aspect_ratio, width_ratio=width_ratio
    )
    default_pt = DEFAULT_FONTSIZE_1COL if columns == 1 else DEFAULT_FONTSIZE_2COL
    base = fontsize_pt or default_pt

    rc: dict[str, Any] = {
        # Geometry & Resolution
        "figure.figsize": (width, height),
        "figure.dpi": 300,
        "savefig.dpi": 300,

        # Typography
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "STIXGeneral", "serif"],
        "font.size": base,
        "axes.labelsize": base,
        "axes.titlesize": base,
        "legend.fontsize": max(base - 1, 6),
        "xtick.labelsize": max(base - 1, 6),
        "ytick.labelsize": max(base - 1, 6),

        # Spines & Lines
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.0,
        "lines.markersize": 4.0,
        "lines.markeredgewidth": 0.5,

        # Ticks (Standard AAS all-four-axes, inward, with minor ticks)
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "xtick.major.size": 4.0,
        "ytick.major.size": 4.0,
        "xtick.minor.size": 2.0,
        "ytick.minor.size": 2.0,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.minor.width": 0.6,
        "ytick.minor.width": 0.6,

        # Legend styling
        "legend.frameon": True,
        "legend.framealpha": 0.85,
        "legend.fancybox": False,
        "legend.edgecolor": "0.8",
        "legend.borderpad": 0.4,

        # Font Embedding for ApJ/arXiv submission (Type 42 TrueType)
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }

    # LaTeX vs STIX Mathtext
    actual_use_tex = False
    if use_tex:
        if is_latex_available():
            actual_use_tex = True
        else:
            warnings.warn(
                "LaTeX (or type1cm/type1ec) is not available on this system. "
                "Falling back to publication-grade STIX mathtext rendering.",
                UserWarning,
                stacklevel=2,
            )

    if actual_use_tex:
        rc["text.usetex"] = True
        preamble = (
            r"\usepackage[T1]{fontenc}"
            r"\usepackage{textcomp}"
            r"\usepackage{amsmath,amssymb}"
            r"\usepackage{mathptmx}"
            r"\renewcommand{\vec}[1]{\boldsymbol{#1}}"
        )
        if "text.latex.fontset" in mpl.rcParams:
            rc["text.latex.fontset"] = "custom"
        rc["text.latex.preamble"] = preamble
    else:
        rc["text.usetex"] = False
        rc.update({
            "mathtext.fontset": "stix",
            "mathtext.rm": "Times New Roman",
            "mathtext.it": "Times New Roman:italic",
            "mathtext.bf": "Times New Roman:bold",
        })

    return rc


def _set_apj_style(
    columns: int = 1,
    *,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
    use_tex: bool = False,
    fontsize_pt: int | None = None,
) -> tuple[float, float]:
    """
    Configure matplotlib globally for ApJ-ready figures.

    Parameters
    ----------
    columns : {1, 2}
        1 -> 3.5" single-column; 2 -> 7.1" double-column.
    aspect_ratio : float, default 0.60
        height / width of the figure.
    width_ratio : float, default 1.0
        width of plot in units of column width.
    use_tex : bool, default False
        Use full LaTeX rendering if available; falls back to STIX mathtext.
    fontsize_pt : int or None, default None
        Override the default font size (10 pt).

    Returns
    -------
    (width, height) in inches
    """
    # Seaborn paper context
    sns.set_theme(context="paper", style="ticks")

    rc = get_apj_rcparams(
        columns=columns,
        aspect_ratio=aspect_ratio,
        width_ratio=width_ratio,
        use_tex=use_tex,
        fontsize_pt=fontsize_pt,
    )
    rcParams.update(rc)
    return rc["figure.figsize"]


# Alias for clean public API
set_style = _set_apj_style


@contextmanager
def style(
    columns: int = 1,
    *,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
    use_tex: bool = False,
    fontsize_pt: int | None = None,
) -> Generator[tuple[float, float], None, None]:
    """
    Context manager for temporary, scoped ApJ styling without mutating global rcParams.

    Example
    -------
    >>> with apj_formatter.style(columns=1) as (w, h):
    ...     fig, ax = plt.subplots(figsize=(w, h))
    ...     ax.plot(x, y)
    """
    rc = get_apj_rcparams(
        columns=columns,
        aspect_ratio=aspect_ratio,
        width_ratio=width_ratio,
        use_tex=use_tex,
        fontsize_pt=fontsize_pt,
    )
    with mpl.rc_context(rc):
        yield rc["figure.figsize"]


def figure(
    columns: int = 1,
    *,
    wide: bool = False,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
    use_tex: bool = False,
    fontsize_pt: int | None = None,
    **kwargs: Any,
) -> plt.Figure:
    """
    Create a new matplotlib Figure configured for ApJ publication.

    Parameters
    ----------
    columns : {1, 2}, default 1
        Number of journal columns (1 -> 3.5", 2 -> 7.1").
    wide : bool, default False
        If True and columns not explicitly specified as 2, sets columns=2.
    aspect_ratio : float, default 0.60
        Figure height / width ratio.
    width_ratio : float, default 1.0
        Width multiplier relative to column width.
    use_tex : bool, default False
        Enable LaTeX rendering if available.
    fontsize_pt : int or None, default None
        Override default font size.
    **kwargs : Any
        Additional keyword arguments passed to plt.figure().
    """
    if wide:
        columns = 2
    w, h = _set_apj_style(
        columns=columns,
        aspect_ratio=aspect_ratio,
        width_ratio=width_ratio,
        use_tex=use_tex,
        fontsize_pt=fontsize_pt,
    )
    return plt.figure(figsize=(w, h), **kwargs)


def subplots(
    nrows: int = 1,
    ncols: int = 1,
    *,
    columns: int = 1,
    wide: bool = False,
    aspect_ratio: float = DEFAULT_ASPECT,
    width_ratio: float = 1.0,
    use_tex: bool = False,
    fontsize_pt: int | None = None,
    sharex: bool | str = False,
    sharey: bool | str = False,
    **kwargs: Any,
) -> tuple[plt.Figure, Any]:
    """
    Convenience wrapper around plt.subplots() configured for ApJ publication.

    Parameters
    ----------
    nrows : int, default 1
        Number of subplot rows.
    ncols : int, default 1
        Number of subplot columns.
    columns : {1, 2}, default 1
        Number of journal columns (1 -> 3.5", 2 -> 7.1").
    wide : bool, default False
        Shortcut for columns=2.
    aspect_ratio : float, default 0.60
        Figure height / width ratio.
    width_ratio : float, default 1.0
        Width multiplier.
    use_tex : bool, default False
        Use LaTeX if available.
    fontsize_pt : int or None, default None
        Override font size.
    sharex, sharey : bool or {'none', 'all', 'row', 'col'}, default False
    **kwargs : Any
        Additional kwargs passed to plt.subplots().
    """
    if wide:
        columns = 2
    w, h = _set_apj_style(
        columns=columns,
        aspect_ratio=aspect_ratio,
        width_ratio=width_ratio,
        use_tex=use_tex,
        fontsize_pt=fontsize_pt,
    )
    return plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(w, h),
        sharex=sharex,
        sharey=sharey,
        **kwargs,
    )


def save_apj(
    fig: plt.Figure,
    filename: str | Path,
    *,
    dpi: int = 300,
    bbox_inches: str = "tight",
    pad_inches: float = 0.03,
    **kwargs: Any,
) -> None:
    """
    Save a figure optimized for ApJ / AAS submission standards.

    Ensures:
    - Tight bounding box (minimal white margins).
    - 300+ DPI resolution.
    - TrueType font embedding (Type 42) for PDF/EPS submissions.
    """
    fig.savefig(
        filename,
        dpi=dpi,
        bbox_inches=bbox_inches,
        pad_inches=pad_inches,
        **kwargs,
    )
