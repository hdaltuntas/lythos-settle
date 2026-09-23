"""
Input schema and readers for Lythos Settle.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``B``, ``water_depth``, ``depth_ratio`` …) are the ones
the interface uses; the nested keys of the configuration
(``foundation.B``, ``groundwater.depth`` …) are the ones the engine and the
``.settle`` project files use. `to_config()` and `from_config()` convert
between the two.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .config import (
    BEHAVIOURS,
    DEFAULT_CONFIG,
    DRAINAGE,
    IMMEDIATE_METHODS,
    RIGIDITY,
    SHAPES,
    STRESS_METHODS,
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "lythos-settle"
FILE_VERSION = "0.1"


def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --------------------------------------------------------------------------- #
#  Schema data structures
# --------------------------------------------------------------------------- #

@dataclass
class Field:
    """One input field."""
    key: str
    label: str
    kind: str = "number"                     # number | text | check | select
    default: Any = 0.0
    unit: str = ""
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    decimals: int = 2
    options: List[Dict[str, str]] = field(default_factory=list)
    shapes: List[str] = field(default_factory=list)       # shown only for these shapes

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        return {k: v for k, v in asdict(self).items()
                if k in keep or v not in ("", None, [], 0.0)}


@dataclass
class Group:
    """A titled set of fields."""
    title: str
    fields: List[Field]
    note: str = ""
    shapes: List[str] = field(default_factory=list)       # shown only for these shapes

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        if self.shapes:
            d["shapes"] = list(self.shapes)
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec)


def _check(key, label, default=False):
    return Field(key, label, "check", default)


def _select(key, label, default, options):
    return Field(key, label, "select", default,
                 options=[{"value": v, "label": t} for v, t in options])


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _only(shapes: List[str], item):
    """Shows a field or a group only for some foundation shapes."""
    item.shapes = list(shapes)
    return item


#: The shapes that are foundations, as against an embankment
FOOTINGS = [s for s in SHAPES if s != "embankment"]


def _choices(lang: str, prefix: str, values: List[str]):
    return [(value, _t(lang, f"{prefix}_{value}")) for value in values]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [Group(_t(lang, "group_project"), [
        _text("title", _t(lang, "title_label"), info["title"]),
        _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
    ])]


def foundation_groups(lang: str = "en") -> List[Group]:
    f = DEFAULT_CONFIG["foundation"]
    e = DEFAULT_CONFIG["embankment"]
    w = DEFAULT_CONFIG["groundwater"]
    return [
        Group(_t(lang, "group_foundation"), [
            _select("shape", _t(lang, "shape_label"), f["shape"], _choices(lang, "shape", SHAPES)),
            _only(FOOTINGS, _num("B", _t(lang, "B_label"), f["B"], 0.1, 500, "m", 2, 0.1)),
            _only(["rectangle"], _num("L", _t(lang, "L_label"), f["L"], 0.1, 500, "m", 2, 0.1)),
            _only(FOOTINGS, _num("Df", _t(lang, "Df_label"), f["Df"], 0, 50, "m", 2, 0.1)),
            _only(FOOTINGS, _num("q", _t(lang, "q_label"), f["q"], 0, 5000, "kPa", 1, 5)),
            _only(FOOTINGS, _check("net_pressure", _t(lang, "net_label"), f["net_pressure"])),
        ]),
        _only(["embankment"], Group(_t(lang, "group_embankment"), [
            _num("emb_crest", _t(lang, "emb_crest_label"), e["crest"], 0, 500, "m", 2, 0.5),
            _num("emb_height", _t(lang, "emb_height_label"), e["height"], 0.1, 100, "m", 2, 0.1),
            _num("emb_slope_left", _t(lang, "emb_slope_left_label"), e["slope_left"], 1, 90,
                 "°", 2, 0.5),
            _num("emb_slope_right", _t(lang, "emb_slope_right_label"), e["slope_right"], 1, 90,
                 "°", 2, 0.5),
            _num("emb_gamma", _t(lang, "emb_gamma_label"), e["gamma"], 1, 30, "kN/m³", 1, 0.5),
        ], note=_t(lang, "emb_note"))),
        Group(_t(lang, "group_water"), [
            _num("water_depth", _t(lang, "water_depth_label"), w["depth"], 0, 500, "m", 2, 0.1),
            _num("gamma_water", _t(lang, "gamma_w_label"), w["gamma_water"], 9, 11, "kN/m³",
                 2, 0.01),
        ]),
    ]


def option_groups(lang: str = "en") -> List[Group]:
    o = DEFAULT_CONFIG["options"]
    c = DEFAULT_CONFIG["criteria"]
    return [
        Group(_t(lang, "group_options"), [
            _select("stress_method", _t(lang, "stress_method_label"), o["stress_method"],
                    _choices(lang, "stress", STRESS_METHODS)),
            _select("immediate_method", _t(lang, "immediate_method_label"),
                    o["immediate_method"], _choices(lang, "immediate", IMMEDIATE_METHODS)),
            _only(FOOTINGS, _select("rigidity", _t(lang, "rigidity_label"), o["rigidity"],
                                    _choices(lang, "rigidity", RIGIDITY))),
            _num("sublayer", _t(lang, "sublayer_label"), o["sublayer"], 0.05, 5, "m", 2, 0.05),
            _num("depth_ratio", _t(lang, "depth_ratio_label"), o["depth_ratio"], 0, 1, "", 2,
                 0.05),
            _num("design_life", _t(lang, "design_life_label"), o["design_life"], 0.1, 500,
                 "yr" if lang == "en" else "yıl", 1, 5),
            _check("creep", _t(lang, "creep_label"), o["creep"]),
        ], note=_t(lang, "options_note")),
        Group(_t(lang, "group_criteria"), [
            _num("s_allow", _t(lang, "s_allow_label"), c["s_allow"], 0, 2000, "mm", 1, 5),
            _num("distortion_allow", _t(lang, "distortion_label"), c["distortion_allow"], 0,
                 5000, "", 0, 50),
        ], note=_t(lang, "criteria_note")),
    ]


def study_groups(lang: str = "en") -> List[Group]:
    from .study import METHODS
    return [Group(_t(lang, "group_study"), [
        _select("study_method", _t(lang, "study_method"), "lhs",
                [(m, _t(lang, f"method_{m}")) for m in METHODS]),
        _num("study_n", _t(lang, "study_n"), 500, 3, 100000, "", 0, 50),
        _num("study_seed", _t(lang, "study_seed"), 0, 0, 10 ** 6, "", 0, 1),
    ], note=_t(lang, "study_note"))]


# --------------------------------------------------------------------------- #
#  Tables: soil layers, study variables
# --------------------------------------------------------------------------- #

SOIL_NUMBERS = ["thickness", "gamma", "gamma_sat", "E", "nu", "Cc", "Cr", "e0", "OCR", "cv",
                "Calpha"]


def soil_columns(lang: str = "en") -> List[dict]:
    """Columns of the soil profile table."""
    def number(key):
        return {"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}

    def select(key, prefix, values):
        return {"key": key, "label": _t(lang, f"col_{key}"), "kind": "select",
                "options": [{"value": v, "label": _t(lang, f"{prefix}_{v}")} for v in values]}

    return ([{"key": "name", "label": _t(lang, "col_name"), "kind": "text"},
             number("thickness"), select("behaviour", "behaviour", BEHAVIOURS)]
            + [number(key) for key in SOIL_NUMBERS[1:]]
            + [select("drainage", "drainage", DRAINAGE)])


def study_columns(lang: str = "en") -> List[dict]:
    """Columns of the study variable table."""
    from .study import DISTRIBUTIONS
    return [
        {"key": "path", "label": _t(lang, "col_param"), "kind": "select", "options": []},
        {"key": "mode", "label": _t(lang, "col_mode"), "kind": "select",
         "options": [{"value": "range", "label": _t(lang, "mode_range")},
                     {"value": "dist", "label": _t(lang, "mode_dist")}]},
        {"key": "min", "label": _t(lang, "col_min"), "kind": "number"},
        {"key": "max", "label": _t(lang, "col_max"), "kind": "number"},
        {"key": "dist", "label": _t(lang, "col_dist"), "kind": "select",
         "options": [{"value": d, "label": _t(lang, f"dist_{d}")} for d in DISTRIBUTIONS]},
        {"key": "mean", "label": _t(lang, "col_mean"), "kind": "number"},
        {"key": "cov", "label": _t(lang, "col_cov"), "kind": "number"},
        {"key": "n_points", "label": _t(lang, "col_points"), "kind": "number"},
    ]


def default_soil_rows() -> List[dict]:
    return [dict(layer) for layer in DEFAULT_CONFIG["soil_profile"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "foundation": {"groups": [g.to_dict() for g in foundation_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "study": {"groups": [g.to_dict() for g in study_groups(lang)]},
        "soil": {"columns": soil_columns(lang), "rows": default_soil_rows(),
                 "note": _t(lang, "soil_note")},
        "study_vars": {"columns": study_columns(lang)},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return (project_groups(lang) + foundation_groups(lang) + option_groups(lang)
            + study_groups(lang))


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["soil_profile"] = default_soil_rows()
    values["study_variables"] = []
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #

def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    return float(v)


def _b(values: dict, key: str, default: bool = False) -> bool:
    v = values.get(key, default)
    return bool(default if v is None or v == "" else v)


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_soil_profile(values: dict) -> List[dict]:
    """Soil layers from the table; rows without a usable thickness are dropped."""
    base = DEFAULT_CONFIG["soil_profile"][0]
    layers = []
    for row in values.get("soil_profile") or []:
        try:
            thickness = float(row.get("thickness"))
        except (TypeError, ValueError):
            continue
        if thickness <= 0:
            continue
        layer = {"name": str(row.get("name") or "").strip() or "Layer",
                 "behaviour": _s(row, "behaviour", "granular", BEHAVIOURS),
                 "drainage": _s(row, "drainage", "double", DRAINAGE)}
        for key in SOIL_NUMBERS:
            layer[key] = _f(row, key, base[key])
        layer["thickness"] = thickness
        layers.append(layer)
    return layers


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    d = DEFAULT_CONFIG
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    cfg["foundation"] = {
        "shape": _s(values, "shape", d["foundation"]["shape"], SHAPES),
        "B": _f(values, "B", d["foundation"]["B"]),
        "L": _f(values, "L", d["foundation"]["L"]),
        "Df": _f(values, "Df", d["foundation"]["Df"]),
        "q": _f(values, "q", d["foundation"]["q"]),
        "net_pressure": _b(values, "net_pressure", d["foundation"]["net_pressure"]),
    }
    e = d["embankment"]
    cfg["embankment"] = {key: _f(values, f"emb_{key}", e[key]) for key in e}
    cfg["groundwater"] = {"depth": _f(values, "water_depth", d["groundwater"]["depth"]),
                          "gamma_water": _f(values, "gamma_water",
                                            d["groundwater"]["gamma_water"])}
    cfg["soil_profile"] = read_soil_profile(values)
    o = d["options"]
    cfg["options"] = {
        "stress_method": _s(values, "stress_method", o["stress_method"], STRESS_METHODS),
        "immediate_method": _s(values, "immediate_method", o["immediate_method"],
                               IMMEDIATE_METHODS),
        "rigidity": _s(values, "rigidity", o["rigidity"], RIGIDITY),
        "sublayer": _f(values, "sublayer", o["sublayer"]),
        "depth_ratio": _f(values, "depth_ratio", o["depth_ratio"]),
        "design_life": _f(values, "design_life", o["design_life"]),
        "creep": _b(values, "creep", o["creep"]),
    }
    cfg["criteria"] = {"s_allow": _f(values, "s_allow", d["criteria"]["s_allow"]),
                       "distortion_allow": _f(values, "distortion_allow",
                                              d["criteria"]["distortion_allow"])}
    return cfg


#: Flat key <- (section, key) of the configuration
_MAP = [("title", "project_info", "title"), ("analyst", "project_info", "analyst")] + \
    [(k, "foundation", k) for k in ("shape", "B", "L", "Df", "q", "net_pressure")] + \
    [(f"emb_{k}", "embankment", k) for k in DEFAULT_CONFIG["embankment"]] + \
    [("water_depth", "groundwater", "depth"), ("gamma_water", "groundwater", "gamma_water")] + \
    [(k, "options", k) for k in ("stress_method", "immediate_method", "rigidity", "sublayer",
                                 "depth_ratio", "design_life", "creep")] + \
    [(k, "criteria", k) for k in ("s_allow", "distortion_allow")]


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.settle` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, section, key in _MAP:
        if key in (cfg.get(section) or {}):
            values[flat] = cfg[section][key]
    if cfg.get("soil_profile"):
        layer_defaults = DEFAULT_CONFIG["soil_profile"][0]
        values["soil_profile"] = [{**layer_defaults, **layer} for layer in cfg["soil_profile"]
                                  if isinstance(layer, dict)]
    study = cfg.get("study") or {}
    for src, dst in (("method", "study_method"), ("n", "study_n"), ("seed", "study_seed")):
        if src in study:
            values[dst] = study[src]
    if "variables" in study:
        values["study_variables"] = [dict(spec) for spec in study["variables"]]
    return values


def study_spec(values: dict) -> Dict[str, Any]:
    """The study block of a project file: options plus the variable table."""
    from .study import METHODS
    return {
        "method": _s(values, "study_method", "lhs", METHODS),
        "n": int(_f(values, "study_n", 500)),
        "seed": int(_f(values, "study_seed", 0)),
        "variables": [dict(spec) for spec in values.get("study_variables") or []],
    }


def project_file(values: dict) -> Dict[str, Any]:
    """What `Save` writes: the configuration plus the study definition."""
    cfg = to_config(values)
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **cfg, "study": study_spec(values)}


def study_variables(values: dict):
    """The study variables as `study.StudyVariable` objects."""
    from .study import StudyVariable
    return [StudyVariable.from_dict(spec) for spec in values.get("study_variables") or []]


def variable_choices(values: dict, lang: str = "en") -> List[dict]:
    """Every input a study may vary, with a readable label and its project value."""
    from .study import available_variables, get_value, pretty_label
    cfg = to_config(values)
    L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return [{"value": path, "label": pretty_label(cfg, path, L),
             "base": float(get_value(cfg, path))}
            for path, _ in available_variables(cfg)]
