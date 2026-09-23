"""Sampling, the study runner and its post-processing."""
import math

import numpy as np
import pytest

from lythossettle import forms, study_plots
from lythossettle.i18n import TRANSLATIONS
from lythossettle.study import (
    Study,
    StudyVariable,
    available_variables,
    pretty_label,
    reliability,
    sample,
    spearman,
    to_csv,
    to_xlsx,
)

BASE = forms.to_config(forms.defaults())


def test_latin_hypercube_puts_one_sample_in_each_stratum():
    var = StudyVariable("foundation.q", "range", 0.0, 1.0)
    rows = sample([var], "lhs", 50, seed=3)
    values = np.sort([row["foundation.q"] for row in rows])
    strata = np.floor(values * 50).astype(int)
    assert list(strata) == list(range(50))


def test_a_lognormal_variable_has_the_mean_and_cov_it_was_given():
    var = StudyVariable("soil_profile.2.Cc", "dist", dist="lognormal", mean=0.3, cov=0.25)
    values = var.ppf((np.arange(20000) + 0.5) / 20000)
    assert values.mean() == pytest.approx(0.3, rel=0.01)
    assert values.std() / values.mean() == pytest.approx(0.25, rel=0.02)
    assert values.min() > 0


def test_a_uniform_variable_spans_mean_plus_minus_root3_sd():
    var = StudyVariable("foundation.q", "dist", dist="uniform", mean=100, cov=0.1)
    lo, hi = var.ppf([1e-9, 1 - 1e-9])
    assert lo == pytest.approx(100 - math.sqrt(3) * 10, rel=1e-6)
    assert hi == pytest.approx(100 + math.sqrt(3) * 10, rel=1e-6)


def test_a_sweep_has_one_row_per_point_per_range_variable():
    variables = [StudyVariable("foundation.q", "range", 80, 120, n_points=5),
                 StudyVariable("foundation.B", "range", 6, 10, n_points=3),
                 StudyVariable("soil_profile.2.Cc", "dist", dist="normal", mean=0.3, cov=0.1)]
    rows = sample(variables, "oat")
    assert len(rows) == 8
    assert {row["_varied"] for row in rows} == {"foundation.q", "foundation.B"}


@pytest.mark.parametrize("bad", [
    dict(mode="range", vmin=2, vmax=1),
    dict(mode="dist", dist="weibull"),
    dict(mode="dist", dist="lognormal", mean=-1),
    dict(mode="sideways"),
])
def test_impossible_variables_are_refused(bad):
    with pytest.raises(ValueError):
        StudyVariable("foundation.q", **bad)


def test_the_study_offers_clay_inputs_only_for_clay():
    paths = [path for path, _ in available_variables(BASE)]
    assert "soil_profile.2.Cc" in paths          # the soft clay
    assert "soil_profile.1.Cc" not in paths      # a sand
    assert "foundation.L" in paths
    L = TRANSLATIONS["tr"]
    assert pretty_label(BASE, "soil_profile.2.Cc", L) == "Soft clay · Cc"
    assert pretty_label(BASE, "foundation.q", L) == "Temel · q"


def test_a_variable_the_project_has_not_got_is_refused():
    with pytest.raises(ValueError):
        Study(BASE, [StudyVariable("soil_profile.9.E", "range", 1, 2)], "lhs", 5)


@pytest.fixture(scope="module")
def mc():
    variables = [
        StudyVariable("foundation.q", "dist", dist="normal", mean=100, cov=0.15, label="q"),
        StudyVariable("soil_profile.2.Cc", "dist", dist="lognormal", mean=0.32, cov=0.3,
                      label="Cc"),
        StudyVariable("soil_profile.3.E", "range", 40, 80, label="E sand"),
    ]
    s = Study(BASE, variables, "lhs", 120, seed=7)
    done = []
    s.run(progress=lambda d, t: done.append((d, t)))
    s.done = done
    return s


def test_a_study_runs_every_sample_and_reports_progress(mc):
    assert len(mc.rows) == 120 and mc.done[-1] == (120, 120)
    assert mc.summary["n_ok"] == 120
    assert mc.summary["stats"]["s_total"]["p5"] < mc.summary["stats"]["s_total"]["p95"]


def test_the_load_and_the_compressibility_drive_the_settlement(mc):
    rho = mc.summary["spearman"]["s_total"]
    assert rho["foundation.q"] > 0.5
    assert rho["soil_profile.2.Cc"] > 0.2
    assert abs(rho["soil_profile.3.E"]) < rho["foundation.q"]


def test_the_probability_of_exceedance_is_counted(mc):
    rel = mc.summary["reliability"]["ls_settlement"]
    values = np.array([row["s_total"] for row in mc.rows])
    assert rel["n_fail"] == int(np.sum(values > 150.0))
    assert rel["pf_lo"] <= rel["pf"] <= rel["pf_hi"]


def test_reliability_index_and_interval():
    r = reliability(np.array([1.0, 2.0, 3.0, 4.0]), 3.5)
    assert r["pf"] == 0.25 and r["n_fail"] == 1
    assert r["beta"] == pytest.approx(0.6745, abs=1e-3)
    assert reliability(np.array([1.0, 2.0]), 5.0)["beta"] == float("inf")


def test_spearman_is_a_rank_correlation():
    x = np.arange(10.0)
    assert spearman(x, x ** 3) == pytest.approx(1.0)
    assert spearman(x, -np.exp(x)) == pytest.approx(-1.0)
    assert math.isnan(spearman(x[:2], x[:2]))


def test_a_cancelled_study_keeps_what_it_has(mc):
    s = Study(BASE, mc.variables, "mc", 50, seed=1)
    calls = []
    s.run(is_cancelled=lambda: len(calls) >= 5, progress=lambda d, t: calls.append(d))
    assert len(s.rows) == 5


def test_an_impossible_sample_is_an_error_row_not_a_crash():
    var = StudyVariable("soil_profile.2.E", "range", -5.0, 5.0, n_points=3)
    s = Study(BASE, [var], "oat")
    s.run()
    errors = [row for row in s.rows if row["error"]]
    assert errors and len(errors) < len(s.rows)


def test_the_samples_export_to_csv_and_xlsx(mc, tmp_path):
    to_csv(mc, str(tmp_path / "s.csv"))
    lines = (tmp_path / "s.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 121 and lines[0].startswith("foundation.q,")
    to_xlsx(mc, str(tmp_path / "s.xlsx"))
    assert (tmp_path / "s.xlsx").stat().st_size > 1000


@pytest.mark.parametrize("lang", ["en", "tr"])
def test_the_summary_text_is_in_the_language_asked_for(mc, lang):
    text = study_plots.summary_text(mc, TRANSLATIONS[lang])
    assert TRANSLATIONS[lang]["st_title"] in text
    assert TRANSLATIONS[lang]["ls_settlement"] in text
