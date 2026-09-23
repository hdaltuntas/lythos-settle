"""
One-dimensional consolidation: Terzaghi's theory, and the settlement of a
clay sublayer from its compression indices.

Time
    U(Tv) is the average degree of consolidation for a uniform initial excess
    pore pressure: the Fourier series, with Terzaghi's √(4Tv/π) where the
    series would need too many terms. Tv(U) is its inverse, found by
    bisection so that U(Tv(U)) = U to the precision of the series, rather
    than by the usual two-branch approximation.

Magnitude
    Δe from Cc and Cr about the preconsolidation pressure σ'p: the
    recompression line up to σ'p and the virgin line beyond it.
"""

from __future__ import annotations

import numpy as np

#: Terms of the Fourier series (plenty for Tv ≥ 1e-3)
TERMS = 200

#: Below this Tv the series is replaced by √(4Tv/π) (identical there to 1e-9)
TV_SMALL = 1e-3

#: Degree of consolidation taken as the end of primary consolidation, from
#: which secondary compression is counted
U_END_OF_PRIMARY = 0.95


def degree(Tv) -> np.ndarray:
    """Average degree of consolidation U for time factor(s) Tv."""
    Tv = np.atleast_1d(np.asarray(Tv, dtype=float))
    Tv = np.maximum(Tv, 0.0)
    m = np.arange(TERMS)
    M = np.pi * (2 * m + 1) / 2.0
    series = 1.0 - np.sum(2.0 / M ** 2 * np.exp(-np.outer(np.maximum(Tv, TV_SMALL), M ** 2)),
                          axis=1)
    small = np.sqrt(4.0 * Tv / np.pi)
    return np.clip(np.where(Tv < TV_SMALL, small, series), 0.0, 1.0)


def time_factor(U: float) -> float:
    """Time factor Tv at which the average degree of consolidation is U."""
    if not 0.0 < U < 1.0:
        raise ValueError("the degree of consolidation must be between 0 and 1")
    lo, hi = 0.0, 10.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if degree(mid)[0] < U:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def drainage_path(thickness: float, drainage: str) -> float:
    """Longest drainage path: half the layer when both faces drain."""
    return thickness / 2.0 if drainage == "double" else thickness


def time_for(U: float, cv: float, h_dr: float) -> float:
    """Time (in the units of cv) to reach degree of consolidation U."""
    if cv <= 0:
        return float("nan")
    return time_factor(U) * h_dr * h_dr / cv


def degree_at(t, cv: float, h_dr: float) -> np.ndarray:
    """U at time(s) t for a layer with coefficient cv and drainage path h_dr.

    A layer without cv is taken as consolidating at once (U = 1)."""
    t = np.atleast_1d(np.asarray(t, dtype=float))
    if cv <= 0 or h_dr <= 0:
        return np.ones_like(t)
    return degree(cv * t / (h_dr * h_dr))


def primary_strain(sigma0, dsigma, sigma_p, Cc: float, Cr: float, e0: float) -> np.ndarray:
    """Vertical strain Δe / (1 + e0) of clay loaded from σ'0 by Δσ.

    σ'0 ≥ σ'p is normally consolidated; below it the recompression line is
    followed up to σ'p (or the final stress, whichever is lower) and the
    virgin line beyond.
    """
    s0 = np.maximum(np.atleast_1d(np.asarray(sigma0, dtype=float)), 1e-6)
    sf = np.maximum(s0 + np.maximum(np.asarray(dsigma, dtype=float), 0.0), s0)
    sp = np.maximum(np.asarray(sigma_p, dtype=float), s0)
    recompression = Cr * np.log10(np.minimum(sf, sp) / s0)
    virgin = Cc * np.log10(np.maximum(sf, sp) / sp)
    return (recompression + virgin) / (1.0 + e0)


def secondary_strain(t, t_p: float, Calpha: float, e0: float) -> np.ndarray:
    """Secondary compression strain Cα/(1 + e0)·log10(t / t_p), zero before t_p."""
    t = np.atleast_1d(np.asarray(t, dtype=float))
    if Calpha <= 0 or not np.isfinite(t_p) or t_p <= 0:
        return np.zeros_like(t)
    return Calpha / (1.0 + e0) * np.log10(np.maximum(t / t_p, 1.0))
