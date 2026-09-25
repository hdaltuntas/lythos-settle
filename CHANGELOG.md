# Changelog

## Unreleased

- The licence changes from MIT to the GNU Affero General Public License, version 3
  (`AGPL-3.0-only`). Versions already published keep the MIT licence they were released under.

## 0.1.0

First release: settlement analysis of shallow foundations, built on the architecture of
the other Lythos programs (local HTTP server + browser interface, schema-driven forms,
bilingual English / Turkish throughout, PDF / HTML / DOCX reports, `.settle` project files,
command line, parametric / reliability studies).

- Stress increase by Boussinesq (rectangle, strip, circle — any point in plan) or 2:1.
- Immediate settlement: layered elastic (Steinbrenner) or Schmertmann (1978).
- Primary consolidation from Cc, Cr, e0, OCR; secondary compression from Cα, reduced to
  Cα·Cr/Cc where the clay stays over-consolidated.
- Terzaghi time–settlement curve, t50 and t90 per clay layer.
- Settlement at the centre, characteristic point, edge and corner; rigid foundations;
  angular distortion; checks against allowable settlement and distortion.
- Embankments: crest width, height, left / right slope angles and fill unit weight; exact
  stress under the trapezoidal load, plane-strain elastic settlement, settlement at the crest
  centre, crest edge, mid-slope and toe.
- Settlement profile across the section, for footings and embankments.
- Studies: one-at-a-time, Latin hypercube, Monte Carlo; statistics, probability of
  exceedance with 95 % CI and β, Spearman sensitivities, CSV / XLSX export.
