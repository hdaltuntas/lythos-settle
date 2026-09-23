"""
Vertical stress increase under a uniformly loaded foundation, and the elastic
settlement influence factors that go with it.

Everything here is a closed-form (or one-dimensional-integral) solution for a
flexible, uniformly loaded area on the surface of a homogeneous elastic
half-space; depth ``z`` is measured from the foundation base. The functions are
vectorised over ``z`` and know nothing about soil layers or the interface.

Stress distribution
    rectangle   Newmark's integration of Boussinesq under a corner, with the
                four-rectangle superposition for any point in plan
    strip       the closed-form strip solution (plane strain)
    circle      a one-dimensional integral over the polar angle, exact for
                any point inside or on the edge of the circle
    2:1         the approximate spread at two vertical to one horizontal

Elastic settlement
    Steinbrenner's influence factors F1, F2 under the corner of a flexible
    rectangle on a layer of finite thickness, superposed like the stresses.
    The settlement of a layer between two depths is the difference of the
    factor at the two depths (the layered Steinbrenner method).
"""

from __future__ import annotations

import math

import numpy as np

#: Long side of a strip, in widths, when a strip is treated as a rectangle
STRIP_ASPECT = 200.0

#: Number of angular steps in the circle integral (per full turn)
CIRCLE_STEPS = 720


def _z(z) -> np.ndarray:
    """Depth as a float array; zero is nudged so the formulas stay finite."""
    return np.maximum(np.atleast_1d(np.asarray(z, dtype=float)), 1e-9)


# --------------------------------------------------------------------------- #
#  Boussinesq: rectangle
# --------------------------------------------------------------------------- #

def corner_factor(a: float, b: float, z) -> np.ndarray:
    """Influence factor Δσz/q under the corner of an a × b rectangle (Newmark).

    ``atan2`` takes care of the branch that the textbook formula corrects by
    adding π when m²n² > m² + n² + 1.
    """
    z = _z(z)
    if a <= 0 or b <= 0:
        return np.zeros_like(z)
    m, n = a / z, b / z
    s = m * m + n * n + 1.0
    root = np.sqrt(s)
    first = 2.0 * m * n * root / (s + m * m * n * n) * (s + 1.0) / s
    second = np.arctan2(2.0 * m * n * root, s - m * m * n * n)
    return (first + second) / (4.0 * np.pi)


def _signed(fn, x1: float, x2: float, y1: float, y2: float, *args) -> np.ndarray:
    """Superposes a corner solution over the rectangle [x1, x2] × [y1, y2]
    seen from the origin: each corner contributes with the sign of its
    quadrant, so the point may lie inside, on the edge or outside."""
    total = 0.0
    for x, sx in ((x2, 1.0), (x1, -1.0)):
        for y, sy in ((y2, 1.0), (y1, -1.0)):
            if x == 0.0 or y == 0.0:
                continue
            sign = sx * sy * math.copysign(1.0, x) * math.copysign(1.0, y)
            total = total + sign * fn(abs(x), abs(y), *args)
    return total


def rectangle(B: float, L: float, x: float, y: float, z) -> np.ndarray:
    """Δσz/q at plan point (x, y) under a B × L rectangle centred on the origin
    (B along x, L along y)."""
    result = _signed(corner_factor, -B / 2 - x, B / 2 - x, -L / 2 - y, L / 2 - y, z)
    return np.zeros_like(_z(z)) + result


# --------------------------------------------------------------------------- #
#  Boussinesq: strip and circle
# --------------------------------------------------------------------------- #

def strip(B: float, x: float, z) -> np.ndarray:
    """Δσz/q at offset x from the centre line of a strip of width B."""
    z = _z(z)
    b = B / 2.0
    t1 = np.arctan((x + b) / z)
    t2 = np.arctan((x - b) / z)
    return (t1 - t2 + np.sin(t1) * np.cos(t1) - np.sin(t2) * np.cos(t2)) / np.pi


def circle(R: float, d: float, z) -> np.ndarray:
    """Δσz/q at distance d from the centre of a circle of radius R.

    Integrating Boussinesq over the radius first leaves
    (1/2π)·∮ [g(r₁) − g(r₂)] dθ with g(r) = z³ / (z² + r²)^{3/2}, where r₁ and
    r₂ are where the ray from the point in direction θ enters and leaves the
    circle (r₁ = 0 for a point inside). For a circle both are explicit, so the
    double integral reduces to one, evaluated by the midpoint rule.
    """
    z = _z(z)
    if d <= 1e-12:
        return 1.0 - z ** 3 / (z * z + R * R) ** 1.5
    theta = (np.arange(CIRCLE_STEPS) + 0.5) * (2.0 * np.pi / CIRCLE_STEPS)
    disc = R * R - (d * np.sin(theta)) ** 2
    root = np.sqrt(np.maximum(disc, 0.0))
    r1 = np.where(disc > 0, np.maximum(-d * np.cos(theta) - root, 0.0), 0.0)
    r2 = np.where(disc > 0, np.maximum(-d * np.cos(theta) + root, 0.0), 0.0)
    zz = z[:, None]

    def g(r):
        return zz ** 3 / (zz * zz + r[None, :] ** 2) ** 1.5

    return (g(r1) - g(r2)).mean(axis=1)


