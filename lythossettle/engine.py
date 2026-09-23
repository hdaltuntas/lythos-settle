"""
The settlement analysis of a shallow foundation on a layered soil profile.

Given the foundation (shape, size, depth, bearing pressure), the groundwater
level and the soil layers, `SettlementAnalysis.run()` works out

    * the in-situ stresses σv0, u0, σ'v0 and, for clays, σ'p = OCR·σ'v0
    * the net pressure and the vertical stress increase Δσ beneath it
      (Boussinesq or 2:1) at the centre, the characteristic point, the
      middle of the long edge and the corner
    * the influence depth, where Δσ falls to a fraction of σ'v0
    * immediate settlement: layered elastic (Steinbrenner) in every layer, or
      Schmertmann (1978) in the granular layers and elastic in the cohesive
    * primary consolidation settlement of the cohesive layers from Cc, Cr,
      e0 and σ'p, sublayer by sublayer
    * secondary compression up to the design life, from Cα
    * the time–settlement curve (Terzaghi, each clay layer draining on its own)
    * angular distortion between the centre and the edge, and the checks
      against the allowable total settlement and distortion

The profile is split into thin sublayers below the foundation base; every
quantity is evaluated at the sublayer mid-depths, so the per-depth results
feed the figures directly.

Input problems are raised as `SettleError`, which carries a translation key,
so the interface can say what is wrong in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Tuple

import numpy as np

from . import consolidation as cons
from . import stress
from .config import (
    BEHAVIOURS,
    DEFAULT_CONFIG,
    DRAINAGE,
    IMMEDIATE_METHODS,
    RIGIDITY,
    SHAPES,
    STRESS_METHODS,
)

#: The points at which the settlement is evaluated, in display order
POINT_KEYS = ["center", "char", "edge", "corner", "shoulder", "midslope", "toe"]

#: Points of the settlement profile across the section
PROFILE_POINTS = 61

#: Distance of the characteristic point from the centre, as a fraction of the
#: half-width: 0.74 for a rectangle or a strip, 0.845 for a circle (Grasshoff)
CHAR_RECT = 0.74
CHAR_CIRCLE = 0.845

#: Number of points of the time–settlement curve
TIME_POINTS = 240

#: Earliest time on the time–settlement curve [years] (about nine hours)
T_MIN = 1e-3


class SettleError(ValueError):
    """An input the analysis cannot work with; `key` names the message."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        from .i18n import TRANSLATIONS
        super().__init__(TRANSLATIONS["en"].get(key, key).format(**params))


def _message(key: str, **params) -> Tuple[str, Dict[str, Any]]:
    return key, params


# --------------------------------------------------------------------------- #
#  Soil profile
# --------------------------------------------------------------------------- #

class Profile:
    """The layered soil column and its in-situ stresses."""

    def __init__(self, layers: List[dict], water_depth: float, gamma_w: float):
        self.layers = layers
        self.zw = water_depth
        self.gw = gamma_w
        top = 0.0
        for layer in layers:
            layer["top"] = top
            layer["bottom"] = top + layer["thickness"]
            top = layer["bottom"]
        self.depth = top

    def layer_index(self, z) -> np.ndarray:
        """Index of the layer at depth z (the last layer below the profile)."""
        bottoms = np.array([layer["bottom"] for layer in self.layers])
        index = np.searchsorted(bottoms, np.asarray(z, dtype=float), side="right")
        return np.minimum(index, len(self.layers) - 1)

    def total_stress(self, z) -> np.ndarray:
        """σv0 at depth z; the last layer is taken as continuing below the profile."""
        z = np.atleast_1d(np.asarray(z, dtype=float))
        sigma = np.zeros_like(z)
        for i, layer in enumerate(self.layers):
            top = layer["top"]
            bottom = layer["bottom"] if i < len(self.layers) - 1 else np.inf
            seg_bot = np.clip(z, top, bottom)
            dry = np.clip(np.minimum(seg_bot, self.zw) - top, 0.0, None)
            wet = np.clip(seg_bot - max(top, self.zw), 0.0, None)
            sigma += layer["gamma"] * dry + layer["gamma_sat"] * wet
        return sigma

    def pore_pressure(self, z) -> np.ndarray:
        z = np.atleast_1d(np.asarray(z, dtype=float))
        return self.gw * np.maximum(z - self.zw, 0.0)

    def effective_stress(self, z) -> np.ndarray:
        return self.total_stress(z) - self.pore_pressure(z)


