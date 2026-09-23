"""
Lythos Settle — settlement analysis of shallow foundations, driven from a browser.

The program works out how much, and how fast, a shallow foundation settles on
a layered soil profile:

    1. Stresses        — in-situ σ'v0 and σ'p; the stress increase beneath the
                         foundation by Boussinesq (rectangle, strip, circle) or 2:1
    2. Immediate       — layered elastic (Steinbrenner) or Schmertmann (1978)
    3. Consolidation   — primary settlement of the clay layers from Cc, Cr, e0
                         and σ'p, and secondary compression from Cα
    4. Time            — Terzaghi's one-dimensional consolidation, per layer
    5. Checks          — total settlement and angular distortion

On top of it, a parametric or reliability study sweeps any input (a range, or
a distribution) and reports sensitivities and the probability of exceeding
the allowable settlement.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    lythossettle.config         app identity, defaults, themes, palette
    lythossettle.i18n           every text of the program, English and Turkish
    lythossettle.stress         Boussinesq, 2:1 and Steinbrenner solutions
    lythossettle.consolidation  Terzaghi time factor, compression of clay
    lythossettle.engine         the settlement analysis
    lythossettle.study          parametric / reliability studies
    lythossettle.plotting       analysis figures
    lythossettle.study_plots    study figures
    lythossettle.report         calculation report: HTML, PDF, DOCX
    lythossettle.forms          input schema and readers (interface-independent)
    lythossettle.web            local web server and the browser interface

Run it:  lythos-settle            (or  python -m lythossettle)
"""

__version__ = "0.1.0"

APP_NAME = "Lythos Settle"
ORG = "Lythos"

__all__ = ["__version__", "APP_NAME", "ORG"]
