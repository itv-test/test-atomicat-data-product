from pathlib import Path
from unittest.mock import mock_open, patch

from apply_pre_commit.template_utils import (
    get_and_render_pre_commit_config,
    get_and_render_test_workflow,
    render_jinja_template,
)


def test_render_jinja_template() -> None:
    # Given
    template_file_content = "Hello, {{ name }}!"
    context = {"name": "World"}

    # When
    with patch("apply_pre_commit.template_utils.open", mock_open(read_data=template_file_content)):
        actual_rendered_template = render_jinja_template(
            template_path="some/template/path",
            context=context,
        )

        # Then
        expected_rendered_template = "Hello, World!\n"
        assert actual_rendered_template == expected_rendered_template


def test_get_and_render_pre_commit_config_with_python() -> None:
    # Given
    path_to_template = Path(__file__).parent / "resources" / ".pre-commit-config.yaml.jinja"
    language = "python"

    # When
    actual_rendered_template = get_and_render_pre_commit_config(
        path_to_template=path_to_template,
        language=language,
    )

    # Then
    expected_rendered_template = (
        "some-key:\n"
        "  python-key\n"
    )
    assert actual_rendered_template == expected_rendered_template


def test_get_and_render_pre_commit_config_with_scala() -> None:
    # Given
    path_to_template = Path(__file__).parent / "resources" / ".pre-commit-config.yaml.jinja"
    language = "scala"

    # When
    actual_rendered_template = get_and_render_pre_commit_config(
        path_to_template=path_to_template,
        language=language,
    )

    # Then
    expected_rendered_template = (
        "some-key:\n"
        "  python-key\n"
        "  scala-only-key\n"
    )
    assert actual_rendered_template == expected_rendered_template


def test_get_and_render_test_workflow() -> None:
    # Given
    path_to_template = Path(__file__).parent / "resources" / "test.yml.jinja"
    data_product_name_kebab_case = "some-data-product"
    domain = "some-domain"
    language = "python"

    # When
    actual_rendered_template = get_and_render_test_workflow(
        path_to_template=path_to_template,
        data_product_name_kebab_case=data_product_name_kebab_case,
        domain=domain,
        language=language,
    )

    # Then
    expected_rendered_template = (
        "some-key:\n"
        "  data-product: some-data-product\n"
        "  domain: some-domain\n"
        "  python-key: some-value\n"
    )
    assert actual_rendered_template == expected_rendered_template


def test_get_and_render_test_workflow_with_optional_args() -> None:
    # Given
    path_to_template = Path(__file__).parent / "resources" / "test.yml.jinja"
    data_product_name_kebab_case = "some-data-product"
    domain = "some-domain"
    language = "scala"

    # When
    actual_rendered_template = get_and_render_test_workflow(
        path_to_template=path_to_template,
        data_product_name_kebab_case=data_product_name_kebab_case,
        domain=domain,
        language=language,
        has_machine_learning=True,
        has_flex=True,
        set_type_in_infra_checks=True,
    )

    # Then
    expected_rendered_template = (
        "some-key:\n"
        "  data-product: some-data-product\n"
        "  domain: some-domain\n"
        "  python-key: some-value\n"
        "  scala-only-key: some-value\n"
        "  machine-learning:\n"
        "    some-config: some-value\n"
        "  flex:\n"
        "    some-config: some-value\n"
        "  set-type-in-infra-checks: true\n"
    )
    assert actual_rendered_template == expected_rendered_template