# --------------------------------------------------------------------------- #
#  The analysis
# --------------------------------------------------------------------------- #

def _num(d: dict, key: str, default: float) -> float:
    value = d.get(key, default)
    if value is None or value == "":
        return float(default)
    return float(value)


class SettlementAnalysis:
    """Settlement of one shallow foundation. Build it, then call `run()`."""

    def __init__(self, config: Dict[str, Any]):
        self.config = copy.deepcopy(config)
        self.warnings: List[Tuple[str, Dict[str, Any]]] = []
        self._read()
        self.results: Dict[str, Any] = {}

    # ------------------------------------------------------------------ input
    def _read(self) -> None:
        cfg = self.config
        base = DEFAULT_CONFIG
        f = {**base["foundation"], **cfg.get("foundation", {})}
        o = {**base["options"], **cfg.get("options", {})}
        c = {**base["criteria"], **cfg.get("criteria", {})}
        w = {**base["groundwater"], **cfg.get("groundwater", {})}

        self.shape = f["shape"] if f["shape"] in SHAPES else "rectangle"
        self.embankment = None
        if self.shape == "embankment":
            self._read_embankment({**base["embankment"], **cfg.get("embankment", {})})
        else:
            self.B = _num(f, "B", 1.0)
            self.L = _num(f, "L", self.B) if self.shape == "rectangle" else self.B
            self.Df = _num(f, "Df", 0.0)
            self.q = _num(f, "q", 0.0)
            self.net_pressure = bool(f.get("net_pressure", True))
            if self.B <= 0 or (self.shape == "rectangle" and self.L <= 0):
                raise SettleError("err_dimensions")
            if self.q < 0:
                raise SettleError("err_pressure")
            if self.Df < 0:
                raise SettleError("err_depth")
            if self.shape == "rectangle" and self.L < self.B:
                self.B, self.L = self.L, self.B
                self.warnings.append(_message("warn_swapped"))

        self.stress_method = (o["stress_method"] if o["stress_method"] in STRESS_METHODS
                              else STRESS_METHODS[0])
        self.immediate_method = (o["immediate_method"] if o["immediate_method"]
                                 in IMMEDIATE_METHODS else IMMEDIATE_METHODS[0])
        self.rigidity = o["rigidity"] if o["rigidity"] in RIGIDITY else RIGIDITY[0]
        if self.embankment:
            # A fill is as flexible as the ground under it, and Schmertmann's
            # diagram is for footings: an embankment is analysed elastically.
            self.rigidity = "flexible"
            if self.immediate_method == "schmertmann":
                self.immediate_method = "elastic"
                self.warnings.append(_message("warn_emb_schmertmann"))
        self.sublayer = _num(o, "sublayer", 0.25)
        self.depth_ratio = max(0.0, _num(o, "depth_ratio", 0.1))
        self.design_life = _num(o, "design_life", 50.0)
        self.creep = bool(o.get("creep", True))
        if self.sublayer <= 0:
            raise SettleError("err_sublayer")
        if self.design_life <= 0:
            raise SettleError("err_life")

        self.s_allow = max(0.0, _num(c, "s_allow", 0.0))
        self.distortion_allow = max(0.0, _num(c, "distortion_allow", 0.0))

        gamma_w = _num(w, "gamma_water", 9.81)
        layers = []
        for row in cfg.get("soil_profile") or []:
            layer = {**base["soil_profile"][0], **row}
            thickness = _num(layer, "thickness", 0.0)
            if thickness <= 0:
                continue
            layers.append(self._read_layer(layer, thickness, gamma_w))
        if not layers:
            raise SettleError("err_no_layers")
        self.profile = Profile(layers, _num(w, "depth", 0.0), gamma_w)
        if self.Df >= self.profile.depth:
            raise SettleError("err_depth")
        for layer in layers:
            if layer["bottom"] <= self.Df:
                continue
            if layer["E"] <= 0:
                raise SettleError("err_layer_E", name=layer["name"])

    def _read_embankment(self, e: dict) -> None:
        """An embankment: a trapezoidal fill on the ground surface."""
        crest, height = _num(e, "crest", 0.0), _num(e, "height", 0.0)
        left, right = _num(e, "slope_left", 30.0), _num(e, "slope_right", 30.0)
        gamma = _num(e, "gamma", 20.0)
        if height <= 0 or crest < 0 or gamma <= 0 or not (0 < left <= 90 and 0 < right <= 90):
            raise SettleError("err_embankment")
        run_l, run_r = stress.slope_run(height, left), stress.slope_run(height, right)
        if crest + run_l + run_r <= 0:
            raise SettleError("err_embankment")
        self.embankment = {"crest": crest, "height": height, "slope_left": left,
                           "slope_right": right, "gamma": gamma, "run_left": run_l,
                           "run_right": run_r}
        # the fill sits on the ground surface and loads it with γ·H at most
        self.Df, self.q, self.net_pressure = 0.0, gamma * height, False
        self.B = self.L = crest + run_l + run_r          # width at the base

    def _read_layer(self, row: dict, thickness: float, gamma_w: float) -> dict:
        name = str(row.get("name") or "").strip() or "Layer"
        behaviour = row.get("behaviour") if row.get("behaviour") in BEHAVIOURS else "granular"
        layer = {
            "name": name,
            "thickness": thickness,
            "behaviour": behaviour,
            "gamma": _num(row, "gamma", 18.0),
            "gamma_sat": _num(row, "gamma_sat", 19.0),
            "E": _num(row, "E", 10.0) * 1000.0,          # MPa -> kPa
            "E_MPa": _num(row, "E", 10.0),
            "nu": _num(row, "nu", 0.3),
            "Cc": max(0.0, _num(row, "Cc", 0.0)),
            "Cr": max(0.0, _num(row, "Cr", 0.0)),
            "e0": _num(row, "e0", 1.0),
            "OCR": _num(row, "OCR", 1.0),
            "cv": max(0.0, _num(row, "cv", 0.0)),
            "Calpha": max(0.0, _num(row, "Calpha", 0.0)),
            "drainage": row.get("drainage") if row.get("drainage") in DRAINAGE else "double",
        }
        if layer["gamma"] <= 0 or layer["gamma_sat"] <= gamma_w:
            raise SettleError("err_gamma", name=name)
        if not 0.0 <= layer["nu"] <= 0.5:
            raise SettleError("err_layer_nu", name=name)
        if behaviour == "cohesive":
            if layer["e0"] <= 0:
                raise SettleError("err_layer_e0", name=name)
            if layer["OCR"] < 1.0:
                self.warnings.append(_message("warn_ocr", name=name))
                layer["OCR"] = 1.0
        return layer

    # ------------------------------------------------------------------ geometry
    def points(self) -> Dict[str, tuple]:
        """Plan coordinates of the evaluation points, from the centre."""
        B, L = self.B, self.L
        if self.embankment:
            e = self.embankment
            edge = e["crest"] / 2.0
            return {"center": (0.0,), "shoulder": (edge,),
                    "midslope": (edge + e["run_right"] / 2.0,), "toe": (edge + e["run_right"],)}
        if self.shape == "circle":
            R = B / 2.0
            return {"center": (0.0,), "char": (CHAR_CIRCLE * R,), "edge": (R,)}
        if self.shape == "strip":
            return {"center": (0.0,), "char": (CHAR_RECT * B / 2.0,), "edge": (B / 2.0,)}
        return {"center": (0.0, 0.0), "char": (CHAR_RECT * B / 2.0, CHAR_RECT * L / 2.0),
                "edge": (B / 2.0, 0.0), "corner": (B / 2.0, L / 2.0)}

    @property
    def governing_point(self) -> str:
        """Where the foundation's settlement is read: the centre of a flexible
        foundation, the characteristic point of a rigid one."""
        return "char" if self.rigidity == "rigid" else "center"

    def area(self) -> float:
        if self.shape == "circle":
            return math.pi * self.B ** 2 / 4.0
        if self.shape == "strip":
            return self.B              # per metre run
        return self.B * self.L

    def influence(self, point: tuple, zb) -> np.ndarray:
        """Δσ/q at depth zb below the base, by the chosen stress method."""
        if self.embankment:
            e = self.embankment
            geometry = (e["crest"], e["height"], e["slope_left"], e["slope_right"])
            if self.stress_method == "two_to_one":
                return stress.embankment_two_to_one(*geometry, zb)
            return stress.embankment(*geometry, point[0], zb)
        return stress.influence(self.shape, self.B, self.L, point, zb, self.stress_method)

    def elastic_factor(self, point: tuple, H, nu: float) -> np.ndarray:
        """Settlement × E / q of an elastic layer from the base down to depth H."""
        if self.embankment:
            e = self.embankment
            return stress.embankment_elastic_factor(e["crest"], e["height"], e["slope_left"],
                                                    e["slope_right"], point[0], H, nu)
        return stress.elastic_depth_factor(self.shape, self.B, self.L, point, H, nu)

    def section_point(self, x: float) -> tuple:
        """The plan point at offset x on the section through the centre (across B)."""
        if self.shape == "rectangle":
            return (x, 0.0)
        if self.shape == "circle":
            return (abs(x),)
        return (x,)

    # ------------------------------------------------------------------ sublayers
    def _sublayers(self) -> Dict[str, np.ndarray]:
        tops, bots, idx = [], [], []
        for i, layer in enumerate(self.profile.layers):
            top = max(layer["top"], self.Df)
            bottom = layer["bottom"]
            if bottom <= top + 1e-9:
                continue
            n = max(1, int(math.ceil((bottom - top) / self.sublayer - 1e-9)))
            edges = np.linspace(top, bottom, n + 1)
            tops.extend(edges[:-1])
            bots.extend(edges[1:])
            idx.extend([i] * n)
        top, bot = np.array(tops), np.array(bots)
        return {"top": top, "bot": bot, "mid": 0.5 * (top + bot), "dz": bot - top,
                "layer": np.array(idx, dtype=int)}

    # ------------------------------------------------------------------ run
    def run(self) -> Dict[str, Any]:
        P = self.profile
        self._profile = None
        sub = self._sublayers()
        mid, dz, lay = sub["mid"], sub["dz"], sub["layer"]
        zb_mid, zb_top, zb_bot = mid - self.Df, sub["top"] - self.Df, sub["bot"] - self.Df
        layers = P.layers
        cohesive = np.array([layers[i]["behaviour"] == "cohesive" for i in lay])

        # ---- stresses
        sig_v0 = P.total_stress(mid)
        u0 = P.pore_pressure(mid)
        sig_eff = sig_v0 - u0
        ocr = np.array([layers[i]["OCR"] for i in lay])
        sig_p = np.where(cohesive, ocr * sig_eff, np.nan)

        sigma_base = float(P.total_stress(self.Df)[0])
        sigma_base_eff = float(P.effective_stress(self.Df)[0])
        q_net = self.q - sigma_base if self.net_pressure else self.q
        compensated = q_net <= 0
        if compensated:
            self.warnings.append(_message("warn_compensated"))
            q_net = 0.0

        points = self.points()
        centre = self.influence(points["center"], zb_mid) * q_net

        # ---- influence depth, from the centre (where the stress is largest)
        limit_mask = centre >= max(self.depth_ratio, 0.0) * sig_eff
        if self.depth_ratio <= 0:
            active = np.ones_like(mid, dtype=bool)
            z_limit = float(sub["bot"][-1])
        elif limit_mask.any():
            last = int(np.nonzero(limit_mask)[0][-1])
            active = np.arange(len(mid)) <= last
            z_limit = float(sub["bot"][last])
        else:
            active = np.zeros_like(mid, dtype=bool)
            z_limit = self.Df
        if not compensated and centre[-1] >= 0.1 * sig_eff[-1]:
            self.warnings.append(_message("warn_below_profile", depth=P.depth))

        cc = np.array([layers[i]["Cc"] for i in lay])
        cr = np.array([layers[i]["Cr"] for i in lay])
        compressible = cohesive & ((cc > 0) | (cr > 0))
        self._ctx = {"zb_top": zb_top, "zb_bot": zb_bot, "zb_mid": zb_mid, "dz": dz,
                     "lay": lay, "cohesive": cohesive, "compressible": compressible,
                     "sig_eff": sig_eff, "sig_p": sig_p, "active": active, "q_net": q_net,
                     "compensated": compensated, "schm": None, "creep": []}

        # ---- per-layer time behaviour, and the creep strain of each clay layer
        layer_rows = []
        for i, layer in enumerate(layers):
            rows = lay == i
            if not rows.any():
                continue
            loaded = float(np.sum(dz[rows]))
            info = {"index": i, "name": layer["name"], "behaviour": layer["behaviour"],
                    "top": float(sub["top"][rows][0]), "bottom": float(sub["bot"][rows][-1]),
                    "h_dr": float("nan"), "t50": float("nan"), "t90": float("nan"),
                    "t_p": float("nan"), "cv": layer["cv"]}
            if layer["behaviour"] == "cohesive":
                has_c = layer["Cc"] > 0 or layer["Cr"] > 0
                if not has_c:
                    self.warnings.append(_message("warn_no_cc", name=layer["name"]))
                h_dr = cons.drainage_path(loaded, layer["drainage"])
                info["h_dr"] = h_dr
                if layer["cv"] > 0:
                    info["t50"] = cons.time_for(0.5, layer["cv"], h_dr)
                    info["t90"] = cons.time_for(0.9, layer["cv"], h_dr)
                    info["t_p"] = cons.time_for(cons.U_END_OF_PRIMARY, layer["cv"], h_dr)
                elif has_c:
                    self.warnings.append(_message("warn_no_cv", name=layer["name"]))
                if layer["Calpha"] > 0 and not compensated:
                    if math.isfinite(info["t_p"]):
                        strain = cons.secondary_strain(self.design_life, info["t_p"],
                                                       layer["Calpha"], layer["e0"])[0]
                        # Cα/Cc is a soil constant (Mesri): where the load leaves the
                        # clay over-consolidated, creep follows the recompression line.
                        oc_factor = layer["Cr"] / layer["Cc"] if layer["Cc"] > 0 else 1.0
                        self._ctx["creep"].append((rows & active, strain, oc_factor))
                    else:
                        self.warnings.append(_message("warn_no_tp", name=layer["name"]))
            layer_rows.append(info)

        # ---- Schmertmann, whose footing value the other points scale
        schm = None
        if self.immediate_method == "schmertmann" and not compensated:
            schm = self._schmertmann(q_net, sigma_base_eff, zb_mid, dz, lay)
            zone = (~cohesive) & (zb_mid < schm["z_end"])
            self._ctx.update(schm=schm, zone=zone,
                             centre_el=float(np.sum(self._elastic_at(points["center"])[zone])))
            if schm["z_end"] > P.depth - self.Df + 1e-9:
                self.warnings.append(_message("warn_schmertmann_zone"))

        # ---- every point, sublayer by sublayer
        parts = {key: self._settle_at(pt) for key, pt in points.items()}
        dsig = {key: part["dsigma"] for key, part in parts.items()}
        immediate = {key: part["immediate"] for key, part in parts.items()}
        consolidation = {key: part["consolidation"] for key, part in parts.items()}
        secondary_pts = {key: part["secondary"] for key, part in parts.items()}

        # ---- totals at each point
        point_results = {}
        for key, pt in points.items():
            s_i = float(np.sum(immediate[key]))
            s_c = float(np.sum(consolidation[key]))
            s_s = float(np.sum(secondary_pts[key]))
            point_results[key] = {"coords": pt, "immediate": s_i, "consolidation": s_c,
                                  "secondary": s_s, "total": s_i + s_c + s_s}

        gov = self.governing_point
        for info in layer_rows:
            rows = lay == info["index"]
            info["immediate"] = float(np.sum(immediate[gov][rows]))
            info["consolidation"] = float(np.sum(consolidation[gov][rows]))
            info["secondary"] = float(np.sum(secondary_pts[gov][rows]))
            info["method"] = self._layer_method(layers[info["index"]])

        # ---- time–settlement curve at the governing point
        time_curve = self._time_curve(layer_rows, lay, consolidation[gov], secondary_pts[gov],
                                      point_results[gov]["immediate"])

        # ---- angular distortion and checks
        half = self.B / 2.0
        distortion = None
        if self.rigidity == "flexible" and not self.embankment:
            diff = abs(point_results["center"]["total"] - point_results["edge"]["total"])
            distortion = diff / 1000.0 / half if half > 0 else 0.0
        total = point_results[gov]["total"]
        checks = {
            "total": {"actual": total, "allowable": self.s_allow,
                      "status": "N/A" if self.s_allow <= 0 else
                      ("OK" if total <= self.s_allow else "NOT OK")},
            "distortion": {"actual": distortion,
                           "allowable": (1.0 / self.distortion_allow
                                         if self.distortion_allow > 0 else None),
                           "status": "N/A" if distortion is None or self.distortion_allow <= 0
                           else ("OK" if distortion <= 1.0 / self.distortion_allow
                                 else "NOT OK")},
        }

        self.results = {
            "q": self.q, "q_net": q_net, "sigma_base": sigma_base,
            "sigma_base_eff": sigma_base_eff, "compensated": compensated,
            "z_limit": z_limit, "points": point_results, "governing": gov,
            "total": total, "distortion": distortion, "checks": checks,
            "layers": layer_rows, "schmertmann": schm, "time": time_curve,
            "at_life": float(np.interp(self.design_life, time_curve["t"], time_curve["s"])),
            "sub": {
                "top": sub["top"], "bot": sub["bot"], "mid": mid, "dz": dz, "layer": lay,
                "sigma_v0": sig_v0, "u0": u0, "sigma_eff": sig_eff, "sigma_p": sig_p,
                "dsigma": dsig, "active": active, "immediate": immediate,
                "consolidation": consolidation, "secondary": secondary_pts,
            },
            "warnings": list(self.warnings),
        }
        return self.results

    # ------------------------------------------------------------------ one point
    def _elastic_at(self, point: tuple) -> np.ndarray:
        """Elastic (Steinbrenner) settlement of each sublayer at a point [mm]."""
        c = self._ctx
        values = np.zeros_like(c["zb_mid"])
        if c["compensated"]:
            return values
        for i, layer in enumerate(self.profile.layers):
            rows = np.nonzero(c["lay"] == i)[0]
            if rows.size == 0:
                continue
            edges = np.concatenate([c["zb_top"][rows[:1]], c["zb_bot"][rows]])
            factor = self.elastic_factor(point, edges, layer["nu"])
            values[rows] = c["q_net"] / layer["E"] * np.diff(factor)
        return values * 1000.0

    def _settle_at(self, point: tuple) -> Dict[str, np.ndarray]:
        """Stress increase and the three settlements of each sublayer at a point."""
        c = self._ctx
        dsig = c["q_net"] * self.influence(point, c["zb_mid"])
        elastic = self._elastic_at(point)
        immediate = np.where(c["active"], elastic, 0.0)
        if c["schm"] is not None:
            ratio = (float(np.sum(elastic[c["zone"]])) / c["centre_el"]
                     if c["centre_el"] > 0 else 1.0)
            immediate = np.where(c["cohesive"], immediate, c["schm"]["s"] * ratio)

        strain = np.zeros_like(dsig)
        for i, layer in enumerate(self.profile.layers):
            rows = (c["lay"] == i) & c["compressible"]
            if rows.any():
                strain[rows] = cons.primary_strain(c["sig_eff"][rows], dsig[rows],
                                                   c["sig_p"][rows], layer["Cc"], layer["Cr"],
                                                   layer["e0"])
        consolidation = np.where(c["active"] & c["compressible"], strain * c["dz"] * 1000.0, 0.0)

        secondary = np.zeros_like(dsig)
        for where, creep, oc_factor in c["creep"]:
            virgin = c["sig_eff"][where] + dsig[where] > c["sig_p"][where]
            factor = np.where(virgin, 1.0, oc_factor)
            secondary[where] = np.where(dsig[where] > 0, creep * factor * c["dz"][where] * 1000.0,
                                        0.0)
        return {"dsigma": dsig, "immediate": immediate, "consolidation": consolidation,
                "secondary": secondary}

    def settlement_profile(self, n: int = PROFILE_POINTS) -> Dict[str, np.ndarray]:
        """Settlement along the section through the centre (across B), out to
        well beyond the loaded width [mm]. Computed once, on demand."""
        if getattr(self, "_profile", None) is None:
            half = self.B / 2.0
            x = np.linspace(-2.0 * half, 2.0 * half, n)
            parts = [self._settle_at(self.section_point(float(xi))) for xi in x]
            out = {"x": x}
            for key in ("immediate", "consolidation", "secondary"):
                out[key] = np.array([float(np.sum(p[key])) for p in parts])
            out["total"] = out["immediate"] + out["consolidation"] + out["secondary"]
            self._profile = out
        return self._profile

    # ------------------------------------------------------------------ parts
    def _layer_method(self, layer: dict) -> str:
        if layer["behaviour"] == "cohesive":
            return "cohesive"
        return "schmertmann" if self.immediate_method == "schmertmann" else "elastic"

    def schmertmann_shape(self) -> Dict[str, float]:
        """The strain influence diagram of Schmertmann et al. (1978):
        axisymmetric for L/B = 1, plane strain for L/B ≥ 10, interpolated
        between."""
        if self.shape == "strip":
            ratio = 10.0
        elif self.shape == "circle":
            ratio = 1.0
        else:
            ratio = min(max(self.L / self.B, 1.0), 10.0)
        f = (ratio - 1.0) / 9.0
        return {"z_peak": self.B * (0.5 + 0.5 * f), "z_end": self.B * (2.0 + 2.0 * f),
                "Iz0": 0.1 + 0.1 * f}

    def _schmertmann(self, q_net, sigma_base_eff, zb_mid, dz, lay) -> Dict[str, Any]:
        shape = self.schmertmann_shape()
        z_peak, z_end, iz0 = shape["z_peak"], shape["z_end"], shape["Iz0"]
        sigma_peak = float(self.profile.effective_stress(self.Df + z_peak)[0])
        izp = 0.5 + 0.1 * math.sqrt(q_net / sigma_peak) if sigma_peak > 0 else 0.5
        c1 = max(0.5, 1.0 - 0.5 * sigma_base_eff / q_net)
        c2 = (1.0 + 0.2 * math.log10(self.design_life / 0.1)
              if self.creep and self.design_life > 0.1 else 1.0)
        iz = self.schmertmann_iz(zb_mid, iz0, izp, z_peak, z_end)
        E = np.array([self.profile.layers[i]["E"] for i in lay])
        s = c1 * c2 * q_net * iz / E * dz * 1000.0
        return {"C1": c1, "C2": c2, "Izp": izp, "Iz0": iz0, "z_peak": z_peak,
                "z_end": z_end, "sigma_peak": sigma_peak, "s": s}

    @staticmethod
    def schmertmann_iz(zb, iz0, izp, z_peak, z_end) -> np.ndarray:
        zb = np.asarray(zb, dtype=float)
        rising = iz0 + (izp - iz0) * zb / z_peak
        falling = izp * (z_end - zb) / (z_end - z_peak)
        return np.where(zb <= z_peak, rising, np.clip(falling, 0.0, None))

    def _time_curve(self, layer_rows, lay, consolidation, secondary, s_immediate) -> Dict:
        ends = [info["t_p"] for info in layer_rows if math.isfinite(info["t_p"])]
        t_max = max([2.0 * self.design_life] + [2.0 * t for t in ends])
        t = np.logspace(math.log10(T_MIN), math.log10(max(t_max, 10 * T_MIN)), TIME_POINTS)
        t = np.union1d(t, [self.design_life])
        primary = np.full_like(t, s_immediate)
        creep = np.zeros_like(t)
        for info in layer_rows:
            rows = lay == info["index"]
            layer = self.profile.layers[info["index"]]
            s_c = float(np.sum(consolidation[rows]))
            if s_c > 0:
                primary += cons.degree_at(t, layer["cv"], info["h_dr"]) * s_c
            s_s_life = float(np.sum(secondary[rows]))
            if s_s_life > 0:
                life = cons.secondary_strain(self.design_life, info["t_p"], layer["Calpha"],
                                             layer["e0"])[0]
                now = cons.secondary_strain(t, info["t_p"], layer["Calpha"], layer["e0"])
                creep += s_s_life * now / life
        return {"t": t, "s": primary + creep, "primary": primary}
