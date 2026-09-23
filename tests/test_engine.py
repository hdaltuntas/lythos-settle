"""
The settlement analysis against hand calculations and closed-form cases, and
its handling of the inputs it has to refuse or warn about.
"""
import copy
import math

import numpy as np
import pytest

from lythossettle.config import DEFAULT_CONFIG
from lythossettle.engine import SettleError, SettlementAnalysis


def cfg(**changes):
    """The default project with some sections changed."""
    c = copy.deepcopy(DEFAULT_CONFIG)
    for section, values in changes.items():
        if isinstance(values, dict):
            c[section].update(values)
        else:
            c[section] = values
    return c


def layer(**kw):
    base = {"name": "Layer", "thickness": 10.0, "behaviour": "granular", "gamma": 18.0,
            "gamma_sat": 20.0, "E": 20.0, "nu": 0.3, "Cc": 0.0, "Cr": 0.0, "e0": 1.0,
            "OCR": 1.0, "cv": 0.0, "Calpha": 0.0, "drainage": "double"}
    base.update(kw)
    return base


@pytest.fixture(scope="module")
def default():
    a = SettlementAnalysis(DEFAULT_CONFIG)
    a.run()
    return a


# --------------------------------------------------------------------------- #
#  In-situ stresses and net pressure
# --------------------------------------------------------------------------- #

def test_in_situ_stresses_by_hand(default):
    P = default.profile
    # fill 1.5 m × 18, sand 0.5 m × 18.5 above the water table (2 m), 3 m × 20 below
    sigma = 1.5 * 18 + 0.5 * 18.5 + 3.0 * 20.0
    assert P.total_stress(5.0)[0] == pytest.approx(sigma)
    assert P.pore_pressure(5.0)[0] == pytest.approx(3.0 * 9.81)
    assert P.effective_stress(5.0)[0] == pytest.approx(sigma - 3.0 * 9.81)


def test_net_pressure_deducts_the_excavated_overburden(default):
    res = default.results
    assert res["sigma_base"] == pytest.approx(1.5 * 18.0)
    assert res["q_net"] == pytest.approx(100.0 - 27.0)
    gross = SettlementAnalysis(cfg(foundation={"net_pressure": False}))
    assert gross.run()["q_net"] == pytest.approx(100.0)


# --------------------------------------------------------------------------- #
#  Closed-form cases
# --------------------------------------------------------------------------- #

def test_a_square_on_a_deep_elastic_layer_settles_as_the_half_space():
    B, q, E, nu = 2.0, 100.0, 20.0, 0.3
    c = cfg(foundation={"shape": "rectangle", "B": B, "L": B, "Df": 0.0, "q": q,
                        "net_pressure": False},
            soil_profile=[layer(thickness=400.0, E=E, nu=nu)],
            options={"depth_ratio": 0.0, "sublayer": 2.0})
    res = SettlementAnalysis(c).run()
    expected = q * B * (1 - nu ** 2) / (E * 1000) * 1.122 * 1000      # mm
    assert res["points"]["center"]["immediate"] == pytest.approx(expected, rel=0.01)
    # the corner of a flexible square settles half as much as its centre
    ratio = res["points"]["corner"]["immediate"] / res["points"]["center"]["immediate"]
    assert ratio == pytest.approx(0.5, rel=0.02)


def test_a_wide_load_on_a_thin_clay_layer_is_one_dimensional():
    q, H, Cc, e0 = 50.0, 2.0, 0.4, 1.2
    c = cfg(foundation={"shape": "strip", "B": 2000.0, "Df": 0.0, "q": q, "net_pressure": False},
            groundwater={"depth": 0.0},
            soil_profile=[layer(thickness=H, behaviour="cohesive", gamma_sat=18.0, Cc=Cc,
                                Cr=0.05, e0=e0, OCR=1.0, cv=1.0, E=5.0, nu=0.5)],
            options={"depth_ratio": 0.0, "sublayer": 0.01})
    res = SettlementAnalysis(c).run()
    gamma_b = 18.0 - 9.81
    # ∫ Cc/(1+e0)·log10((σ'+q)/σ') dz over the layer, σ' = γ'·z
    z = (np.arange(20000) + 0.5) / 20000 * H
    exact = float(np.sum(Cc / (1 + e0) * np.log10((gamma_b * z + q) / (gamma_b * z))) * H / 20000)
    assert res["points"]["center"]["consolidation"] == pytest.approx(exact * 1000, rel=0.01)


