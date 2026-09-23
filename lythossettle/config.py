"""
Configuration for Lythos Settle: the default project, the choice lists, and
the theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `lythossettle.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "SOIL_FILL", "SHAPES", "STRESS_METHODS", "IMMEDIATE_METHODS", "RIGIDITY",
           "BEHAVIOURS", "DRAINAGE", "ACCENT"]

MM_PER_M = 1000.0

# --- Choice lists (the first entry is the default where one is needed) -----
SHAPES = ["rectangle", "strip", "circle"]
STRESS_METHODS = ["boussinesq", "two_to_one"]
IMMEDIATE_METHODS = ["elastic", "schmertmann"]
RIGIDITY = ["flexible", "rigid"]
BEHAVIOURS = ["granular", "cohesive"]
DRAINAGE = ["double", "single"]

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#2F80ED"

THEMES = {
    "dark": dict(bg="#1E1F24", panel="#2A2C33", input_bg="#33363F", fg="#E6E6E6",
                 fg_dim="#9AA0AA", border="#3D414B", hover="#3A3E48", btn="#353943",
                 muted="#555A66", accent=ACCENT, accent_hover="#4A90F0"),
    "light": dict(bg="#F3F4F6", panel="#FFFFFF", input_bg="#FFFFFF", fg="#1F2933",
                  fg_dim="#6B7280", border="#D9DDE3", hover="#EEF1F5", btn="#F7F8FA",
                  muted="#B8C0CC", accent=ACCENT, accent_hover="#1F6FDB"),
}

# Semantic colours: the same quantity is the same colour in every figure.
PLOT_PALETTE = dict(
    immediate="#2F80ED", consolidation="#9B5DE5", secondary="#F2994A",
    total="#EB5757", stress="#0EA5A4", overburden="#6B7280", preconsolidation="#27AE60",
    limit="#B9770E", water="#56CCF2", footing="#7F8C8D",
    center="#2F80ED", char="#9B5DE5", edge="#F2994A", corner="#0EA5A4",
    allowable="#EB5757",
)

# Fill colours of the two soil behaviours in the schematic (theme-dependent,
# since a light sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"granular": "#E3C98F", "cohesive": "#A7B8A0"},
    "dark": {"granular": "#8A7250", "cohesive": "#5E6E58"},
}

DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Raft on soft clay",
        "analyst": "",
    },
    "foundation": {
        "shape": "rectangle",
        "B": 8.0,                  # width, or diameter of a circle [m]
        "L": 16.0,                 # length of a rectangle [m]
        "Df": 1.5,                 # depth of the foundation base [m]
        "q": 100.0,                # applied (gross) bearing pressure [kPa]
        "net_pressure": True,      # deduct the overburden removed by the excavation
    },
    "groundwater": {
        "depth": 2.0,              # below ground surface [m]
        "gamma_water": 9.81,       # [kN/m³]
    },
    # Layers from the ground surface down. E [MPa] is the drained modulus of
    # a granular layer and the undrained modulus of a cohesive one; cv in
    # m²/year; OCR = σ'p / σ'v0.
    "soil_profile": [
        {"name": "Fill", "thickness": 1.5, "behaviour": "granular", "gamma": 18.0,
         "gamma_sat": 19.0, "E": 10.0, "nu": 0.30, "Cc": 0.0, "Cr": 0.0, "e0": 0.6,
         "OCR": 1.0, "cv": 0.0, "Calpha": 0.0, "drainage": "double"},
        {"name": "Medium dense sand", "thickness": 3.5, "behaviour": "granular",
         "gamma": 18.5, "gamma_sat": 20.0, "E": 25.0, "nu": 0.30, "Cc": 0.0, "Cr": 0.0,
         "e0": 0.6, "OCR": 1.0, "cv": 0.0, "Calpha": 0.0, "drainage": "double"},
        {"name": "Soft clay", "thickness": 6.0, "behaviour": "cohesive", "gamma": 17.0,
         "gamma_sat": 17.5, "E": 6.0, "nu": 0.50, "Cc": 0.32, "Cr": 0.05, "e0": 1.05,
         "OCR": 1.3, "cv": 1.5, "Calpha": 0.010, "drainage": "double"},
        {"name": "Dense sand", "thickness": 10.0, "behaviour": "granular", "gamma": 19.5,
         "gamma_sat": 21.0, "E": 60.0, "nu": 0.30, "Cc": 0.0, "Cr": 0.0, "e0": 0.5,
         "OCR": 1.0, "cv": 0.0, "Calpha": 0.0, "drainage": "double"},
    ],
    "options": {
        "stress_method": "boussinesq",
        "immediate_method": "elastic",
        "rigidity": "flexible",
        "sublayer": 0.25,          # thickness of the calculation sublayers [m]
        "depth_ratio": 0.10,       # influence depth where Δσ = ratio · σ'v0 (0: whole profile)
        "design_life": 50.0,       # years, for secondary compression and creep
        "creep": True,             # Schmertmann's time factor C2
    },
    "criteria": {
        "s_allow": 150.0,          # allowable total settlement [mm] (0: no check)
        "distortion_allow": 500.0,  # allowable angular distortion 1 / x (0: no check)
    },
}
