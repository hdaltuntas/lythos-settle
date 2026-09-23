"""
The stress and elastic-settlement solutions against published values and
against each other.
"""
import math

import numpy as np
import pytest

from lythossettle import stress

# --------------------------------------------------------------------------- #
#  Boussinesq
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("m, n, expected", [
    (1.0, 1.0, 0.1752),     # Newmark's chart / Das, Table 10.10
    (2.0, 2.0, 0.2325),
    (0.5, 1.0, 0.1202),
    (1.0, 2.0, 0.1999),
    (3.0, 3.0, 0.2439),
])
def test_the_corner_factor_matches_the_tabulated_values(m, n, expected):
    assert stress.corner_factor(m, n, 1.0)[0] == pytest.approx(expected, abs=5e-4)


def test_the_centre_of_a_rectangle_is_four_corners():
    z = np.array([0.5, 2.0, 7.0])
    centre = stress.rectangle(4.0, 6.0, 0.0, 0.0, z)
    assert centre == pytest.approx(4 * stress.corner_factor(2.0, 3.0, z))


def test_a_point_outside_the_rectangle_takes_the_difference_of_rectangles():
    # A point 1 m beyond the edge of a 2 x 2 area: [1, 3] x [-1, 1] seen from it.
    z = 1.5
    expected = 2 * (stress.corner_factor(3.0, 1.0, z) - stress.corner_factor(1.0, 1.0, z))
    assert stress.rectangle(2.0, 2.0, 2.0, 0.0, z) == pytest.approx(expected)


def test_just_below_a_loaded_area_the_full_pressure_arrives():
    assert stress.rectangle(3.0, 5.0, 0.2, -0.4, 1e-4)[0] == pytest.approx(1.0, abs=1e-3)
    assert stress.strip(3.0, 0.5, 1e-4)[0] == pytest.approx(1.0, abs=1e-3)
    assert stress.circle(1.5, 0.7, 1e-4)[0] == pytest.approx(1.0, abs=1e-3)


def test_the_strip_is_the_limit_of_a_long_rectangle():
    z = np.array([0.5, 1.0, 3.0])
    assert stress.rectangle(2.0, 2000.0, 0.3, 0.0, z) == pytest.approx(stress.strip(2.0, 0.3, z),
                                                                     abs=1e-6)


def test_the_strip_centre_closed_form():
    # Δσ/q = (α + sin α)/π with α the angle subtended by the strip
    B, z = 2.0, 1.0
    alpha = 2 * math.atan(B / 2 / z)
    assert stress.strip(B, 0.0, z)[0] == pytest.approx((alpha + math.sin(alpha)) / math.pi)


@pytest.mark.parametrize("z", [0.5, 1.0, 2.0, 5.0])
def test_the_circle_centre_closed_form(z):
    R = 1.0
    assert stress.circle(R, 0.0, z)[0] == pytest.approx(1 - (z * z / (z * z + R * R)) ** 1.5)
    # the off-centre integral agrees with it as d -> 0
    assert stress.circle(R, 1e-6, z)[0] == pytest.approx(stress.circle(R, 0.0, z)[0], abs=1e-6)


def _circle_brute(R, d, z, nr=400, nt=720):
    """Boussinesq summed over a polar grid of the circle: the reference."""
    r = (np.arange(nr) + 0.5) / nr * R
    t = (np.arange(nt) + 0.5) / nt * 2 * math.pi
    rr, tt = np.meshgrid(r, t)
    dist2 = (rr * np.cos(tt) - d) ** 2 + (rr * np.sin(tt)) ** 2
    kernel = 3 * z ** 3 / (2 * math.pi * (dist2 + z * z) ** 2.5)
    return float(np.sum(kernel * rr) * (R / nr) * (2 * math.pi / nt))


@pytest.mark.parametrize("d, z, expected", [
    (1.0, 1.0, 0.332),      # Ahlvin & Ulery: under the edge, z/R = 1
    (1.0, 2.0, 0.196),      # under the edge, z/R = 2
    (0.5, 1.0, 0.562),      # r/R = 0.5, z/R = 1
])
def test_the_circle_off_centre_matches_ahlvin(d, z, expected):
    assert stress.circle(1.0, d, z)[0] == pytest.approx(expected, abs=0.002)
    assert stress.circle(1.0, d, z)[0] == pytest.approx(_circle_brute(1.0, d, z), rel=3e-3)


