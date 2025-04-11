import pytest
from unittest.mock import mock_open, patch
from packaging import version
from helm_chart_updater.helm_values import (
    ValuesFileProcessor,
    convert_key_list_to_dot_notation,
)


@pytest.fixture
def sample_yaml_content():
    return """
microservice:
    image:
        repository: dockerhub.com/apache/dummy-image
        tag: v1.2.0
    annotations:
        reloader.stakater.com/auto: 'true'
    podAnnotations:
        sidecar.istio.io/inject: 'true'
    env:
      - name: SERVER_HOST
        value: 0.0.0.0
      - name: SERVER_PORT
        value: '80'
    prometheus:
        enabled: true
        path: /metrics
        port: 4000
        scrape: 'true'
    service:
        type: ClusterIP
        port: 3000
        targetPort: 3000
    fullnameOverride: ms-dummy-service
    nameOverride: ms-dummy-service
    resources:
        requests:
          memory: 256Mi
          cpu: 50m
        limits:
          memory: 512Mi
          cpu: 200m
    livenessProbe:
        httpGet:
          path: /health/liveness
          port: 3000
        initialDelaySeconds: 60
        failureThreshold: 5
        timeoutSeconds: 1
    readinessProbe:
        httpGet:
          path: /health/readiness
          port: 3000
        initialDelaySeconds: 60
        failureThreshold: 5
        timeoutSeconds: 11
"""


@pytest.fixture
def values_file_processor(tmp_path, sample_yaml_content, caplog):
    caplog.set_level("DEBUG")
    values_file = tmp_path / "values.yaml"
    values_file.write_text(sample_yaml_content)
    return ValuesFileProcessor(values_file, "5.1.0", "microservice")


def test_convert_key_list_to_dot_notation():
    assert convert_key_list_to_dot_notation(["a", "b", "c"]) == "a.b.c"
    assert (
        convert_key_list_to_dot_notation(["global", "replicaCount"])
        == "global.replicaCount"
    )
    assert convert_key_list_to_dot_notation(["a", 0, "b", "c"]) == "a[0].b.c"


def test_init(values_file_processor):
    assert values_file_processor.chart_name == "microservice"
    assert values_file_processor.chart_version == "5.1.0"


def test_load_yaml(values_file_processor):
    loaded_data = values_file_processor._load_yaml()
    assert (
        loaded_data["microservice"]["image"]["repository"]
        == "dockerhub.com/apache/dummy-image"
    )
    assert loaded_data["microservice"]["prometheus"]["port"] == 4000


@patch("builtins.open", new_callable=mock_open)
def test_save_yaml(mock_file, values_file_processor):
    values_file_processor._save_yaml()
    mock_file.assert_called_once_with(values_file_processor.values_file, "w")
    mock_file().write.assert_called()


def test_check_min_version(values_file_processor):
    assert values_file_processor.chart_version == "5.1.0"
    assert values_file_processor.check_min_version("5.0.0")


def test_check_min_version_with_lower_version_than_required(values_file_processor):
    values_file_processor.chart_version = "4.11.0"
    assert values_file_processor.chart_name == "microservice"
    assert not values_file_processor.check_min_version("5.0.0")


def test_check_min_version_with_invalid_chart_version(values_file_processor):
    values_file_processor.chart_version = "asd"
    with pytest.raises(version.InvalidVersion):
        values_file_processor.check_min_version("5.0.0")


def test_check_min_version_with_invalid_min_req_version(values_file_processor):
    with pytest.raises(version.InvalidVersion):
        values_file_processor.check_min_version("invalid_version")


## Add key tests
def test_add_key(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "image", "taggy"],
        False,
        "v1.2.0",
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )

    print(f"caplog text: {caplog.text}")
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} added in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_and_overwrite_value(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "image", "tag"],
        True,
        "v2.1.0",
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} overwritten in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_with_list(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "env", 2],
        False,
        {"name": "SERVER_USE_SSL", "value": "true"},
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} added in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_with_list_and_overwrite_value(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "env", 1],
        True,
        {"name": "SERVER_PORT", "value": "8080"},
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} overwritten in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_with_list_and_not_overwrite_value(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "env", 1],
        False,
        {"name": "SERVER_PORT", "value": "8080"},
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) != overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} already exists in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_not_eligible_for_requirements(values_file_processor):
    (
        key,
        overwrite,
        overwrite_value,
        req_min_version,
        values_file_processor.chart_version,
    ) = ["microservice", "image", "tag"], False, "v1.2.0", "5.0.0", "4.11.0"
    assert values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    ) == (
        f"Chart version {version.parse(values_file_processor.chart_version)} not eligible for the requirements, "
        f"minimum required version: {version.parse(req_min_version)} at {values_file_processor.values_file} file."
    )