def test_schmertmann_by_hand():
    B, q, E, Df = 2.0, 150.0, 25.0, 1.0
    c = cfg(foundation={"shape": "rectangle", "B": B, "L": B, "Df": Df, "q": q,
                        "net_pressure": True},
            groundwater={"depth": 50.0},
            soil_profile=[layer(thickness=20.0, E=E, gamma=18.0)],
            options={"immediate_method": "schmertmann", "sublayer": 0.01, "design_life": 10.0,
                     "creep": True})
    res = SettlementAnalysis(c).run()
    q_net = q - 18.0 * Df
    s0 = 18.0 * Df
    C1 = 1 - 0.5 * s0 / q_net
    C2 = 1 + 0.2 * math.log10(10.0 / 0.1)
    Izp = 0.5 + 0.1 * math.sqrt(q_net / (18.0 * (Df + B / 2)))
    area = (0.1 + Izp) / 2 * (B / 2) + Izp * (2 * B - B / 2) / 2     # ∫ Iz dz
    expected = C1 * C2 * q_net * area / (E * 1000) * 1000
    schm = res["schmertmann"]
    assert schm["C1"] == pytest.approx(C1) and schm["C2"] == pytest.approx(C2)
    assert schm["Izp"] == pytest.approx(Izp)
    assert res["points"]["center"]["immediate"] == pytest.approx(expected, rel=0.005)


def test_schmertmann_strip_diagram_is_the_plane_strain_one():
    a = SettlementAnalysis(cfg(foundation={"shape": "strip", "B": 3.0}))
    shape = a.schmertmann_shape()
    assert shape == {"z_peak": pytest.approx(3.0), "z_end": pytest.approx(12.0),
                     "Iz0": pytest.approx(0.2)}


# --------------------------------------------------------------------------- #
#  Behaviour of the default project
# --------------------------------------------------------------------------- #

def test_the_parts_add_up(default):
    res = default.results
    for p in res["points"].values():
        assert p["total"] == pytest.approx(p["immediate"] + p["consolidation"] + p["secondary"])
    by_layer = sum(r["immediate"] + r["consolidation"] + r["secondary"] for r in res["layers"])
    assert by_layer == pytest.approx(res["total"])


def test_the_centre_settles_most_and_the_corner_least(default):
    p = default.results["points"]
    assert p["center"]["total"] > p["edge"]["total"] > p["corner"]["total"] > 0
    assert p["center"]["secondary"] > p["corner"]["secondary"]


def test_only_the_clay_consolidates(default):
    for row in default.results["layers"]:
        if row["behaviour"] == "granular":
            assert row["consolidation"] == 0 and row["secondary"] == 0
        else:
            assert row["consolidation"] > 0 and row["t90"] > row["t50"] > 0


def test_the_time_curve_rises_to_the_final_settlement(default):
    res = default.results
    curve = res["time"]
    assert np.all(np.diff(curve["s"]) >= -1e-9)
    assert curve["s"][0] == pytest.approx(res["points"]["center"]["immediate"], rel=0.05)
    # primary consolidation is over long before the design life (t90 ≈ 5 years)
    assert res["at_life"] == pytest.approx(res["total"], abs=0.5)


def test_the_influence_depth_limits_the_sum(default):
    whole = SettlementAnalysis(cfg(options={"depth_ratio": 0.0})).run()
    assert whole["z_limit"] == pytest.approx(default.profile.depth)
    assert whole["total"] >= default.results["total"]
    assert default.results["z_limit"] < default.profile.depth


