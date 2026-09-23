# Theory

What Lythos Settle computes, and where the method stops being valid. Depth `z` is
measured from the ground surface; `z_b = z − Df` from the foundation base.

## 1. In-situ stresses

σv0(z) = Σ γ·Δz above the water table and Σ γsat·Δz below it; u0 = γw·(z − z_w) below the
water table; σ'v0 = σv0 − u0. The last layer is taken as continuing below the profile for
the stress calculation only. In a cohesive layer σ'p = OCR·σ'v0 (OCR constant per layer;
OCR < 1 is not supported and is set to 1 with a warning).

## 2. Net pressure

q_net = q − σv0(Df) when the excavated overburden is deducted, q otherwise. Once the pore
pressures have equilibrated the effective stress change equals the total stress change, so
the same q_net drives both the elastic and the consolidation settlement. A zero or negative
q_net is a compensated foundation: nothing settles.

## 3. Stress increase

**Rectangle** — Newmark's integration of Boussinesq under the corner of an a × b area,
m = a/z, n = b/z:

    I = 1/(4π) · [ 2mn√(m²+n²+1)/(m²+n²+1+m²n²) · (m²+n²+2)/(m²+n²+1)
                   + atan2(2mn√(m²+n²+1), m²+n²+1−m²n²) ]

`atan2` takes the branch that the textbook formula corrects by adding π. Any plan point
(inside, on the edge or outside) is the signed sum of four corner rectangles.

**Strip** — Δσ/q = [θ₁ − θ₂ + sinθ₁cosθ₁ − sinθ₂cosθ₂]/π with θ = atan((x ± B/2)/z).

**Circle** — integrating Boussinesq over the radius leaves
Δσ/q = (1/2π) ∮ [g(r₁) − g(r₂)] dθ, g(r) = z³/(z² + r²)^{3/2}, where r₁, r₂ are the
distances at which the ray from the point in direction θ enters and leaves the circle. Both
are explicit for a circle, so the integral is one-dimensional and exact up to the quadrature
(720 steps); at the centre the closed form 1 − (z²/(z²+R²))^{3/2} is used.

**2:1** — q·B·L/((B+z)(L+z)), q·B/(B+z), q·D²/(D+z)²: an average over the widened area,
the same at every point, so under 2:1 the consolidation settlement does not vary in plan.

**Embankment** — a long fill on the ground surface: crest width b, height H, slope angles
β_L, β_R, unit weight γ. The load is p(x) = γH under the crest, falling linearly to zero over
the slope runs H/tan β. For a segment where p = A + Bξ, Flamant's line load
2p z³/(π((ξ−x)² + z²)²) integrates, with u = ξ − x, to

    Δσ = (A + Bx)·[atan(u/z) + uz/(u² + z²)]/π − B·z³/(π(u² + z²))

between the ends of the segment; the embankment is the sum of its three segments, so the
stress is exact at any point (plane strain). Under 2:1 the fill is replaced by the uniform
strip of the same load, of width b + (run_L + run_R)/2. The evaluation points are the crest
centre, the crest edge, the middle of the (right) slope and its toe. The elastic
settlement superposes plane-strain Steinbrenner strips — the crest as one, each slope as 16
slices carrying the load at their middle (converged to 0.2 %). A fill is flexible;
Schmertmann's footing diagram is not applied to it, and its angular distortion is not
checked. The fill's own compression, undrained lateral spreading and stability are outside
the program.

## 4. Influence depth

The profile below the base is cut into sublayers (0.25 m by default). Settlement is summed
down to the bottom of the deepest sublayer where Δσ at the centre is still at least the
chosen fraction of σ'v0 (0.1 by default; 0 sums the whole profile). The base of the profile
is incompressible; the program warns when Δσ at the base is still ≥ 0.1·σ'v0.

## 5. Immediate settlement