# --------------------------------------------------------------------------- #
#  Approximate: 2:1
# --------------------------------------------------------------------------- #

def two_to_one(shape: str, B: float, L: float, z) -> np.ndarray:
    """Δσz/q by the 2:1 spread: the load over the area at depth z.

    It is an average over the loaded width, the same everywhere in plan.
    """
    z = _z(z)
    if shape == "strip":
        return B / (B + z)
    if shape == "circle":
        return B * B / (B + z) ** 2          # B is the diameter here
    return B * L / ((B + z) * (L + z))


# --------------------------------------------------------------------------- #
#  Dispatcher
# --------------------------------------------------------------------------- #

def influence(shape: str, B: float, L: float, point: tuple, z,
              method: str = "boussinesq") -> np.ndarray:
    """Δσz/q under a foundation at a plan point.

    ``point`` is (x, y) for a rectangle, (x,) for a strip and (d,) for a
    circle, all measured from the centre. ``B`` is the width, or the diameter
    of a circle.
    """
    if method == "two_to_one":
        return two_to_one(shape, B, L, z)
    if shape == "strip":
        return strip(B, point[0], z)
    if shape == "circle":
        return circle(B / 2.0, point[0], z)
    return rectangle(B, L, point[0], point[1], z)


# --------------------------------------------------------------------------- #
#  Steinbrenner: elastic settlement of a layered, finite-depth profile
# --------------------------------------------------------------------------- #

def steinbrenner_factors(a: float, b: float, H) -> tuple:
    """Steinbrenner's F1 and F2 under the corner of an a × b rectangle on an
    elastic layer of thickness H (a rigid base below it)."""
    H = np.atleast_1d(np.asarray(H, dtype=float))
    short, long_ = min(a, b), max(a, b)
    M = long_ / short
    N = np.maximum(H / short, 1e-12)
    s1 = math.sqrt(M * M + 1.0)
    s2 = np.sqrt(M * M + N * N)
    s3 = np.sqrt(M * M + N * N + 1.0)
    A0 = M * np.log((1.0 + s1) * s2 / (M * (1.0 + s3)))
    A1 = np.log((M + s1) * np.sqrt(1.0 + N * N) / (M + s3))
    A2 = M / (N * s3)
    F1 = (A0 + A1) / np.pi
    F2 = N / (2.0 * np.pi) * np.arctan(A2)
    zero = H <= 0
    F1 = np.where(zero, 0.0, F1)
    F2 = np.where(zero, 0.0, F2)
    return F1, F2


def steinbrenner_corner(a: float, b: float, H, nu: float) -> np.ndarray:
    """Settlement × E / q under the corner of an a × b flexible rectangle on
    a layer of thickness H (a length):  B·[(1 − ν²)F1 + (1 − ν − 2ν²)F2]."""
    F1, F2 = steinbrenner_factors(a, b, H)
    return min(a, b) * ((1.0 - nu * nu) * F1 + (1.0 - nu - 2.0 * nu * nu) * F2)


def elastic_depth_factor(shape: str, B: float, L: float, point: tuple, H,
                         nu: float) -> np.ndarray:
    """Settlement × E / q at a plan point for an elastic layer from the base
    down to depth H (a length). Differences between two depths give the
    settlement of a layer between them.

    A strip is a long rectangle; a circle is the square of the same area,
    with its points placed at the same fraction of the half-width.
    """
    H = np.atleast_1d(np.asarray(H, dtype=float))
    if shape == "strip":
        B_, L_, x, y = B, STRIP_ASPECT * B, point[0], 0.0
    elif shape == "circle":
        side = B / 2.0 * math.sqrt(math.pi)
        B_, L_ = side, side
        x, y = point[0] / (B / 2.0) * side / 2.0 if B > 0 else 0.0, 0.0
    else:
        B_, L_, x, y = B, L, point[0], point[1]
    result = _signed(steinbrenner_corner, -B_ / 2 - x, B_ / 2 - x,
                     -L_ / 2 - y, L_ / 2 - y, H, nu)
    return np.zeros_like(H) + result


