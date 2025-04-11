import pytest
from unittest.mock import mock_open, patch
from packaging import version
from helm_chart_updater.helm_charts import ChartFileProcessor


@pytest.fixture
def sample_yaml_content():
    return """
apiVersion: v2
dependencies:
- name: microservice
  repository: oci://harbor.example.com/foundation
  version: 5.1.0
description: ms-example
name: ms-example
version: 2.0.2
"""


@pytest.fixture
def chart_file_processor(tmp_path, sample_yaml_content):
    chart_file = tmp_path / "Chart.yaml"
    chart_file.write_text(sample_yaml_content)
    return ChartFileProcessor(chart_file, "microservice", "4.0.0", "6.0.0")


def test_init(chart_file_processor):
    assert chart_file_processor.chart_name == "microservice"
    assert chart_file_processor.chart_min_version == "4.0.0"
    assert chart_file_processor.chart_max_version == "6.0.0"
    assert chart_file_processor.chart_version == "5.1.0"


def test_load_yaml(chart_file_processor):
    loaded_data = chart_file_processor._load_yaml()
    assert loaded_data["name"] == "ms-example"
    assert loaded_data["version"] == "2.0.2"
    assert len(loaded_data["dependencies"]) == 1
    assert loaded_data["dependencies"][0]["name"] == "microservice"


@patch("builtins.open", new_callable=mock_open)
def test_save_yaml(mock_file, chart_file_processor):
    chart_file_processor._save_yaml()
    mock_file.assert_called_once_with(chart_file_processor.chart_file, "w")
    mock_file().write.assert_called()


def test_get_chart_version(chart_file_processor):
    assert chart_file_processor.get_chart_version() == "5.1.0"


def test_get_chart_version_invalid_chart_name(chart_file_processor):
    chart_file_processor.chart_name = "invalid_chart_name"
    assert chart_file_processor.get_chart_version() is None


def test_version_check(chart_file_processor):
    chart_file_processor.chart_version = "5.1.0"
    assert chart_file_processor.chart_min_version == "4.0.0"
    assert chart_file_processor.chart_max_version == "6.0.0"
    assert chart_file_processor.version_check()


def test_version_check_version_out_of_range(chart_file_processor):
    chart_file_processor.chart_version = "7.1.0"
    assert chart_file_processor.chart_min_version == "4.0.0"
    assert chart_file_processor.chart_max_version == "6.0.0"
    assert not chart_file_processor.version_check()


def test_version_check_version_with_invalid_version(chart_file_processor):
    chart_file_processor.chart_version = "asd"
    assert chart_file_processor.chart_min_version == "4.0.0"
    assert chart_file_processor.chart_max_version == "6.0.0"
    with pytest.raises(version.InvalidVersion):
        chart_file_processor.version_check()


def test_update_chart_version(chart_file_processor):
    new_version = "5.2.0"
    assert (
        chart_file_processor.update_chart_version(new_version)
        == f"Chart {chart_file_processor.chart_name} updated to {new_version} version"
    )


def test_update_chart_version_to_actual_version(chart_file_processor):
    new_version = "5.1.0"
    assert chart_file_processor.chart_version == new_version
    assert (
        chart_file_processor.update_chart_version(new_version)
        == f"Chart version is already at the desired version: {new_version}  at {chart_file_processor.chart_file} file"
    )


def test_update_chart_version_but_dependency_not_found(chart_file_processor):
    new_version = "5.2.0"
    chart_file_processor.chart_name = "microfrontend"
    assert (
        chart_file_processor.update_chart_version(new_version)
        == f"{chart_file_processor.chart_name} dependency not found in the {chart_file_processor.chart_file} file"
    )


def test_update_chart_version_but_chart_version_not_meet_requirements(
    chart_file_processor,
):
    new_version = "5.2.0"
    chart_file_processor.chart_version = "7.1.0"
    assert chart_file_processor.chart_min_version == "4.0.0"
    assert chart_file_processor.chart_max_version == "6.0.0"
    assert (
        chart_file_processor.update_chart_version(new_version)
        == f"Chart version {chart_file_processor.chart_version} not eligible for the requirements {version.parse(chart_file_processor.chart_min_version)} <= {version.parse(chart_file_processor.chart_version)} <= {version.parse(chart_file_processor.chart_max_version)} at {chart_file_processor.chart_file} file to update it's version"
    )


def test_update_chart_version_invalid_version(chart_file_processor):
    new_version = "invalid_version"
    with pytest.raises(version.InvalidVersion):
        chart_file_processor.update_chart_version(new_version)
