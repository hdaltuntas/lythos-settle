"""Embankment (fill) loading: the stress solution, the elastic superposition and
the analysis through every layer of the program."""
import copy
import math

import numpy as np
import pytest

from lythossettle import forms, stress
from lythossettle.config import DEFAULT_CONFIG
from lythossettle.engine import SettleError, SettlementAnalysis
from lythossettle.study import available_variables


def brute(crest, height, left, right, x, z, n=400001):
    """Flamant's line load summed over the load profile: the reference."""
    xs, ps = stress.embankment_vertices(crest, height, left, right)
    xi = np.linspace(xs[0], xs[-1], n)
    p = np.interp(xi, xs, ps)
    kernel = 2 * z ** 3 / (math.pi * ((xi - x) ** 2 + z * z) ** 2)
    return float(np.sum((p * kernel)[1:] + (p * kernel)[:-1]) / 2 * (xi[1] - xi[0]))


def embankment_cfg(**emb):
    c = copy.deepcopy(DEFAULT_CONFIG)
    c["foundation"]["shape"] = "embankment"
    c["embankment"].update(emb)
    return c


# --------------------------------------------------------------------------- #
#  Stress
# --------------------------------------------------------------------------- #

def test_vertical_slopes_make_a_uniform_strip():
    z = np.array([0.3, 1.0, 4.0])
    assert stress.embankment(5.0, 2.0, 90, 90, 0.7, z) == pytest.approx(stress.strip(5.0, 0.7, z))


@pytest.mark.parametrize("x, z", [(0.0, 1.0), (4.0, 2.5), (9.0, 3.0), (-12.0, 6.0), (20.0, 1.0)])
def test_the_trapezoid_agrees_with_a_brute_force_integral(x, z):
    exact = stress.embankment(6.0, 3.0, 30.0, 45.0, x, z)[0]
    assert exact == pytest.approx(brute(6.0, 3.0, 30.0, 45.0, x, z), abs=1e-6)


def test_a_triangular_embankment_has_no_crest():
    assert stress.embankment(0.0, 3.0, 30.0, 30.0, 0.0, 2.0)[0] == pytest.approx(
        brute(0.0, 3.0, 30.0, 30.0, 0.0, 2.0), abs=1e-6)


def test_a_symmetric_embankment_loads_symmetrically():
    z = np.linspace(0.5, 20, 30)
    assert stress.embankment(8, 4, 26.57, 26.57, 5.0, z) == pytest.approx(
        stress.embankment(8, 4, 26.57, 26.57, -5.0, z))


def test_just_below_the_crest_the_full_load_arrives_and_below_a_toe_half_of_nothing():
    assert stress.embankment(10, 4, 30, 30, 0.0, 1e-4)[0] == pytest.approx(1.0, abs=1e-3)
    mid = 5 + stress.slope_run(4, 30) / 2
    assert stress.embankment(10, 4, 30, 30, mid, 1e-4)[0] == pytest.approx(0.5, abs=1e-3)


def test_the_2_to_1_spread_carries_the_whole_load():
    width = 6 + 0.5 * (stress.slope_run(3, 30) + stress.slope_run(3, 45))
    assert stress.embankment_two_to_one(6, 3, 30, 45, 0.0)[0] == pytest.approx(1.0)
    assert stress.embankment_two_to_one(6, 3, 30, 45, 4.0)[0] == pytest.approx(width / (width + 4))


# --------------------------------------------------------------------------- #
#  Elastic superposition
# --------------------------------------------------------------------------- #

def test_the_plane_strain_strip_is_the_long_rectangle():
    assert stress.plane_strip_elastic(-2, 2, [5, 10], 0.3) == pytest.approx(
        stress.elastic_depth_factor("strip", 4, 0, (0.0,), [5, 10], 0.3), rel=1e-3)


def test_vertical_slopes_leave_only_the_crest_strip():
    assert stress.embankment_elastic_factor(4, 3, 90, 90, 1.0, [8], 0.3) == pytest.approx(
        stress.plane_strip_elastic(-3, 1, [8], 0.3))


def test_the_slices_are_converged():
    coarse = stress.embankment_elastic_factor(6, 3, 26.57, 30, 4.0, [10], 0.3)
    fine = stress.embankment_elastic_factor(6, 3, 26.57, 30, 4.0, [10], 0.3, slices=400)
    assert coarse == pytest.approx(fine, rel=2e-3)


# --------------------------------------------------------------------------- #
#  The analysis
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def default():
    a = SettlementAnalysis(embankment_cfg())
    a.run()
    return a


