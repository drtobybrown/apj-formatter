"""
Unit tests for apj_formatter.
"""

import tempfile
import unittest
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

import apj_formatter
from apj_formatter import (
    DOUBLE_COL_WIDTH,
    SINGLE_COL_WIDTH,
    _set_apj_style,
    figure,
    get_apj_rcparams,
    get_figure_dimensions,
    save_apj,
    set_style,
    style,
    subplots,
)


class TestApjFormatter(unittest.TestCase):

    def test_dimensions(self):
        w1, h1 = get_figure_dimensions(1, aspect_ratio=0.6, width_ratio=1.0)
        self.assertAlmostEqual(w1, SINGLE_COL_WIDTH)
        self.assertAlmostEqual(h1, SINGLE_COL_WIDTH * 0.6)

        w2, h2 = get_figure_dimensions(2, aspect_ratio=0.5, width_ratio=0.8)
        self.assertAlmostEqual(w2, DOUBLE_COL_WIDTH * 0.8)
        self.assertAlmostEqual(h2, DOUBLE_COL_WIDTH * 0.8 * 0.5)

        with self.assertRaises(ValueError):
            get_figure_dimensions(3)

    def test_rcparams_apj_styling(self):
        rc = get_apj_rcparams(columns=1)
        # Check standard ApJ/AAS publication parameters
        self.assertEqual(rc["xtick.direction"], "in")
        self.assertEqual(rc["ytick.direction"], "in")
        self.assertTrue(rc["xtick.top"])
        self.assertTrue(rc["ytick.right"])
        self.assertTrue(rc["xtick.minor.visible"])
        self.assertTrue(rc["ytick.minor.visible"])
        self.assertEqual(rc["axes.linewidth"], 0.8)
        self.assertEqual(rc["pdf.fonttype"], 42)
        self.assertEqual(rc["ps.fonttype"], 42)
        self.assertEqual(rc["font.family"], "serif")
        self.assertIn("Times New Roman", rc["font.serif"])

    def test_convenience_functions(self):
        fig = figure(columns=1, aspect_ratio=0.7)
        self.assertIsInstance(fig, plt.Figure)
        self.assertAlmostEqual(fig.get_figwidth(), SINGLE_COL_WIDTH)
        plt.close(fig)

        fig, ax = subplots(1, 2, wide=True, aspect_ratio=0.4)
        self.assertIsInstance(fig, plt.Figure)
        self.assertAlmostEqual(fig.get_figwidth(), DOUBLE_COL_WIDTH)
        self.assertEqual(len(ax), 2)
        plt.close(fig)

    def test_context_manager(self):
        original_lw = mpl.rcParams.get("axes.linewidth")
        with style(columns=2, aspect_ratio=0.5) as (w, h):
            self.assertAlmostEqual(w, DOUBLE_COL_WIDTH)
            self.assertAlmostEqual(h, DOUBLE_COL_WIDTH * 0.5)
            self.assertEqual(mpl.rcParams["axes.linewidth"], 0.8)
            self.assertTrue(mpl.rcParams["xtick.top"])

        # Outside context, rcParams should revert
        self.assertEqual(mpl.rcParams.get("axes.linewidth"), original_lw)

    def test_save_apj(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = subplots(1, 1, columns=1)
            ax.plot([0, 1, 2], [0, 1, 4], label=r"Test $\chi^2$")
            ax.set_xlabel(r"Wavelength ($\mu\mathrm{m}$)")
            ax.set_ylabel(r"Flux Density ($F_\nu$)")
            ax.legend()

            pdf_path = Path(tmpdir) / "test_plot.pdf"
            png_path = Path(tmpdir) / "test_plot.png"

            save_apj(fig, pdf_path)
            save_apj(fig, png_path)
            plt.close(fig)

            self.assertTrue(pdf_path.exists())
            self.assertGreater(pdf_path.stat().st_size, 0)
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)

    def test_latex_fallback_safety(self):
        # Requesting use_tex=True should not crash even if LaTeX packages are missing
        rc = get_apj_rcparams(columns=1, use_tex=True)
        self.assertIn("text.usetex", rc)


if __name__ == "__main__":
    unittest.main()
