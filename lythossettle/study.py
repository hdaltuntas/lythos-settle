"""
Parametric and probabilistic (reliability) studies for Lythos Settle.

A study is defined by a list of variables, each addressing one input of the
project configuration by a dotted path (``foundation.q``,
``soil_profile.2.Cc``, ``groundwater.depth`` …), and either

* a **range** (min, max)                      -> parametric / sensitivity, or
* a **distribution** (normal, lognormal, uniform; mean, CoV) -> reliability.

Sampling methods
    oat   one-at-a-time sweep over each range variable (the others at their
          project values)
    lhs   Latin hypercube (ranges as uniform distributions)
    mc    plain Monte Carlo

Every sample is a complete settlement analysis — a few milliseconds — so the
runner works in one thread, reporting progress and honouring cancellation
between samples. Post-processing gives summary statistics, Spearman rank
sensitivities and, for the two criteria, the probability of exceeding them
with a 95 % confidence interval and the corresponding reliability index.
"""

from __future__ import annotations

import copy
import csv
import math
from statistics import NormalDist
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .engine import SettlementAnalysis
from .summary import longest_t90

DISTRIBUTIONS = ["normal", "lognormal", "uniform"]
METHODS = ["oat", "lhs", "mc"]

#: Outputs collected for every sample: (key, unit)
OUTPUTS = [("s_total", "mm"), ("s_imm", "mm"), ("s_cons", "mm"), ("s_sec", "mm"),
           ("beta", "‰"), ("t90", "yr")]

#: Criteria: (key, output, capacity key); exceeded when output > capacity
LIMIT_STATES = [("ls_settlement", "s_total", "s_allow"),
                ("ls_distortion", "beta", "beta_allow")]

#: Soil inputs a study may vary, and the ones that only mean anything in clay
SOIL_KEYS = ["thickness", "gamma", "gamma_sat", "E", "nu"]
CLAY_KEYS = ["Cc", "Cr", "e0", "OCR", "cv", "Calpha"]

_NORMAL = NormalDist()


