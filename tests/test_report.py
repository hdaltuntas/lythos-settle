"""The calculation report, in each format and both languages."""
import pytest

from lythossettle import forms, report
from lythossettle.engine import SettlementAnalysis
from lythossettle.study import Study, StudyVariable


@pytest.fixture(scope="module")
def analysis():
    a = SettlementAnalysis(forms.to_config(forms.defaults()))
    a.run()
    return a


@pytest.fixture(scope="module")
def figures(analysis):
    return report.render_figures(analysis, "en")


@pytest.mark.parametrize("lang", ["en", "tr"])
def test_the_html_has_every_section(analysis, figures, lang):
    text = report.build_html(analysis, lang, figures)
    T = report.TEXTS[lang]
    for key in ("sec_inputs", "sec_soil", "sec_stress", "sec_points", "sec_time", "sec_checks",
                "sec_figs", "sec_notes"):
        assert T[key] in text
    assert text.count("data:image/png;base64,") == len(figures)
    assert "Soft clay" in text


def test_the_numbers_in_the_report_are_the_analysis_numbers(analysis, figures):
    text = report.build_html(analysis, "en", figures)
    assert f"{analysis.results['total']:,.1f}" in text
    assert f"{analysis.results['q_net']:,.1f}" in text


def test_the_report_texts_have_the_same_keys_in_both_languages():
    assert set(report.TEXTS["en"]) == set(report.TEXTS["tr"])
    assert len(report.TEXTS["en"]["notes"]) == len(report.TEXTS["tr"]["notes"])


def test_every_format_is_written(analysis, tmp_path):
    report.export_report(str(tmp_path / "r.pdf"), analysis, "tr")
    assert (tmp_path / "r.pdf").read_bytes()[:4] == b"%PDF"
    report.export_report(str(tmp_path / "r.html"), analysis, "en")
    assert "<html" in (tmp_path / "r.html").read_text(encoding="utf-8")[:100]
    report.export_report(str(tmp_path / "r.docx"), analysis, "en")
    assert (tmp_path / "r.docx").read_bytes()[:2] == b"PK"


def test_a_study_becomes_section_seven(analysis, tmp_path):
    study = Study(analysis.config, [StudyVariable("foundation.q", "dist", dist="normal",
                                                  mean=100, cov=0.1, label="q")], "lhs", 20)
    study.run()
    figures = report.render_figures(analysis, "en", keys=["schematic"])
    figures.update(report.render_study_figures(study, "en"))
    text = report.build_html(analysis, "en", figures, study=study)
    assert report.TEXTS["en"]["sec_study"] in text
    assert "study_tornado" in "".join(figures)
    report.export_pdf(str(tmp_path / "s.pdf"), analysis, "en", study)
    assert (tmp_path / "s.pdf").stat().st_size > 10000