# --------------------------------------------------------------------------- #
#  Embankments: trapezoidal strip loads (plane strain)
# --------------------------------------------------------------------------- #

#: Half-length of a strip treated as a rectangle for plane strain [m]; the
#: Steinbrenner factors are converged to machine precision long before it
PLANE_STRAIN_HALF_LENGTH = 1.0e5

#: Slices per slope when an embankment's elastic settlement is superposed
EMBANKMENT_SLICES = 16


def slope_run(height: float, angle: float) -> float:
    """Horizontal run of a slope of the given angle (degrees from horizontal)."""
    if angle >= 90.0:
        return 0.0
    return height / math.tan(math.radians(angle))


def embankment_vertices(crest: float, height: float, slope_left: float,
                        slope_right: float) -> tuple:
    """The load profile of an embankment as vertices (x, p/p_max), centred on
    the crest: zero at the toes, full over the crest."""
    run_l, run_r = slope_run(height, slope_left), slope_run(height, slope_right)
    xs = [-crest / 2 - run_l, -crest / 2, crest / 2, crest / 2 + run_r]
    return xs, [0.0, 1.0, 1.0, 0.0]


def linear_strip(xs, ps, x: float, z) -> np.ndarray:
    """Δσz/p under a piecewise-linear strip load p(ξ) given by vertices (xs, ps).

    Integrating Flamant's line load 2p z³/(π((ξ−x)² + z²)²) over a segment
    where p = A + Bξ gives, with u = ξ − x,
        (A + Bx)·[atan(u/z) + uz/(u² + z²)]/π − B·z³/(π(u² + z²))
    between the ends of the segment: exact, so no quadrature is needed.
    """
    z = _z(z)
    total = np.zeros_like(z)
    for (xa, pa), (xb, pb) in zip(zip(xs[:-1], ps[:-1]), zip(xs[1:], ps[1:])):
        if xb - xa <= 1e-12:
            continue
        slope = (pb - pa) / (xb - xa)
        level = pa - slope * xa + slope * x          # A + B·x

        def F(u):
            return (level * (np.arctan(u / z) + u * z / (u * u + z * z))
                    - slope * z ** 3 / (u * u + z * z)) / np.pi

        total = total + F(xb - x) - F(xa - x)
    return total


def embankment(crest: float, height: float, slope_left: float, slope_right: float,
               x: float, z) -> np.ndarray:
    """Δσz/(γ·H) at offset x from the crest centre, depth z below the ground."""
    xs, ps = embankment_vertices(crest, height, slope_left, slope_right)
    return linear_strip(xs, ps, x, z)


def embankment_two_to_one(crest: float, height: float, slope_left: float,
                          slope_right: float, z) -> np.ndarray:
    """Δσz/(γ·H) by the 2:1 spread of the equivalent uniform strip (same load)."""
    width = crest + 0.5 * (slope_run(height, slope_left) + slope_run(height, slope_right))
    z = _z(z)
    return width / (width + z) if width > 0 else np.zeros_like(z)


def plane_strip_elastic(x1: float, x2: float, H, nu: float) -> np.ndarray:
    """Settlement × E / p at the origin under a uniform strip [x1, x2] × (−∞, ∞)
    on a layer of thickness H: Steinbrenner on a very long rectangle."""
    H = np.atleast_1d(np.asarray(H, dtype=float))
    Lh = PLANE_STRAIN_HALF_LENGTH
    return np.zeros_like(H) + _signed(steinbrenner_corner, x1, x2, -Lh, Lh, H, nu)


def embankment_elastic_factor(crest: float, height: float, slope_left: float,
                              slope_right: float, x: float, H, nu: float,
                              slices: int = EMBANKMENT_SLICES) -> np.ndarray:
    """Settlement × E / (γ·H) at offset x under an embankment, for an elastic layer
    from the ground down to depth H.

    The crest is one uniform strip; each slope is cut into slices, each a
    uniform strip carrying the load at its middle. The solution is linear in
    the load, so the slices superpose.
    """
    H = np.atleast_1d(np.asarray(H, dtype=float))
    total = np.zeros_like(H)
    if crest > 0:
        total = total + plane_strip_elastic(-crest / 2 - x, crest / 2 - x, H, nu)
    for run, side in ((slope_run(height, slope_left), -1.0),
                      (slope_run(height, slope_right), 1.0)):
        if run <= 0:
            continue
        width = run / slices
        for k in range(slices):
            # distance from the crest edge to the slice's near and far sides
            near, far = k * width, (k + 1) * width
            weight = 1.0 - (k + 0.5) / slices
            a = side * (crest / 2 + near) - x
            b = side * (crest / 2 + far) - x
            total = total + weight * plane_strip_elastic(min(a, b), max(a, b), H, nu)
    return total
