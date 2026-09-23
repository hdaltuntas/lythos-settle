"""The input schema, the defaults and the conversions to and from project files."""
import pytest

from lythossettle import forms
from lythossettle.config import DEFAULT_CONFIG
from lythossettle.engine import SettlementAnalysis


@pytest.mark.parametrize("lang", ["en", "tr"])
def test_every_field_of_the_schema_has_a_label_and_a_default(lang):
    schema = forms.schema(lang)
    values = forms.defaults(lang)
    for section in ("project", "foundation", "options", "study"):
        for group in schema[section]["groups"]:
            assert group["title"]
            for field in group["fields"]:
                assert field["label"] and field["key"] in values
    assert [c["key"] for c in schema["soil"]["columns"]][:3] == ["name", "thickness", "behaviour"]
    assert all(c["label"] for c in schema["soil"]["columns"])


def test_the_languages_differ_where_they_should():
    en, tr = forms.schema("en"), forms.schema("tr")
    assert en["foundation"]["groups"][0]["title"] == "Foundation"
    assert tr["foundation"]["groups"][0]["title"] == "Temel"


def test_the_defaults_are_the_default_project():
    assert forms.to_config(forms.defaults()) == {**DEFAULT_CONFIG,
                                                 "project_info": DEFAULT_CONFIG["project_info"]}


def test_a_project_file_round_trips():
    values = forms.defaults()
    values.update(B=6.5, water_depth=4.0, rigidity="rigid", s_allow=60.0, study_n=77)
    values["soil_profile"][2]["Cc"] = 0.41
    values["study_variables"] = [{"path": "foundation.q", "mode": "range", "min": 1, "max": 2}]
    project = forms.project_file(values)
    assert project["format"] == forms.FILE_FORMAT
    back = forms.from_config(project)
    for key in ("B", "water_depth", "rigidity", "s_allow", "study_n"):
        assert back[key] == values[key]
    assert back["soil_profile"][2]["Cc"] == 0.41
    assert back["study_variables"][0]["path"] == "foundation.q"


def test_a_partial_project_file_keeps_the_defaults():
    values = forms.from_config({"foundation": {"q": 250.0}})
    assert values["q"] == 250.0
    assert values["B"] == DEFAULT_CONFIG["foundation"]["B"]
    assert len(values["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])


def test_empty_and_unusable_table_rows_are_dropped():
    values = forms.defaults()
    values["soil_profile"] = values["soil_profile"] + [{"name": "blank", "thickness": None},
                                                       {"name": "zero", "thickness": 0}]
    assert len(forms.to_config(values)["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])


def test_empty_cells_fall_back_to_defaults_and_unknown_choices_are_ignored():
    values = forms.defaults()
    values.update(q="", shape="hexagon", stress_method=None)
    values["soil_profile"][0]["E"] = None
    cfg = forms.to_config(values)
    assert cfg["foundation"]["q"] == DEFAULT_CONFIG["foundation"]["q"]
    assert cfg["foundation"]["shape"] == "rectangle"
    assert cfg["options"]["stress_method"] == "boussinesq"
    assert cfg["soil_profile"][0]["E"] == DEFAULT_CONFIG["soil_profile"][0]["E"]
    SettlementAnalysis(cfg).run()


def test_variable_choices_carry_label_and_project_value():
    choices = forms.variable_choices(forms.defaults(), "en")
    by_path = {c["value"]: c for c in choices}
    assert by_path["foundation.q"]["base"] == DEFAULT_CONFIG["foundation"]["q"]
    assert by_path["soil_profile.2.Cc"]["label"] == "Soft clay · Cc"