def test_add_key_invalid_chart_version(values_file_processor):
    (
        key,
        overwrite,
        overwrite_value,
        req_min_version,
        values_file_processor.chart_version,
    ) = ["microservice", "image", "tag"], False, "v1.2.0", "5.0.0", "asd"
    with pytest.raises(version.InvalidVersion):
        values_file_processor.add_key(
            key, overwrite, overwrite_value, req_min_version=req_min_version
        )


def test_add_key_invalid_req_min_version(values_file_processor):
    (
        key,
        overwrite,
        overwrite_value,
        req_min_version,
        values_file_processor.chart_version,
    ) = ["microservice", "image", "tag"], False, "v1.2.0", "asd", "5.0.0"
    with pytest.raises(version.InvalidVersion):
        values_file_processor.add_key(
            key, overwrite, overwrite_value, req_min_version=req_min_version
        )


def test_add_key_key_already_exist(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "image", "tag"],
        False,
        "v1.2.0",
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} already exists in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_key_already_exist_with_overwrite(values_file_processor, caplog):
    key, overwrite, overwrite_value, req_min_version = (
        ["microservice", "image", "tag"],
        True,
        "v1.2.0",
        "5.0.0",
    )
    values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    )
    assert values_file_processor.values_data.get(key) == overwrite_value
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} overwritten in {values_file_processor.values_file}"
        in caplog.text
    )


def test_add_key_key_invalid_input_keys_not_matching_chart_name(values_file_processor):
    key, overwrite, overwrite_value, req_min_version = (
        ["microfervice", "image", "tag"],
        True,
        "v1.3.0",
        "5.0.0",
    )
    assert values_file_processor.add_key(
        key, overwrite, overwrite_value, req_min_version=req_min_version
    ) == (
        f"Chart name {values_file_processor.chart_name} does not match the key {key[0]} at {values_file_processor.values_file} file."
    )


## Remove key tests
def test_remove_key(values_file_processor, caplog):
    key, req_min_version = ["microservice", "image", "tag"], "5.0.0"
    ref_data = values_file_processor.values_data.clone()
    ref_data.pop(key, None)
    values_file_processor.remove_key(key, req_min_version=req_min_version)
    assert (
        f"Removed {convert_key_list_to_dot_notation(key)} section from {values_file_processor.values_file}"
        in caplog.text
    )
    assert values_file_processor.values_data == ref_data


def test_remove_key_not_eligible_for_requirements(values_file_processor):
    key, req_min_version, values_file_processor.chart_version = (
        ["microservice", "image", "tag"],
        "5.0.0",
        "4.11.0",
    )
    assert values_file_processor.remove_key(key, req_min_version=req_min_version) == (
        f"Chart version {version.parse(values_file_processor.chart_version)} not eligible for the requirements, "
        f"minimum required version: {version.parse(req_min_version)} at {values_file_processor.values_file} file."
    )


def test_remove_key_invalid_chart_version(values_file_processor):
    key, req_min_version, values_file_processor.chart_version = (
        ["microservice", "image", "taggy"],
        "5.0.0",
        "asd",
    )
    with pytest.raises(version.InvalidVersion):
        values_file_processor.remove_key(key, req_min_version=req_min_version)


def test_remove_key_invalid_req_min_version(values_file_processor):
    key, req_min_version, values_file_processor.chart_version = (
        ["microservice", "image", "taggy"],
        "asd",
        "5.0.0",
    )
    with pytest.raises(version.InvalidVersion):
        values_file_processor.remove_key(key, req_min_version=req_min_version)


def test_remove_key_key_not_exist(values_file_processor, caplog):
    key, req_min_version = ["microservice", "image", "taggy"], "5.0.0"
    values_file_processor.remove_key(key, req_min_version=req_min_version)
    assert (
        f"No {convert_key_list_to_dot_notation(key)} section found in {values_file_processor.values_file}"
        in caplog.text
    )


def test_remove_key_key_invalid_input_keys_not_matching_chart_name(
    values_file_processor,
):
    req_min_version = "5.0.0"
    assert values_file_processor.remove_key(
        ["microfervice", "image", "tag"], req_min_version=req_min_version
    ) == (
        f"Chart name {values_file_processor.chart_name} does not match the key microfervice at {values_file_processor.values_file} file."
    )


def test_rename_key_both_exists_wit_merging(values_file_processor, caplog):
    old_key, key, merge = (
        ["microservice", "podAnnotations"],
        ["microservice", "annotations"],
        True,
    )
    ref_data = values_file_processor.values_data.clone()
    ref_data.pop(old_key, None)
    ref_data.set(
        key, {"reloader.stakater.com/auto": "true", "sidecar.istio.io/inject": "true"}
    )
    values_file_processor.rename_key(old_key, key, merge, "5.0.0")
    assert (
        f"Merged old values of {convert_key_list_to_dot_notation(old_key)} to {convert_key_list_to_dot_notation(key)} at {values_file_processor.values_file}"
        in caplog.text
    )
    assert (
        f"Removed {convert_key_list_to_dot_notation(old_key)} section from {values_file_processor.values_file}"
        in caplog.text
    )
    assert values_file_processor.values_data == ref_data


