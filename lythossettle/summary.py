"""
Results as text and as summary cards.

Both the browser interface and the command line show the same thing: the
headline numbers as a row of cards, and the full account of the analysis as
text. Assembling them here keeps that promise without either side copying the
other's wording, and it needs no interface toolkit at all — pass a finished
analysis and a language code.
"""

from __future__ import annotations

import math
from typing import List

from .i18n import TRANSLATIONS, warning_text

#: Card order, as the interface lays them out
CARD_KEYS = ["total", "immediate", "consolidation", "secondary", "time", "distortion",
             "check_total", "check_dist"]


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def _status(L: dict, status: str) -> tuple:
    """A check status as (short text, state) — state drives the card colour."""
    if status == "N/A":
        return L["na_short"], "na"
    return (L["ok_short"], "ok") if status == "OK" else (L["notok_short"], "bad")


def duration(L: dict, years: float) -> str:
    """A time in days below a year, in years above."""
    if years is None or not math.isfinite(years):
        return L["card_none"]
    if years < 1.0:
        return L["unit_days"].format(v=years * 365.25)
    return L["unit_years"].format(v=years)


def distortion_text(value) -> str:
    """Angular distortion as 1/x."""
    if value is None:
        return "—"
    if value <= 0:
        return "0"
    return f"1/{1.0 / value:,.0f}"


def longest_t90(res: dict) -> float:
    times = [info["t90"] for info in res["layers"] if math.isfinite(info["t90"])]
    return max(times) if times else float("nan")


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers: settlement, its parts, time, distortion and checks."""
    L = _lang(lang)
    res = analysis.results
    gov = res["points"][res["governing"]]
    out = []

    def card(key, value, sub="", state="", title=None):
        out.append({"key": key, "title": title or L[f"card_{key}"], "value": value,
                    "sub": sub, "state": state})

    life = analysis.design_life
    card("total", f"{gov['total']:.1f} mm", L["point_" + res["governing"]])
    card("immediate", f"{gov['immediate']:.1f} mm")
    card("consolidation", f"{gov['consolidation']:.1f} mm")
    card("secondary", f"{gov['secondary']:.1f} mm",
         title=L["card_secondary"].format(life=life))
    t90 = longest_t90(res)
    card("time", duration(L, t90), L["card_at_life"].format(life=life) +
         f": {res['at_life']:.1f} mm", "" if math.isfinite(t90) else "na")
    card("distortion", distortion_text(res["distortion"]),
         "" if res["distortion"] is not None else
         L["card_dist_emb"] if analysis.embankment else L["rigidity_rigid"],
         "na" if res["distortion"] is None else "")

    check = res["checks"]["total"]
    text, state = _status(L, check["status"])
    card("check_total", text,
         f"{check['actual']:.1f} / {check['allowable']:.1f} mm" if check["status"] != "N/A"
         else "", state)
    check = res["checks"]["distortion"]
    text, state = _status(L, check["status"])
    card("check_dist", text,
         f"{distortion_text(check['actual'])} / {distortion_text(check['allowable'])}"
         if check["status"] != "N/A" else "", state)
    return out


def _row(first: str, values, width: int = 30) -> str:
    return f"  {first:<{width}}" + "".join(f"{v:>12}" for v in values)


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    a, res = analysis, analysis.results
    lines = [L["res_title"], "-" * 78]
    if a.embankment:
        e = a.embankment
        lines += [L["res_embankment"].format(c=e["crest"], h=e["height"], sl=e["slope_left"],
                                             sr=e["slope_right"], g=e["gamma"], w=a.B),
                  L["res_emb_load"].format(q=res["q"])]
    else:
        L_part = f", L = {a.L:.2f} m" if a.shape == "rectangle" else ""
        lines += [L["res_foundation"].format(shape=L["shape_" + a.shape], B=a.B, L=L_part,
                                             Df=a.Df, rigidity=L["rigidity_" + a.rigidity]),
                  L["res_pressure"].format(q=res["q"], s=res["sigma_base"], qn=res["q_net"])]
    lines += [
        L["res_methods"].format(stress=L["stress_" + a.stress_method],
                                imm=L["immediate_" + a.immediate_method]),
        L["res_limit"].format(z=res["z_limit"], zb=res["z_limit"] - a.Df),
    ]
    if res["compensated"]:
        lines.append(L["res_compensated"])

    heads = [L["head_immediate"], L["head_consolidation"], L["head_secondary"], L["head_total"]]
    lines += ["", L["res_points_title"], _row(L["head_point"], heads)]
    for key, p in res["points"].items():
        lines.append(_row(L["point_" + key], [f"{p['immediate']:.1f}", f"{p['consolidation']:.1f}",
                                              f"{p['secondary']:.1f}", f"{p['total']:.1f}"]))

    lines += ["", L["res_layers_title"].format(point=L["point_" + res["governing"]].lower()),
              _row(L["head_layer"], heads)]
    for info in res["layers"]:
        total = info["immediate"] + info["consolidation"] + info["secondary"]
        lines.append(_row(info["name"][:30], [f"{info['immediate']:.1f}",
                                              f"{info['consolidation']:.1f}",
                                              f"{info['secondary']:.1f}", f"{total:.1f}"]))

    schm = res.get("schmertmann")
    if schm:
        lines += ["", L["res_schm"].format(c1=schm["C1"], c2=schm["C2"], izp=schm["Izp"],
                                           zp=schm["z_peak"], ze=schm["z_end"])]

    clays = [info for info in res["layers"] if info["behaviour"] == "cohesive"]
    if clays:
        lines += ["", L["res_time_title"]]
        for info in clays:
            lines.append("  " + L["res_time_line"].format(
                name=info["name"], h=info["h_dr"], cv=info["cv"],
                t50=duration(L, info["t50"]), t90=duration(L, info["t90"])))
    lines.append("  " + L["res_at_life"].format(life=a.design_life, s=res["at_life"]))

    lines += ["", L["res_checks_title"]]
    check = res["checks"]["total"]
    if check["status"] != "N/A":
        lines.append("  " + L["res_check_total"].format(
            s=check["actual"], a=check["allowable"], status=_status(L, check["status"])[0]))
    check = res["checks"]["distortion"]
    if check["status"] != "N/A":
        lines.append("  " + L["res_check_dist"].format(
            x=distortion_text(check["actual"]), a=distortion_text(check["allowable"]),
            status=_status(L, check["status"])[0]))
    if a.embankment:
        lines.append("  " + L["res_emb_dist"])
    elif a.rigidity == "rigid":
        lines.append("  " + L["res_rigid"])

    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, w) for w in res["warnings"]]
    return "\n".join(lines)


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar: the settlement, the time and the check."""
    L = _lang(lang)
    res = analysis.results
    status, _ = _status(L, res["checks"]["total"]["status"])
    return (f"s = {res['total']:.1f} mm · t90 = {duration(L, longest_t90(res))} · "
            f"{L['card_check_total']}: {status}")
