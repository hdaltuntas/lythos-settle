"""
Figures and text of a parametric / reliability study.

    oat      the output against each swept input, one panel per input
    hist     the distribution of an output, with the allowable value
    scatter  the output against each sampled input
    tornado  Spearman rank correlations of the output with the inputs
"""

from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
from matplotlib.figure import Figure

from .config import PLOT_PALETTE
from .plot_style import TITLE_FONT, style_axis, style_figure
from .study import OUTPUTS, Study, _column

#: The colour of each output in the study figures
COLORS = {"s_total": PLOT_PALETTE["total"], "s_imm": PLOT_PALETTE["immediate"],
          "s_cons": PLOT_PALETTE["consolidation"], "s_sec": PLOT_PALETTE["secondary"],
          "beta": PLOT_PALETTE["stress"], "t90": PLOT_PALETTE["preconsolidation"]}


def _label(L: Dict[str, str], key: str) -> str:
    """An output's name; the translations carry its unit."""
    return L.get(f"out_{key}", key)


def _ok(study: Study) -> List[dict]:
    return [r for r in study.rows if not r.get("error")]


def default_outputs(study: Study) -> List[str]:
    """The outputs that have values, total settlement first."""
    stats = study.summary.get("stats", {}) if study.summary else {}
    return [key for key, _ in OUTPUTS if key in stats]


def _grid(n: int):
    cols = min(3, max(1, n))
    return int(math.ceil(n / cols)), cols


def _capacity(study: Study, output: str):
    if output == "s_total":
        return study.capacity.get("s_allow")
    if output == "beta":
        return study.capacity.get("beta_allow")
    return None


def _empty(fig: Figure, text: str, th) -> None:
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    ax.text(0.5, 0.5, text, ha="center", va="center", color=th["fg_dim"], fontsize=11)


def _title(fig, th, text):
    fig.suptitle(text, color=th["fg"], fontsize=13.5, fontfamily=TITLE_FONT, x=0.02, ha="left")