def test_the_2_to_1_method_loads_every_point_alike():
    res = SettlementAnalysis(cfg(options={"stress_method": "two_to_one"})).run()
    cons = [p["consolidation"] for p in res["points"].values()]
    assert max(cons) == pytest.approx(min(cons))


def test_a_rigid_foundation_settles_as_its_characteristic_point():
    res = SettlementAnalysis(cfg(options={"rigidity": "rigid"})).run()
    assert res["governing"] == "char"
    assert res["total"] == pytest.approx(res["points"]["char"]["total"])
    assert res["distortion"] is None
    assert res["checks"]["distortion"]["status"] == "N/A"


def test_the_checks_follow_the_criteria(default):
    res = default.results
    assert res["checks"]["total"]["status"] == ("OK" if res["total"] <= 150 else "NOT OK")
    strict = SettlementAnalysis(cfg(criteria={"s_allow": 10.0, "distortion_allow": 0.0})).run()
    assert strict["checks"]["total"]["status"] == "NOT OK"
    assert strict["checks"]["distortion"]["status"] == "N/A"


@pytest.mark.parametrize("shape", ["strip", "circle"])
def test_other_shapes_have_no_corner(shape):
    res = SettlementAnalysis(cfg(foundation={"shape": shape})).run()
    assert list(res["points"]) == ["center", "char", "edge"]
    assert res["total"] > 0


def test_schmertmann_is_used_for_sand_and_elasticity_for_clay():
    res = SettlementAnalysis(cfg(options={"immediate_method": "schmertmann"})).run()
    methods = {row["name"]: row["method"] for row in res["layers"]}
    assert methods["Soft clay"] == "cohesive"
    assert methods["Medium dense sand"] == "schmertmann"


# --------------------------------------------------------------------------- #
#  Refusals and warnings
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("changes, key", [
    ({"foundation": {"B": 0.0}}, "err_dimensions"),
    ({"foundation": {"q": -5.0}}, "err_pressure"),
    ({"foundation": {"Df": 30.0}}, "err_depth"),
    ({"soil_profile": []}, "err_no_layers"),
    ({"soil_profile": [layer(E=0.0)]}, "err_layer_E"),
    ({"soil_profile": [layer(nu=0.6)]}, "err_layer_nu"),
    ({"soil_profile": [layer(gamma_sat=9.0)]}, "err_gamma"),
    ({"soil_profile": [layer(behaviour="cohesive", e0=0.0)]}, "err_layer_e0"),
    ({"options": {"sublayer": 0.0}}, "err_sublayer"),
    ({"options": {"design_life": 0.0}}, "err_life"),
])
def test_impossible_input_is_refused_with_a_key(changes, key):
    with pytest.raises(SettleError) as caught:
        SettlementAnalysis(cfg(**changes)).run()
    assert caught.value.key == key
    assert str(caught.value)                       # an English sentence as well


def test_a_compensated_foundation_does_not_settle():
    res = SettlementAnalysis(cfg(foundation={"q": 20.0})).run()
    assert res["compensated"] and res["total"] == 0.0
    assert ("warn_compensated", {}) in res["warnings"]


def test_a_short_length_is_swapped_and_said_so():
    a = SettlementAnalysis(cfg(foundation={"B": 16.0, "L": 8.0}))
    assert (a.B, a.L) == (8.0, 16.0)
    assert ("warn_swapped", {}) in a.warnings


def test_clay_without_its_properties_is_warned_about():
    clay = layer(behaviour="cohesive", Cc=0.0, Cr=0.0, cv=0.0, OCR=0.8, name="Clay")
    res = SettlementAnalysis(cfg(soil_profile=[layer(thickness=2.0), clay])).run()
    keys = {key for key, _ in res["warnings"]}
    assert {"warn_no_cc", "warn_ocr"} <= keys


def test_a_shallow_profile_is_warned_about():
    res = SettlementAnalysis(cfg(soil_profile=[layer(thickness=4.0)])).run()
    assert any(key == "warn_below_profile" for key, _ in res["warnings"])
