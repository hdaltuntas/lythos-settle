"""
The analysis figures of Lythos Settle.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display.

    schematic         section through the foundation: layers, water table,
                      footing and the Boussinesq isobars of Δσ / q_net
    stress            σ'v0, σ'v0 + Δσ, σ'p and the influence-depth criterion
    influence         Δσ / q_net at each evaluation point, and Schmertmann's Iz
    settlement_depth  settlement of the soil below each depth (cumulative)
    profile           settlement along the section through the centre
    time              time–settlement curve at the governing point
    points            immediate / consolidation / secondary at each point
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle

from . import stress
from .config import PLOT_PALETTE, SOIL_FILL
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure

#: The figures, in the order the interface offers them
PLOT_KEYS = ["schematic", "stress", "influence", "settlement_depth", "time", "points", "profile"]

#: Isobar levels of the stress bulb
ISOBARS = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]


class Plotter:
    """Draws the figures of one finished `SettlementAnalysis`."""

    def __init__(self, analysis, lang: str = "en", theme: str = "light", titles: bool = True):
        self.a = analysis
        self.res = analysis.results
        self.L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        self.theme = theme if theme in ("light", "dark", "paper") else "light"
        # The report writes each figure's name above it; there the figure goes untitled.
        self.titles = titles

    # ------------------------------------------------------------------ entry
    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        th = style_figure(fig, self.theme)
        getattr(self, f"_{key}")(fig, th)

    # ------------------------------------------------------------------ helpers
    def _title(self, fig, th, key):
        if not self.titles:
            return
        info = self.a.config.get("project_info", {}).get("title", "")
        fig.suptitle(self.L[f"fig_{key}"], color=th["fg"], fontsize=13.5, fontfamily=TITLE_FONT,
                     x=0.02, ha="left")
        if info:
            fig.text(0.98, 0.965, info, color=th["fg_dim"], fontsize=8.5, ha="right",
                     va="center")

    def _depth_axis(self, ax, th, z_max=None):
        """Depth downwards, with the layer boundaries and the water table."""
        a = self.a
        z_max = z_max or a.profile.depth
        ax.set_ylim(z_max, 0.0)
        ax.set_ylabel(self.L["ax_depth"])
        for layer in a.profile.layers:
            if 0 < layer["bottom"] < z_max:
                ax.axhline(layer["bottom"], color=th["border"], lw=0.8, zorder=1)
        if 0 <= a.profile.zw <= z_max:
            ax.axhline(a.profile.zw, color=PLOT_PALETTE["water"], lw=1.1, ls=(0, (6, 3)),
                       zorder=2, label=self.L["lg_water"])
        ax.axhline(a.Df, color=PLOT_PALETTE["footing"], lw=1.4, zorder=2)
        ax.grid(True, axis="both", color=th["border"], lw=0.6, alpha=0.7)

    def _legend(self, ax, th, **kw):
        legend = ax.legend(fontsize=8, frameon=True, **kw)
        legend.get_frame().set_facecolor(th["panel"])
        legend.get_frame().set_edgecolor(th["border"])
        for text in legend.get_texts():
            text.set_color(th["fg"])

    def _section_influence(self, x, zb):
        """Δσ/q along the section through the centre (across B)."""
        a = self.a
        if a.embankment:
            e = a.embankment
            return stress.embankment(e["crest"], e["height"], e["slope_left"], e["slope_right"],
                                     x, zb)
        if a.shape == "rectangle":
            return stress.rectangle(a.B, a.L, x, 0.0, zb)
        if a.shape == "strip":
            return stress.strip(a.B, x, zb)
        return stress.circle(a.B / 2.0, abs(x), zb)

    # ------------------------------------------------------------------ figures
    def _schematic(self, fig, th):
        a, res, L = self.a, self.res, self.L
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        z_max = min(a.profile.depth, a.Df + 4.0 * a.B) if a.B > 0 else a.profile.depth
        z_max = max(z_max, res["z_limit"] + 0.5 * a.B)
        z_max = min(z_max, a.profile.depth)
        x_max = max(1.6 * a.B, 0.8 * (z_max - a.Df) + a.B / 2.0)

        fills = SOIL_FILL[self.theme]
        for layer in a.profile.layers:
            if layer["top"] >= z_max:
                break
            bottom = min(layer["bottom"], z_max)
            ax.add_patch(Rectangle((-x_max, layer["top"]), 2 * x_max, bottom - layer["top"],
                                   facecolor=fills[layer["behaviour"]], edgecolor=th["border"],
                                   lw=0.8, alpha=0.55, zorder=0))
            ax.text(-x_max + 0.02 * x_max, 0.5 * (layer["top"] + bottom),
                    f"{layer['name']}\n{L['behaviour_' + layer['behaviour']]}, "
                    f"E = {layer['E_MPa']:g} MPa", fontsize=7.5, color=th["fg"], va="center",
                    ha="left", zorder=4, bbox=label_box(th, 0.8))

        if a.embankment:
            top = self._draw_embankment(ax, th, z_max)
        else:
            top = self._draw_footing(ax, th, z_max)

        # water table
        if 0 <= a.profile.zw <= z_max:
            ax.axhline(a.profile.zw, color=PLOT_PALETTE["water"], lw=1.3, ls=(0, (6, 3)),
                       zorder=3)
            ax.plot([x_max * 0.9], [a.profile.zw], marker="v", color=PLOT_PALETTE["water"],
                    ms=8, zorder=6)
            ax.text(x_max * 0.86, a.profile.zw, L["lg_water"], fontsize=7.5, ha="right",
                    va="bottom", color=th["fg_dim"], zorder=6)

        # isobars
        if res["q_net"] > 0:
            xs = np.linspace(-x_max, x_max, 97)
            zs = np.linspace(a.Df + 0.02, z_max, 90)
            grid = np.column_stack([self._section_influence(x, zs - a.Df) for x in xs])
            contours = ax.contour(xs, zs, grid, levels=ISOBARS, colors=th["accent"],
                                  linewidths=1.0, zorder=4)
            ax.clabel(contours, fmt="%.1f", fontsize=7.5, colors=th["fg"])
        if res["z_limit"] < z_max:
            ax.axhline(res["z_limit"], color=PLOT_PALETTE["limit"], lw=1.0, ls="--", zorder=4)
            ax.text(x_max * 0.98, res["z_limit"], L["lg_zlimit"], fontsize=7.5, ha="right",
                    va="bottom", color=PLOT_PALETTE["limit"], zorder=6)

        ax.set_xlim(-x_max, x_max)
        ax.set_ylim(z_max, top)
        ax.set_xlabel(L["ax_x"])
        ax.set_ylabel(L["ax_depth"])
        ax.text(0.01, -0.09, L["lg_isobar"], transform=ax.transAxes, fontsize=7.5,
                color=th["fg_dim"])
        self._title(fig, th, "schematic")

    def _draw_footing(self, ax, th, z_max) -> float:
        """The excavation, the footing and its pressure; returns the top of the view."""
        a, res, L = self.a, self.res, self.L
        ax.add_patch(Rectangle((-a.B / 2.0, 0.0), a.B, a.Df, facecolor=th["panel"],
                               edgecolor="none", zorder=1))
        thick = max(0.08 * a.B, 0.3)
        ax.add_patch(Rectangle((-a.B / 2.0, a.Df - thick), a.B, thick,
                               facecolor=PLOT_PALETTE["footing"], edgecolor=th["fg_dim"],
                               lw=1.0, zorder=5))
        for x in np.linspace(-a.B / 2.0, a.B / 2.0, 9):
            ax.annotate("", xy=(x, a.Df - thick), xytext=(x, a.Df - thick - 0.12 * z_max),
                        arrowprops=dict(arrowstyle="-|>", color=PLOT_PALETTE["total"], lw=1.0),
                        zorder=6)
        ax.text(0.0, a.Df - thick - 0.13 * z_max, L["lg_qnet"].format(q=res["q_net"]),
                ha="center", va="bottom", fontsize=8.5, color=th["fg"], zorder=6)
        return min(0.0, a.Df - thick - 0.2 * z_max)

    def _draw_embankment(self, ax, th, z_max) -> float:
        """The fill on the ground surface; returns the top of the view."""
        a, res, L = self.a, self.res, self.L
        e = a.embankment
        xs = [-e["crest"] / 2 - e["run_left"], -e["crest"] / 2, e["crest"] / 2,
              e["crest"] / 2 + e["run_right"]]
        ax.add_patch(Polygon([(xs[0], 0.0), (xs[1], -e["height"]), (xs[2], -e["height"]),
                              (xs[3], 0.0)], closed=True, facecolor=PLOT_PALETTE["fill"],
                             edgecolor=th["fg_dim"], lw=1.0, alpha=0.9, zorder=5))
        ax.text(0.0, -e["height"] / 2.0, L["lg_emb_load"].format(q=res["q_net"]), ha="center",
                va="center", fontsize=8.5, color="#1F2933", zorder=6)
        ax.axhline(0.0, color=th["fg_dim"], lw=0.8, zorder=2)
        return -e["height"] - 0.12 * z_max

    def _profile(self, fig, th):
        a, res, L = self.a, self.res, self.L
        prof = a.settlement_profile()
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        x = prof["x"]
        c1 = prof["immediate"]
        c2 = c1 + prof["consolidation"]
        c3 = c2 + prof["secondary"]
        ax.fill_between(x, 0, c1, color=PLOT_PALETTE["immediate"], alpha=0.3, lw=0)
        ax.fill_between(x, c1, c2, color=PLOT_PALETTE["consolidation"], alpha=0.3, lw=0)
        ax.fill_between(x, c2, c3, color=PLOT_PALETTE["secondary"], alpha=0.3, lw=0)
        ax.plot(x, c1, color=PLOT_PALETTE["immediate"], lw=1.4, label=L["head_immediate"])
        ax.plot(x, c2, color=PLOT_PALETTE["consolidation"], lw=1.4,
                label=f"+ {L['head_consolidation']}")
        ax.plot(x, c3, color=PLOT_PALETTE["total"], lw=2.0, label=f"+ {L['head_secondary']}")
        for key, p in res["points"].items():
            ax.plot([p["coords"][0]], [p["total"]], "o", color=PLOT_PALETTE.get(key, th["accent"]),
                    ms=6, zorder=5, label=L["point_" + key])
        if a.s_allow > 0:
            ax.axhline(a.s_allow, color=PLOT_PALETTE["allowable"], lw=1.0, ls="-.",
                       label=L["lg_allow"])
        # the loaded width, as a band along the top of the plot
        if a.embankment:
            e = a.embankment
            edges = [-e["crest"] / 2 - e["run_left"], e["crest"] / 2 + e["run_right"]]
        else:
            edges = [-a.B / 2.0, a.B / 2.0]
        ax.axvspan(*edges, color=PLOT_PALETTE["fill" if a.embankment else "footing"],
                   alpha=0.12, lw=0, zorder=0)
        top = max(float(np.max(c3)), a.s_allow if a.s_allow > 0 else 0.0, 1.0)
        ax.set_ylim(top * 1.1, 0.0)
        ax.set_xlim(x[0], x[-1])
        ax.set_xlabel(L["ax_x"])
        ax.set_ylabel(L["ax_settlement"])
        self._legend(ax, th, loc="lower right", ncol=2)
        self._title(fig, th, "profile")

    def _stress(self, fig, th):
        a, res, L = self.a, self.res, self.L
        sub = res["sub"]
        gov = res["governing"]
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        z = np.linspace(0.0, a.profile.depth, 400)
        ax.plot(a.profile.effective_stress(z), z, color=PLOT_PALETTE["overburden"], lw=1.6,
                label=L["lg_sigma_eff"])
        ax.plot(sub["sigma_eff"] + sub["dsigma"][gov], sub["mid"], color=PLOT_PALETTE["total"],
                lw=1.8, label=L["lg_final"])
        ax.plot(sub["dsigma"][gov], sub["mid"], color=PLOT_PALETTE["stress"], lw=1.4,
                label=L["lg_dsigma"].format(point=L["point_" + gov].lower()))
        if a.depth_ratio > 0:
            ax.plot(a.depth_ratio * sub["sigma_eff"], sub["mid"], color=PLOT_PALETTE["limit"],
                    lw=1.0, ls="--", label=L["lg_limit"].format(r=a.depth_ratio))
        sigma_p = np.where(np.isfinite(sub["sigma_p"]), sub["sigma_p"], np.nan)
        if np.isfinite(sigma_p).any():
            ax.plot(sigma_p, sub["mid"], color=PLOT_PALETTE["preconsolidation"], lw=1.4,
                    ls="-.", label=L["lg_sigma_p"])
        self._depth_axis(ax, th)
        if res["z_limit"] < a.profile.depth:
            ax.axhline(res["z_limit"], color=PLOT_PALETTE["limit"], lw=1.0, ls=":",
                       label=L["lg_zlimit"])
        ax.set_xlim(left=0.0)
        ax.set_xlabel(L["ax_stress"])
        self._legend(ax, th, loc="lower left")
        self._title(fig, th, "stress")

    def _influence(self, fig, th):
        a, res, L = self.a, self.res, self.L
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        z = np.linspace(a.Df + 1e-3, a.profile.depth, 300)
        for key, pt in a.points().items():
            ax.plot(a.influence(pt, z - a.Df), z, color=PLOT_PALETTE[key], lw=1.6,
                    label=L["point_" + key])
        schm = res.get("schmertmann")
        if schm:
            zb = np.linspace(0.0, schm["z_end"], 100)
            iz = a.schmertmann_iz(zb, schm["Iz0"], schm["Izp"], schm["z_peak"], schm["z_end"])
            ax.plot(iz, zb + a.Df, color=PLOT_PALETTE["limit"], lw=1.6, ls="--",
                    label=L["lg_iz"])
        self._depth_axis(ax, th)
        ax.set_xlim(0.0, 1.05)
        ax.set_xlabel(L["ax_influence"])
        self._legend(ax, th, loc="lower right")
        self._title(fig, th, "influence")

    def _settlement_depth(self, fig, th):
        res, L = self.res, self.L
        sub = res["sub"]
        gov = res["governing"]
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        imm, con, sec = (sub["immediate"][gov], sub["consolidation"][gov],
                         sub["secondary"][gov])

        def below(values):
            """Settlement of everything below each sublayer top, and at the bottom."""
            return np.concatenate([np.cumsum(values[::-1])[::-1], [0.0]])

        depth = np.concatenate([sub["top"], sub["bot"][-1:]])
        c1 = below(imm)
        c2 = c1 + below(con)
        c3 = c2 + below(sec)
        ax.fill_betweenx(depth, 0, c1, color=PLOT_PALETTE["immediate"], alpha=0.35, lw=0)
        ax.fill_betweenx(depth, c1, c2, color=PLOT_PALETTE["consolidation"], alpha=0.35, lw=0)
        ax.fill_betweenx(depth, c2, c3, color=PLOT_PALETTE["secondary"], alpha=0.35, lw=0)
        ax.plot(c1, depth, color=PLOT_PALETTE["immediate"], lw=1.5, label=L["head_immediate"])
        ax.plot(c2, depth, color=PLOT_PALETTE["consolidation"], lw=1.5,
                label=f"+ {L['head_consolidation']}")
        ax.plot(c3, depth, color=PLOT_PALETTE["secondary"], lw=1.5,
                label=f"+ {L['head_secondary']}")
        self._depth_axis(ax, th)
        ax.set_xlim(left=0.0)
        ax.set_xlabel(L["ax_cumulative"])
        ax.set_title(L["point_" + gov], color=th["fg_dim"], fontsize=9.5)
        self._legend(ax, th, loc="lower right")
        self._title(fig, th, "settlement_depth")

    def _time(self, fig, th):
        a, res, L = self.a, self.res, self.L
        curve = res["time"]
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(True, which="both", color=th["border"], lw=0.5, alpha=0.7)
        ax.semilogx(curve["t"], curve["primary"], color=PLOT_PALETTE["consolidation"], lw=1.5,
                    ls="--", label=L["lg_primary"])
        ax.semilogx(curve["t"], curve["s"], color=PLOT_PALETTE["total"], lw=2.0,
                    label=L["lg_total"])
        ax.axvline(a.design_life, color=th["fg_dim"], lw=1.0, ls=":", label=L["lg_life"])
        if a.s_allow > 0:
            ax.axhline(a.s_allow, color=PLOT_PALETTE["allowable"], lw=1.0, ls="-.",
                       label=L["lg_allow"])
        for info in res["layers"]:
            if math.isfinite(info["t90"]):
                s90 = float(np.interp(info["t90"], curve["t"], curve["s"]))
                ax.plot([info["t90"]], [s90], "o", color=PLOT_PALETTE["consolidation"], ms=5)
                ax.annotate(L["lg_t90"].format(name=info["name"]), (info["t90"], s90),
                            xytext=(6, -12), textcoords="offset points", fontsize=7.5,
                            color=th["fg"])
        top = max(float(np.max(curve["s"])), a.s_allow if a.s_allow > 0 else 0.0, 1.0)
        ax.set_ylim(top * 1.08, 0.0)
        ax.set_xlim(curve["t"][0], curve["t"][-1])
        ax.set_xlabel(L["ax_time"])
        ax.set_ylabel(L["ax_settlement"])
        ax.set_title(L["point_" + res["governing"]], color=th["fg_dim"], fontsize=9.5)
        self._legend(ax, th, loc="lower left")
        self._title(fig, th, "time")

    def _points(self, fig, th):
        a, res, L = self.a, self.res, self.L
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(True, axis="y", color=th["border"], lw=0.8)
        ax.grid(False, axis="x")
        keys = list(res["points"])
        x = np.arange(len(keys))
        bottom = np.zeros(len(keys))
        for part, key in (("immediate", "head_immediate"), ("consolidation", "head_consolidation"),
                          ("secondary", "head_secondary")):
            values = np.array([res["points"][k][part] for k in keys])
            ax.bar(x, values, 0.55, bottom=bottom, color=PLOT_PALETTE[part], alpha=0.85,
                   label=L[key], zorder=3)
            bottom += values
        for xi, total in zip(x, bottom):
            ax.text(xi, total, f"{total:.1f}", ha="center", va="bottom", fontsize=8.5,
                    color=th["fg"], zorder=4)
        if a.s_allow > 0:
            ax.axhline(a.s_allow, color=PLOT_PALETTE["allowable"], lw=1.2, ls="-.",
                       label=L["lg_allow"], zorder=4)
        ax.set_xticks(x)
        ax.set_xticklabels([L["point_" + k] for k in keys])
        ax.set_ylabel(L["ax_settlement"])
        ax.set_ylim(0, max(float(bottom.max()), a.s_allow) * 1.15 + 1e-9)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "points")