def test_the_fill_load_is_gamma_times_height(default):
    assert default.q == pytest.approx(20.0 * 4.0)
    assert default.results["q_net"] == pytest.approx(80.0)
    assert default.Df == 0.0
    assert default.B == pytest.approx(12 + 2 * 4 / math.tan(math.radians(26.57)))


def test_settlement_falls_from_the_crest_to_the_toe(default):
    p = default.results["points"]
    assert list(p) == ["center", "shoulder", "midslope", "toe"]
    assert p["center"]["total"] > p["shoulder"]["total"] > p["midslope"]["total"] > \
        p["toe"]["total"] > 0


def test_a_fill_is_flexible_and_its_distortion_is_not_checked(default):
    assert default.rigidity == "flexible"
    assert default.results["distortion"] is None
    assert default.results["checks"]["distortion"]["status"] == "N/A"


def test_a_very_wide_fill_on_thin_clay_is_one_dimensional():
    H, q, Cc, e0 = 2.0, 60.0, 0.4, 1.2
    c = embankment_cfg(crest=4000.0, height=3.0, gamma=20.0)
    c["groundwater"]["depth"] = 0.0
    c["soil_profile"] = [{"name": "Clay", "thickness": H, "behaviour": "cohesive",
                          "gamma": 18.0, "gamma_sat": 18.0, "E": 5.0, "nu": 0.5, "Cc": Cc,
                          "Cr": 0.05, "e0": e0, "OCR": 1.0, "cv": 1.0, "Calpha": 0.0,
                          "drainage": "double"}]
    c["options"].update(depth_ratio=0.0, sublayer=0.01)
    res = SettlementAnalysis(c).run()
    gb = 18.0 - 9.81
    z = (np.arange(20000) + 0.5) / 20000 * H
    exact = float(np.sum(Cc / (1 + e0) * np.log10((gb * z + q) / (gb * z))) * H / 20000)
    assert res["points"]["center"]["consolidation"] == pytest.approx(exact * 1000, rel=0.01)


def test_the_profile_is_symmetric_for_a_symmetric_fill(default):
    prof = default.settlement_profile()
    assert prof["total"] == pytest.approx(prof["total"][::-1], rel=1e-6, abs=1e-9)
    assert np.argmax(prof["total"]) == len(prof["x"]) // 2
    centre = prof["total"][len(prof["x"]) // 2]
    assert centre == pytest.approx(default.results["points"]["center"]["total"], rel=1e-9)


def test_a_steeper_right_slope_moves_the_settlement_left():
    prof = SettlementAnalysis(embankment_cfg(slope_left=20.0, slope_right=60.0))
    prof.run()
    p = prof.settlement_profile()
    assert p["x"][np.argmax(p["total"])] < 0


def test_schmertmann_is_not_used_under_a_fill():
    c = embankment_cfg()
    c["options"]["immediate_method"] = "schmertmann"
    a = SettlementAnalysis(c)
    res = a.run()
    assert a.immediate_method == "elastic" and res["schmertmann"] is None
    assert ("warn_emb_schmertmann", {}) in res["warnings"]


@pytest.mark.parametrize("bad", [dict(height=0.0), dict(gamma=0.0), dict(crest=-1.0),
                                 dict(slope_left=0.0), dict(slope_right=95.0)])
def test_an_impossible_fill_is_refused(bad):
    with pytest.raises(SettleError) as caught:
        SettlementAnalysis(embankment_cfg(**bad))
    assert caught.value.key == "err_embankment"


# --------------------------------------------------------------------------- #
#  Forms and study
# --------------------------------------------------------------------------- #

def test_the_form_shows_the_fill_fields_only_for_a_fill():
    groups = forms.schema("tr")["foundation"]["groups"]
    by_key = {f["key"]: f for g in groups for f in g["fields"]}
    assert by_key["L"]["shapes"] == ["rectangle"]
    assert "embankment" not in by_key["q"]["shapes"]
    fill = next(g for g in groups if g.get("shapes") == ["embankment"])
    assert fill["title"] == "Dolgu"
    assert [f["key"] for f in fill["fields"]] == ["emb_crest", "emb_height", "emb_slope_left",
                                                  "emb_slope_right", "emb_gamma"]


def test_the_fill_inputs_round_trip_through_a_project_file():
    values = forms.defaults()
    values.update(shape="embankment", emb_height=6.5, emb_slope_right=33.69)
    back = forms.from_config(forms.project_file(values))
    assert back["emb_height"] == 6.5 and back["emb_slope_right"] == 33.69
    SettlementAnalysis(forms.to_config(back)).run()


def test_a_study_of_a_fill_varies_the_fill():
    paths = [p for p, _ in available_variables(embankment_cfg())]
    assert "embankment.height" in paths and "embankment.gamma" in paths
    assert "foundation.q" not in paths