def plot_oat(fig: Figure, study: Study, L: Dict[str, str], output: str = "s_total",
             theme="light") -> None:
    th = style_figure(fig, theme)
    swept = [v for v in study.variables if v.mode == "range"]
    rows = _ok(study)
    if not swept or not rows:
        return _empty(fig, L["study_no_data"], th)
    nr, nc = _grid(len(swept))
    capacity = _capacity(study, output)
    for i, var in enumerate(swept, 1):
        ax = fig.add_subplot(nr, nc, i)
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        mine = [r for r in rows if r.get("_varied") == var.path]
        x, y = _column(mine, var.path), _column(mine, output)
        ax.plot(x, y, "-o", color=COLORS.get(output, th["accent"]), ms=4, lw=1.6)
        if var.base is not None:
            ax.axvline(var.base, color=th["fg_dim"], lw=0.9, ls=":")
        if capacity is not None:
            ax.axhline(capacity, color=PLOT_PALETTE["allowable"], lw=1.0, ls="-.")
        ax.set_xlabel(var.label, fontsize=8.5)
        if (i - 1) % nc == 0:
            ax.set_ylabel(_label(L, output), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _title(fig, th, L["study_fig_oat"])


def plot_hist(fig: Figure, study: Study, L: Dict[str, str], output: str = "s_total",
              theme="light") -> None:
    th = style_figure(fig, theme)
    values = _column(_ok(study), output)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return _empty(fig, L["study_no_data"], th)
    ax = fig.add_subplot(111)
    style_axis(ax, th)
    bins = max(8, min(40, int(math.sqrt(values.size)) + 2))
    ax.hist(values, bins=bins, color=COLORS.get(output, th["accent"]), alpha=0.75,
            edgecolor=th["panel"], zorder=3)
    ax.axvline(values.mean(), color=th["fg"], lw=1.2, ls="--",
               label=f"{L['st_mean']} = {values.mean():.3g}")
    capacity = _capacity(study, output)
    if capacity is not None:
        exceed = float(np.mean(values > capacity))
        ax.axvline(capacity, color=PLOT_PALETTE["allowable"], lw=1.4, ls="-.",
                   label=f"{L['lg_allow']} = {capacity:.3g}  (P = {exceed:.3g})")
    ax.set_xlabel(_label(L, output))
    ax.set_ylabel("n")
    legend = ax.legend(fontsize=8.5)
    legend.get_frame().set_facecolor(th["panel"])
    for text in legend.get_texts():
        text.set_color(th["fg"])
    _title(fig, th, L["study_fig_hist"])


def plot_scatter(fig: Figure, study: Study, L: Dict[str, str], output: str = "s_total",
                 theme="light") -> None:
    th = style_figure(fig, theme)
    rows = _ok(study)
    if not rows or not study.variables:
        return _empty(fig, L["study_no_data"], th)
    nr, nc = _grid(len(study.variables))
    y = _column(rows, output)
    capacity = _capacity(study, output)
    for i, var in enumerate(study.variables, 1):
        ax = fig.add_subplot(nr, nc, i)
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        ax.scatter(_column(rows, var.path), y, s=9, alpha=0.6,
                   color=COLORS.get(output, th["accent"]), edgecolor="none", zorder=3)
        if capacity is not None:
            ax.axhline(capacity, color=PLOT_PALETTE["allowable"], lw=1.0, ls="-.")
        ax.set_xlabel(var.label, fontsize=8.5)
        if (i - 1) % nc == 0:
            ax.set_ylabel(_label(L, output), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _title(fig, th, L["study_fig_scatter"])


def plot_tornado(fig: Figure, study: Study, L: Dict[str, str], output: str = "s_total",
                 theme="light") -> None:
    th = style_figure(fig, theme)
    rho = study.summary.get("spearman", {}).get(output, {})
    if not rho:
        return _empty(fig, L["st_no_sens"], th)
    labels = {v.path: v.label for v in study.variables}
    items = sorted(rho.items(), key=lambda item: abs(item[1]))
    ax = fig.add_subplot(111)
    style_axis(ax, th)
    values = [value for _, value in items]
    colors = [PLOT_PALETTE["total"] if value > 0 else PLOT_PALETTE["immediate"]
              for value in values]
    ax.barh(range(len(items)), values, color=colors, alpha=0.85, zorder=3)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([labels.get(path, path) for path, _ in items], fontsize=8.5)
    ax.axvline(0.0, color=th["fg_dim"], lw=0.9)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xlabel(f"Spearman ρ — {_label(L, output)}")
    _title(fig, th, L["study_fig_tornado"])


def _beta_text(beta: float, n: int) -> str:
    if beta == float("inf"):
        return f"> {-float(np.clip(_inv(3.0 / max(n, 1)), -10, 10)):.2f}"
    if beta == float("-inf"):
        return "−∞"
    return f"{beta:.2f}"


def _inv(p: float) -> float:
    from statistics import NormalDist
    return NormalDist().inv_cdf(min(max(p, 1e-12), 1 - 1e-12))


def summary_text(study: Study, L: Dict[str, str]) -> str:
    """The study as text: statistics, exceedance probabilities, sensitivities."""
    s = study.summary
    lines = [L["st_title"], "-" * 78,
             L["st_info"].format(method=L[f"method_{study.method}"], n=s.get("n_total", 0),
                                 ok=s.get("n_ok", 0)),
             "", L["st_stats_title"],
             f"  {'':<36}{'n':>6}{L['st_mean']:>10}{L['st_std']:>10}{'P5':>10}{'P50':>10}"
             f"{'P95':>10}"]
    for key, _ in OUTPUTS:
        st = s.get("stats", {}).get(key)
        if st:
            lines.append(f"  {_label(L, key):<36}{st['n']:>6}{st['mean']:>10.3g}{st['std']:>10.3g}"
                         f"{st['p5']:>10.3g}{st['p50']:>10.3g}{st['p95']:>10.3g}")
    if s.get("reliability"):
        lines += ["", L["st_rel_title"]]
        for name, r in s["reliability"].items():
            lines.append("  " + L["st_rel_line"].format(
                name=L[name], k=r["n_fail"], n=r["n"], pf=r["pf"], lo=r["pf_lo"], hi=r["pf_hi"],
                beta=_beta_text(r["beta"], r["n"])))
    rho = s.get("spearman", {}).get("s_total")
    lines += ["", L["st_sens_title"]]
    if rho:
        labels = {v.path: v.label for v in study.variables}
        for path, value in sorted(rho.items(), key=lambda item: -abs(item[1])):
            lines.append(f"  {labels.get(path, path):<40}{value:+.2f}")
    else:
        lines.append("  " + L["st_no_sens"])
    return "\n".join(lines)