def available_variables(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(path, group) pairs of the inputs that can be varied for this project."""
    out = [("foundation.q", "foundation"), ("foundation.B", "foundation")]
    if cfg.get("foundation", {}).get("shape", "rectangle") == "rectangle":
        out.append(("foundation.L", "foundation"))
    out += [("foundation.Df", "foundation"), ("groundwater.depth", "groundwater")]
    for i, layer in enumerate(cfg.get("soil_profile", [])):
        keys = SOIL_KEYS + (CLAY_KEYS if layer.get("behaviour") == "cohesive" else [])
        out += [(f"soil_profile.{i}.{key}", layer.get("name", f"layer {i + 1}")) for key in keys]
    return out


def pretty_label(cfg: Dict[str, Any], path: str, L: Dict[str, str]) -> str:
    """A readable variable name, e.g. 'Soft clay · Cc' or 'Foundation · q'."""
    parts = path.split(".")
    name = L.get(f"var_{parts[-1]}", parts[-1])
    if parts[0] == "soil_profile":
        index = int(parts[1])
        layers = cfg.get("soil_profile", [])
        layer = layers[index].get("name", f"{index + 1}") if index < len(layers) else parts[1]
        return f"{layer} · {name}"
    group = {"foundation": "grp_foundation", "groundwater": "grp_water"}.get(parts[0])
    return f"{L.get(group, parts[0])} · {name}" if group else name


def get_value(cfg: Dict[str, Any], path: str) -> Any:
    node = cfg
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def set_value(cfg: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    if isinstance(node, list):
        node[int(parts[-1])] = value
    else:
        node[parts[-1]] = value


class StudyVariable:
    """One varied input. mode = 'range' (min / max) or 'dist' (a distribution)."""

    def __init__(self, path: str, mode: str = "range", vmin: float = 0.0, vmax: float = 1.0,
                 dist: str = "normal", mean: float = 0.0, cov: float = 0.1,
                 n_points: int = 5, label: Optional[str] = None):
        self.path, self.mode = path, mode
        self.vmin, self.vmax = float(vmin), float(vmax)
        self.dist, self.mean, self.cov = dist, float(mean), float(cov)
        self.n_points = max(2, int(n_points))
        self.label = label or path
        self.base: Optional[float] = None
        if mode not in ("range", "dist"):
            raise ValueError(f"{self.label}: the mode must be 'range' or 'dist'")
        if mode == "range" and self.vmax <= self.vmin:
            raise ValueError(f"{self.label}: max must be greater than min")
        if mode == "dist":
            if dist not in DISTRIBUTIONS:
                raise ValueError(f"{self.label}: unknown distribution '{dist}'")
            if self.cov < 0:
                raise ValueError(f"{self.label}: the CoV cannot be negative")
            if dist == "lognormal" and self.mean <= 0:
                raise ValueError(f"{self.label}: a lognormal variable needs a positive mean")

    def ppf(self, u: np.ndarray) -> np.ndarray:
        """Values at the probabilities u (0 < u < 1)."""
        u = np.clip(np.asarray(u, dtype=float), 1e-12, 1 - 1e-12)
        if self.mode == "range":
            return self.vmin + u * (self.vmax - self.vmin)
        sd = abs(self.mean) * self.cov
        if self.dist == "uniform":
            half = math.sqrt(3.0) * sd
            return self.mean - half + 2.0 * half * u
        z = np.array([_NORMAL.inv_cdf(float(p)) for p in u.ravel()]).reshape(u.shape)
        if self.dist == "normal":
            return self.mean + sd * z
        s_ln = math.sqrt(math.log(1.0 + self.cov ** 2))
        m_ln = math.log(self.mean) - 0.5 * s_ln ** 2
        return np.exp(m_ln + s_ln * z)

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "label": self.label, "mode": self.mode, "min": self.vmin,
                "max": self.vmax, "dist": self.dist, "mean": self.mean, "cov": self.cov,
                "n_points": self.n_points}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StudyVariable":
        def num(key, default):
            value = d.get(key, default)
            return float(default) if value is None or value == "" else float(value)

        return cls(str(d.get("path", "")), str(d.get("mode", "range")), num("min", 0.0),
                   num("max", 1.0), str(d.get("dist", "normal")), num("mean", 0.0),
                   num("cov", 0.1), int(num("n_points", 5)), d.get("label"))


def sample(variables: Sequence[StudyVariable], method: str, n: int = 100,
           seed: int = 0) -> List[Dict[str, Any]]:
    """The samples: each a {path: value} dict, plus '_varied' for a sweep."""
    rng = np.random.default_rng(seed)
    if method == "oat":
        rows = []
        for var in variables:
            if var.mode != "range":
                continue
            for value in np.linspace(var.vmin, var.vmax, var.n_points):
                rows.append({var.path: float(value), "_varied": var.path})
        return rows
    n = max(1, int(n))
    columns = {}
    for var in variables:
        if method == "lhs":
            u = (rng.permutation(n) + rng.random(n)) / n
        else:
            u = rng.random(n)
        columns[var.path] = var.ppf(u)
    return [{path: float(values[i]) for path, values in columns.items()} for i in range(n)]


def evaluate(base_cfg: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
    """Analyses one sample; the outputs, or the reason it failed."""
    cfg = copy.deepcopy(base_cfg)
    row: Dict[str, Any] = {k: v for k, v in values.items()}
    try:
        for path, value in values.items():
            if not path.startswith("_"):
                set_value(cfg, path, value)
        analysis = SettlementAnalysis(cfg)
        res = analysis.run()
        gov = res["points"][res["governing"]]
        row.update(s_total=gov["total"], s_imm=gov["immediate"], s_cons=gov["consolidation"],
                   s_sec=gov["secondary"],
                   beta=res["distortion"] * 1000.0 if res["distortion"] is not None else None,
                   t90=longest_t90(res), error="")
    except Exception as exc:                    # an impossible sample, e.g. E < 0
        row["error"] = str(exc)
    return row


class Study:
    """A parametric / reliability study over one project."""

    def __init__(self, base_cfg: Dict[str, Any], variables: Sequence[StudyVariable],
                 method: str = "lhs", n: int = 200, seed: int = 0):
        if method not in METHODS:
            raise ValueError(f"unknown sampling method: {method}")
        self.base_cfg = copy.deepcopy(base_cfg)
        self.variables = list(variables)
        self.method, self.n, self.seed = method, int(n), int(seed)
        paths = {path for path, _ in available_variables(self.base_cfg)}
        for var in self.variables:
            if var.path not in paths:
                raise ValueError(f"{var.label}: not an input this project has")
            var.base = float(get_value(self.base_cfg, var.path))
        if method == "oat" and not any(v.mode == "range" for v in self.variables):
            raise ValueError("a one-at-a-time sweep needs at least one range variable")
        criteria = self.base_cfg.get("criteria", {})
        s_allow = float(criteria.get("s_allow", 0) or 0)
        d_allow = float(criteria.get("distortion_allow", 0) or 0)
        self.capacity = {"s_allow": s_allow if s_allow > 0 else None,
                         "beta_allow": 1000.0 / d_allow if d_allow > 0 else None}
        self.rows: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}

    @property
    def paths(self) -> List[str]:
        return [v.path for v in self.variables]

    def run(self, progress: Optional[Callable[[int, int], None]] = None,
            is_cancelled: Optional[Callable[[], bool]] = None) -> None:
        samples = sample(self.variables, self.method, self.n, self.seed)
        rows = []
        total = len(samples)
        for i, values in enumerate(samples):
            if is_cancelled and is_cancelled():
                break
            rows.append(evaluate(self.base_cfg, values))
            if progress:
                progress(i + 1, total)
        self.rows = rows
        self.summary = summarize(self)


# ----------------------------------------------------------------------
# post-processing
# ----------------------------------------------------------------------

def _column(rows: List[Dict[str, Any]], key: str) -> np.ndarray:
    return np.array([np.nan if r.get(key) is None else float(r.get(key)) for r in rows])


def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    ranks[order] = np.arange(len(x))
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx, ry = _ranks(x[ok]), _ranks(y[ok])
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def reliability(values: np.ndarray, capacity: float) -> Dict[str, float]:
    """P(value > capacity) with a Wilson 95 % interval and β = −Φ⁻¹(P)."""
    values = values[np.isfinite(values)]
    n = len(values)
    k = int(np.sum(values > capacity))
    pf = k / n if n else float("nan")
    z = 1.959964
    if n:
        centre = (pf + z * z / (2 * n)) / (1 + z * z / n)
        half = z * math.sqrt(pf * (1 - pf) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        lo, hi = max(0.0, centre - half), min(1.0, centre + half)
    else:
        lo = hi = float("nan")
    if not n:
        beta = float("nan")
    elif pf <= 0:
        beta = float("inf")
    elif pf >= 1:
        beta = float("-inf")
    else:
        beta = -_NORMAL.inv_cdf(pf)
    return {"n": n, "n_fail": k, "pf": pf, "pf_lo": lo, "pf_hi": hi, "beta": beta,
            "capacity": capacity}


def summarize(study: Study) -> Dict[str, Any]:
    ok = [r for r in study.rows if not r.get("error")]
    out: Dict[str, Any] = {"n_total": len(study.rows), "n_ok": len(ok), "stats": {},
                           "reliability": {}, "spearman": {}}
    for key, _ in OUTPUTS:
        values = _column(ok, key)
        values = values[np.isfinite(values)]
        if values.size:
            std = float(values.std(ddof=1)) if values.size > 1 else 0.0
            if std <= 1e-9 * max(abs(float(values.mean())), 1.0):
                std = 0.0                       # a constant output, not rounding noise
            out["stats"][key] = {"n": int(values.size), "mean": float(values.mean()), "std": std,
                                 "p5": float(np.percentile(values, 5)),
                                 "p50": float(np.percentile(values, 50)),
                                 "p95": float(np.percentile(values, 95))}
    if study.method != "oat":
        for name, output, cap_key in LIMIT_STATES:
            capacity = study.capacity.get(cap_key)
            values = _column(ok, output)
            if capacity is not None and np.isfinite(values).any():
                out["reliability"][name] = reliability(values, capacity)
    for key, _ in OUTPUTS:
        rho = {}
        for var in study.variables:
            # a sweep varies one input at a time: only its own rows say anything about it
            rows = ok if study.method != "oat" else [r for r in ok if r.get("_varied") == var.path]
            value = spearman(_column(rows, var.path), _column(rows, key))
            if math.isfinite(value):
                rho[var.path] = value
        if rho:
            out["spearman"][key] = rho
    return out


def table_columns(study: Study) -> List[str]:
    """Columns of the sampled table: the variables, the outputs, the error."""
    return study.paths + [key for key, _ in OUTPUTS] + ["error"]


def to_csv(study: Study, path: str) -> None:
    columns = table_columns(study)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in study.rows:
            writer.writerow(["" if row.get(c) is None else row.get(c) for c in columns])


def to_xlsx(study: Study, path: str) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is not installed (pip install openpyxl).") from exc
    columns = table_columns(study)
    book = Workbook()
    sheet = book.active
    sheet.title = "samples"
    sheet.append(columns)
    for row in study.rows:
        values = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float) and not math.isfinite(value):
                value = None
            values.append(value)
        sheet.append(values)
    book.save(path)
