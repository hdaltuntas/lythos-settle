**English** | [Türkçe](https://github.com/hdaltuntas/lythos-settle/blob/main/README.tr.md)

# Lythos Settle

[![Tests](https://github.com/hdaltuntas/lythos-settle/actions/workflows/tests.yml/badge.svg)](https://github.com/hdaltuntas/lythos-settle/actions/workflows/tests.yml)

Settlement analysis of shallow foundations, driven from your browser. A rectangular, strip
or circular foundation on a layered soil profile is analysed for **how much** it settles
and **how fast**:

1. **Stresses** — in-situ σv0, u0, σ'v0 and σ'p; the stress increase beneath the foundation
   by Boussinesq (Newmark's rectangle, the strip and the circle solutions) or by the 2:1
   spread, at the centre, the characteristic point, the middle of the long edge and the corner.
2. **Immediate settlement** — layered elastic (Steinbrenner) in every layer, or
   Schmertmann (1978) in the granular layers.
3. **Consolidation** — primary settlement of the clay layers from Cc, Cr, e0 and σ'p, and
   secondary compression from Cα up to the design life.
4. **Time** — Terzaghi's one-dimensional consolidation, each clay layer draining on its own;
   t50, t90 and the time–settlement curve.
5. **Checks** — total settlement and angular distortion against their allowable values.

On top of it, a **parametric or reliability study** sweeps any input — a range, or a
distribution — and reports sensitivities and the probability of exceeding the allowable
settlement or distortion, with a confidence interval and the reliability index β.

The whole program — every label, result text, figure and report — is bilingual in
**English and Turkish**, switchable while it runs.

The interface is a small HTTP server on your own machine, driven from a browser. That
keeps the program usable over a remote session or inside a container, where a desktop
toolkit would need a display it does not have, and it costs no dependency beyond the
standard library.

> This is the sibling of [LythosFEA](https://github.com/hdaltuntas/lythos),
> [Lythos Kinematic](https://github.com/hdaltuntas/lythoskinematic),
> [Lythos SPWA](https://github.com/hdaltuntas/lythosspwa) and
> [LythosLE](https://github.com/hdaltuntas/lythosle), and follows the same architecture.

## Screenshots

| Results summary | Time–settlement |
|---|---|
| ![Results summary](https://raw.githubusercontent.com/hdaltuntas/lythos-settle/main/screenshots/settle_summary.png) | ![Time–settlement](https://raw.githubusercontent.com/hdaltuntas/lythos-settle/main/screenshots/settle_time.png) |

| Reliability study | Settlement with depth, dark theme, Turkish |
|---|---|
| ![Study](https://raw.githubusercontent.com/hdaltuntas/lythos-settle/main/screenshots/settle_study.png) | ![Settlement with depth](https://raw.githubusercontent.com/hdaltuntas/lythos-settle/main/screenshots/settle_depth_dark_tr.png) |

## Install & run

From a clone, with nothing installed but the scientific stack:

```bash
pip install numpy matplotlib reportlab
python main.py
```

or install it and use the command:

```bash
pip install .
lythos-settle                      # opens the interface in your browser
```

`main.py` puts its own directory first on the import path, so the clone's code is what
runs even when `lythossettle` is also installed.

Python 3.10+ is required. Word reports need `python-docx` and the spreadsheet export of a
study needs `openpyxl`; both are extras (`pip install ".[docx,xlsx]"`).

## Command line

```bash
lythos-settle                                  # web interface (the default)
lythos-settle web --port 9000 --lang tr --no-browser
lythos-settle example -o project.settle        # a starter project file
lythos-settle run project.settle -o report.pdf # analyse, print the results, write a report
lythos-settle study project.settle -o samples.csv
```

`run` and `study` read the same `.settle` file the interface saves, so a case set up in
the browser can be re-run unattended.

## Inputs

* **Foundation:** shape (rectangle, strip, circle), B (diameter of a circle), L, depth Df,
  gross bearing pressure q; optionally the excavated overburden is deducted
  (q_net = q − σv0(Df)).
* **Groundwater:** depth of the water table, γw.
* **Soil profile**, from the surface down, one row per layer: thickness, granular or
  cohesive, γ, γsat, E, ν, and for the clays Cc, Cr, e0, OCR, cv, Cα and single / double
  drainage. E is the drained modulus of a sand and the undrained modulus of a clay.
* **Options:** stress distribution, immediate-settlement method, flexible or rigid
  foundation, sublayer thickness, influence-depth ratio Δσ/σ'v0, design life, Schmertmann's
  creep factor.
* **Criteria:** allowable total settlement and angular distortion (1/x).

## What it computes

| quantity | method |
|---|---|
| Δσ under a rectangle | Newmark's integration of Boussinesq, superposed for any point |
| Δσ under a strip / circle | closed form / exact one-dimensional integral over the polar angle |
| Δσ, approximate | 2:1 spread |
| immediate settlement | Steinbrenner F1, F2 on each layer (layered elastic), or Schmertmann (1978) with C1, C2 and the L/B-interpolated influence diagram |
| primary consolidation | Cr up to σ'p = OCR·σ'v0, Cc beyond it, sublayer by sublayer at each point |
| secondary compression | Cα/(1+e0)·H·log(t/t_p) from U = 95 % to the design life; Cα·Cr/Cc where the clay stays over-consolidated |
| time | Terzaghi U(Tv), per clay layer, H_dr = H/2 or H |
| rigid foundation | settlement of the characteristic point (0.74·B/2, 0.74·L/2; 0.845·R) |
| angular distortion | (s_centre − s_edge) / (B/2) |

The derivations and their limits are in [docs/theory.md](https://github.com/hdaltuntas/lythos-settle/blob/main/docs/theory.md).

## Figures

Section with the Boussinesq stress bulb · stresses with depth (σ'v0, σ'v0 + Δσ, σ'p and the
influence-depth criterion) · influence factors at each point with Schmertmann's Iz ·
cumulative settlement with depth · time–settlement curve · settlement components at each
point. Study figures: one-at-a-time sweep, histogram, scatter, tornado.

## Reports

Choose PDF, self-contained HTML or Word in the header and press *Export report…*. The
report carries the inputs, the stresses, the settlement at each point and in each layer,
the Schmertmann factors, the consolidation times, the checks, the figures, the warnings,
the method notes and — if one was run — the study, in whichever language the interface is
in. All three formats are assembled from one place, so they say the same thing.

## Project files (`.settle`)

JSON. *Save* writes the inputs and the study definition; *Open…* reads them back. Missing
entries keep their defaults.

## Modules

| file | content |
|---|---|
| `lythossettle/stress.py` | Boussinesq (rectangle, strip, circle), 2:1, Steinbrenner |
| `lythossettle/consolidation.py` | Terzaghi U(Tv) and its inverse, compression of clay, secondary compression |
| `lythossettle/engine.py` | The settlement analysis: profile, sublayers, points, checks, time curve |
| `lythossettle/study.py`, `study_plots.py` | Parametric (one at a time) and reliability (LHS / Monte Carlo) studies, statistics, P of exceedance with 95 % CI and β, Spearman sensitivities, CSV / XLSX |
| `lythossettle/plotting.py`, `plot_style.py`, `render.py` | Matplotlib figures, theme-aware, off-screen |
| `lythossettle/report.py`, `pdf.py` | Calculation report: one HTML assembly, exported as PDF (reportlab), HTML or DOCX |
| `lythossettle/forms.py` | Input schema and readers; converts between the interface's flat values and the engine's configuration |
| `lythossettle/summary.py` | The results as cards and as text, for the browser and the command line alike |
| `lythossettle/i18n.py` | Every text, English and Turkish, written side by side |
| `lythossettle/web/` | The local HTTP server, the session, and the browser interface |

## Development

```bash
pip install -e ".[dev]"
pytest -q                 # engine against hand calculations, stresses against tables, study, report, web, packaging
ruff check .
```

The tests check the stress solutions against published values and brute-force integrals,
the engine against closed-form cases (a square on an elastic half-space, a one-dimensional
clay layer, Schmertmann by hand), the report in all three formats, the input schema and its
file round-trips, and the interface itself — the session and the HTTP layer both, so the
browser is exercised without a browser.

Releasing to PyPI is described in [docs/releasing.md](https://github.com/hdaltuntas/lythos-settle/blob/main/docs/releasing.md);
`tools/upload_to_pypi.py` does it from an editor, without a terminal.

## License

[MIT](https://github.com/hdaltuntas/lythos-settle/blob/main/LICENSE) © 2026 Hasan Deniz Altuntaş
