"""Terzaghi's time factor and the compression of clay."""
import math

import numpy as np
import pytest

from lythossettle import consolidation as cons


@pytest.mark.parametrize("U, Tv", [(0.1, 0.00785), (0.5, 0.197), (0.9, 0.848), (0.95, 1.129)])
def test_the_time_factor_matches_terzaghi(U, Tv):
    assert cons.time_factor(U) == pytest.approx(Tv, rel=3e-3)
    assert cons.degree(cons.time_factor(U))[0] == pytest.approx(U, abs=1e-9)


def test_the_degree_rises_from_zero_to_one_without_a_step():
    Tv = np.logspace(-6, 1, 2000)
    U = cons.degree(Tv)
    assert U[0] == pytest.approx(math.sqrt(4e-6 / math.pi), rel=1e-6)
    assert U[-1] == pytest.approx(1.0, abs=1e-9)
    assert np.all(np.diff(U) >= 0)
    # where the series takes over from √(4Tv/π) the two agree
    edge = cons.TV_SMALL
    assert cons.degree(edge * 0.999)[0] == pytest.approx(cons.degree(edge * 1.001)[0], abs=1e-4)


def test_the_time_factor_refuses_impossible_degrees():
    for U in (0.0, 1.0, 1.2):
        with pytest.raises(ValueError):
            cons.time_factor(U)


def test_drainage_path_and_time_scale_with_the_square_of_the_path():
    assert cons.drainage_path(6.0, "double") == 3.0
    assert cons.drainage_path(6.0, "single") == 6.0
    t_double = cons.time_for(0.9, 2.0, 3.0)
    assert t_double == pytest.approx(0.848 * 9 / 2, rel=3e-3)
    assert cons.time_for(0.9, 2.0, 6.0) == pytest.approx(4 * t_double)
    assert math.isnan(cons.time_for(0.9, 0.0, 3.0))
    assert cons.degree_at([0.1, 10], 0.0, 3.0) == pytest.approx([1.0, 1.0])


def test_normally_consolidated_clay_follows_the_virgin_line():
    strain = cons.primary_strain(100.0, 50.0, 100.0, 0.3, 0.05, 1.0)[0]
    assert strain == pytest.approx(0.3 / 2 * math.log10(1.5))


def test_overconsolidated_clay_stays_on_the_recompression_line():
    strain = cons.primary_strain(100.0, 50.0, 200.0, 0.3, 0.05, 1.0)[0]
    assert strain == pytest.approx(0.05 / 2 * math.log10(1.5))


def test_loading_through_the_preconsolidation_pressure_uses_both_lines():
    strain = cons.primary_strain(100.0, 150.0, 200.0, 0.3, 0.05, 1.0)[0]
    assert strain == pytest.approx((0.05 * math.log10(2.0) + 0.3 * math.log10(1.25)) / 2)


def test_secondary_compression_starts_at_the_end_of_primary():
    t = np.array([0.5, 1.0, 10.0])
    strain = cons.secondary_strain(t, 1.0, 0.02, 1.0)
    assert strain == pytest.approx([0.0, 0.0, 0.01])
    assert cons.secondary_strain(10.0, float("nan"), 0.02, 1.0)[0] == 0.0