def test_rename_key_both_exists_without_merging(values_file_processor, caplog):
    old_key, key, merge = (
        ["microservice", "podAnnotations"],
        ["microservice", "annotations"],
        False,
    )
    ref_data = values_file_processor.values_data.clone()
    ref_data.pop(old_key, None)
    assert ref_data.get(key) == {"reloader.stakater.com/auto": "true"}
    values_file_processor.rename_key(old_key, key, merge, req_min_version="5.0.0")
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} already exists in {values_file_processor.values_file}"
        in caplog.text
    )
    assert (
        f"Removed {convert_key_list_to_dot_notation(old_key)} section from {values_file_processor.values_file}"
        in caplog.text
    )


def test_rename_key_old_key_exists_key_not_exists_merge(values_file_processor, caplog):
    old_key, key, merge = (
        ["microservice", "image", "repository"],
        ["microservice", "image", "repositorry"],
        True,
    )
    ref_data = values_file_processor.values_data.clone()
    ref_data.pop(old_key, None)
    ref_data.set(key, "dockerhub.com/apache/dummy-image")
    values_file_processor.rename_key(old_key, key, merge, req_min_version="5.0.0")
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} added in {values_file_processor.values_file}"
        in caplog.text
    )
    assert (
        f"Removed {convert_key_list_to_dot_notation(old_key)} section from {values_file_processor.values_file}"
        in caplog.text
    )


def test_rename_key_old_key_exists_key_not_exists_not_merge(
    values_file_processor, caplog
):
    old_key, key, merge = (
        ["microservice", "image", "repository"],
        ["microservice", "image", "repositorry"],
        False,
    )
    ref_data = values_file_processor.values_data.clone()
    ref_data.pop(old_key, None)
    ref_data.set(key, {})
    values_file_processor.rename_key(old_key, key, merge, req_min_version="5.0.0")
    assert (
        f"Key: {convert_key_list_to_dot_notation(key)} added in {values_file_processor.values_file}"
        in caplog.text
    )
    assert ref_data.get(key) == values_file_processor.values_data.get(key)
    assert (
        f"Removed {convert_key_list_to_dot_notation(old_key)} section from {values_file_processor.values_file}"
        in caplog.text
    )


def test_rename_key_old_key_not_exists(values_file_processor, caplog):
    old_key, key, merge = (
        ["microservice", "image", "repositorry"],
        ["microservice", "image", "repository"],
        False,
    )
    values_file_processor.rename_key(old_key, key, merge, req_min_version="5.0.0")
    assert (
        f"Cannot rename key {convert_key_list_to_dot_notation(old_key)}, because the old key does not exist"
        in caplog.text
    )


def test_rename_key_not_eligible_for_requirements(values_file_processor):
    (
        key,
        merge,
        req_min_version,
        values_file_processor.chart_version,
    ) = ["microservice", "key"], False, "5.0.0", "4.11.0"
    assert values_file_processor.rename_key(
        key, merge, "new_value", req_min_version=req_min_version
    ) == (
        f"Chart version {version.parse(values_file_processor.chart_version)} not eligible for the requirements, "
        f"minimum required version: {version.parse(req_min_version)} at {values_file_processor.values_file} file."
    )


def test_rename_key_invalid_chart_version(values_file_processor):
    values_file_processor.chart_version, req_min_version = "asd", "5.0.0"
    with pytest.raises(version.InvalidVersion):
        values_file_processor.rename_key(
            ["microservice", "key"], False, "new_value", req_min_version=req_min_version
        )


def test_rename_key_invalid_req_min_version(values_file_processor):
    values_file_processor.chart_version, req_min_version = "5.0.0", "asd"
    with pytest.raises(version.InvalidVersion):
        values_file_processor.rename_key(
            ["microservice", "key"], False, "new_value", req_min_version=req_min_version
        )


def test_rename_key_key_invalid_input_keys_not_matching_chart_name(
    values_file_processor,
):
    old_key, key, merge, req_min_version = (
        ["microservice", "image", "tag"],
        ["microfervice", "image", "tag"],
        True,
        "5.0.0",
    )
    assert (
        values_file_processor.rename_key(
            old_key, key, merge, req_min_version=req_min_version
        )
        == f"Chart name {values_file_processor.chart_name} does not match the key {key[0]} at {values_file_processor.values_file} file."
    )