**Elastic (Steinbrenner).** Under the corner of a flexible a × b rectangle on an elastic
layer of thickness H over a rigid base, with M = L/B, N = H/B (B the shorter side):

    s = q·B/E · [ (1 − ν²)·F1 + (1 − ν − 2ν²)·F2 ]
    F1 = (A0 + A1)/π,   F2 = N/(2π)·atan(A2)
    A0 = M·ln[(1+√(M²+1))·√(M²+N²) / (M·(1+√(M²+N²+1)))]
    A1 = ln[(M+√(M²+1))·√(1+N²) / (M+√(M²+N²+1))]
    A2 = M / (N·√(M²+N²+1))

The settlement of a layer between z₁ and z₂ below the base is q/E times the difference of
the bracket at the two depths (the layered method), each layer with its own E and ν, and
any point is superposed from four corners. A strip is a rectangle 200 B long; a circle is
the square of the same area, its points placed at the same fraction of the half-width.
Clay layers use their undrained E and ν (≈ 0.5), which makes this the undrained
distortion settlement that precedes consolidation.

**Schmertmann et al. (1978)**, granular layers only:

    s = C1·C2·q_net·Σ (Iz/E)·Δz
    C1 = 1 − 0.5·σ'v0(Df)/q_net ≥ 0.5,   C2 = 1 + 0.2·log10(t/0.1 yr)
    Izp = 0.5 + 0.1·√(q_net/σ'vp),   σ'vp at the depth of the peak

The influence diagram runs from Iz = 0.1 at the base to Izp at B/2 and zero at 2B for
L/B = 1, from 0.2 to Izp at B and zero at 4B for L/B ≥ 10, and is interpolated linearly in
L/B between. The result is the footing's settlement; at the other points it is scaled by
the ratio of the elastic settlement of the same granular sublayers at that point to the one
at the centre. E is entered directly (Schmertmann suggests E = 2.5·qc for axisymmetric and
3.5·qc for plane-strain loading).

## 6. Primary consolidation

For each clay sublayer, at each evaluation point, with σ'f = σ'v0 + Δσ:

    Δe = Cr·log10(min(σ'f, σ'p)/σ'v0) + Cc·log10(max(σ'f, σ'p)/σ'p)
    s  = Σ Δe/(1 + e0) · Δz

No Skempton–Bjerrum correction is applied; the one-dimensional value is conservative for
over-consolidated clay under a narrow footing.

## 7. Time

Terzaghi's average degree of consolidation for a uniform initial excess pore pressure,
U = 1 − Σ 2/M²·exp(−M²Tv), M = π(2m+1)/2, with √(4Tv/π) for Tv < 10⁻³; Tv = cv·t/H_dr²,
H_dr = H/2 for double and H for single drainage, H the thickness of the layer below the
base. Tv(U) is found by bisection, so U(Tv(U)) = U exactly. Each clay layer consolidates
independently; interaction between layers through a common drainage boundary is ignored.
A clay without cv is taken as consolidating at once.

## 8. Secondary compression

From the end of primary consolidation, taken as U = 95 % (t_p), to the design life:
s = Cα/(1 + e0)·Δz·log10(t/t_p). Since Cα/Cc is a soil constant (Mesri), where σ'f stays
below σ'p the clay creeps along the recompression line and Cα·Cr/Cc is used instead. e0 is
used for (1 + e_p).

## 9. Rigid foundation, distortion, checks

A rigid foundation settles uniformly by the settlement of its characteristic point
(Grasshoff: 0.74 of the half-widths from the centre in a rectangle or strip, 0.845·R in a
circle). The angular distortion of a flexible foundation is
β = |s_centre − s_edge| / (B/2) (R for a circle); for a rigid one it is not checked. The
total settlement of the governing point (centre, or characteristic point) and β are
checked against their allowable values.

## 10. Studies

Inputs vary as a range (uniform in LHS / Monte Carlo, n evenly spaced points in a
one-at-a-time sweep) or a distribution (normal; lognormal with the given mean and CoV;
uniform over mean ± √3·σ). Exceedance probabilities P = k/n carry a Wilson 95 % interval;
β = −Φ⁻¹(P), reported as "> −Φ⁻¹(3/n)" when nothing exceeded. Sensitivities are Spearman
rank correlations.