def test_the_circle_outside_agrees_with_a_brute_force_integral():
    assert stress.circle(1.0, 1.8, 1.2)[0] == pytest.approx(_circle_brute(1.0, 1.8, 1.2), rel=2e-3)


def test_two_to_one_spreads_the_load_over_a_growing_area():
    assert stress.two_to_one("rectangle", 2.0, 4.0, 2.0)[0] == pytest.approx(8 / (4 * 6))
    assert stress.two_to_one("strip", 2.0, 0.0, 2.0)[0] == pytest.approx(0.5)
    assert stress.two_to_one("circle", 2.0, 0.0, 2.0)[0] == pytest.approx(0.25)


def test_stress_decreases_with_depth_and_away_from_the_centre():
    z = np.linspace(0.1, 20, 50)
    centre = stress.rectangle(4, 8, 0, 0, z)
    edge = stress.rectangle(4, 8, 2, 0, z)
    assert np.all(np.diff(centre) < 0)
    assert np.all(centre > edge)


# --------------------------------------------------------------------------- #
#  Steinbrenner
# --------------------------------------------------------------------------- #

def test_steinbrenner_on_a_half_space_gives_the_classic_corner_factor():
    F1, F2 = stress.steinbrenner_factors(1.0, 1.0, 1e6)
    assert F1[0] == pytest.approx(0.561, abs=1e-3)      # corner of a square
    assert F2[0] == pytest.approx(0.0, abs=1e-5)


@pytest.mark.parametrize("M, N, F1, F2", [
    (1.0, 1.0, 0.1419, 0.0833),    # Bowles, Table 5-2; worked by hand from the formulas
    (1.0, 2.0, 0.2851, 0.0641),
    (2.0, 1.0, 0.1250, 0.1090),
])
def test_steinbrenner_factors_match_bowles(M, N, F1, F2):
    f1, f2 = stress.steinbrenner_factors(M, 1.0, N)
    assert f1[0] == pytest.approx(F1, abs=2e-4)
    assert f2[0] == pytest.approx(F2, abs=2e-4)


def test_a_flexible_square_centre_on_a_half_space():
    # s = q B (1 − ν²) / E · 1.122 at the centre of a flexible square
    factor = stress.elastic_depth_factor("rectangle", 1.0, 1.0, (0.0, 0.0), 1e5, 0.3)[0]
    assert factor == pytest.approx(1.122 * (1 - 0.3 ** 2), rel=2e-3)


def test_a_flexible_circle_centre_on_a_half_space_through_the_equivalent_square():
    # exact: s = 2 q R (1 − ν²) / E, here with D = 2 m (R = 1)
    factor = stress.elastic_depth_factor("circle", 2.0, 0.0, (0.0,), 1e5, 0.0)[0]
    assert factor == pytest.approx(2.0, rel=0.01)


def test_the_strip_factor_is_converged():
    a = stress.elastic_depth_factor("strip", 1.0, 0.0, (0.0,), [5.0, 10.0], 0.3)
    saved = stress.STRIP_ASPECT
    try:
        stress.STRIP_ASPECT = 2000.0
        b = stress.elastic_depth_factor("strip", 1.0, 0.0, (0.0,), [5.0, 10.0], 0.3)
    finally:
        stress.STRIP_ASPECT = saved
    assert a == pytest.approx(b, rel=2e-3)


def test_the_elastic_factor_grows_with_depth_and_starts_at_zero():
    H = np.array([0.0, 0.5, 1, 2, 5, 10, 50])
    f = stress.elastic_depth_factor("rectangle", 3.0, 6.0, (0.0, 0.0), H, 0.3)
    assert f[0] == pytest.approx(0.0, abs=1e-12)
    assert np.all(np.diff(f) > 0)


def test_an_incompressible_layer_settles_only_through_distortion():
    # ν = 0.5 leaves (1 − ν − 2ν²) = 0: only the F1 term remains
    f = stress.elastic_depth_factor("rectangle", 2.0, 2.0, (0.0, 0.0), 3.0, 0.5)[0]
    F1, _ = stress.steinbrenner_factors(1.0, 1.0, 3.0)
    assert f == pytest.approx(4 * 1.0 * 0.75 * F1[0])
