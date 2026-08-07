from typing import Any, Dict

import jinja2


def render_jinja_template(
    template_path: str,
    context: Dict[str, Any] = {},
) -> str:
    """Render a Jinja template with the provided context."""
    with open(template_path, "r") as f:
        template_content = f.read()
    template = jinja2.Template(template_content)
    return template.render(context) + "\n"


def get_and_render_pre_commit_config(
    path_to_template: str,
    language: str
) -> str:
    """Get the pre-commit configuration for the specified language."""
    context = {
        "language": language,
    }
    return render_jinja_template(path_to_template, context)


def get_and_render_test_workflow(
    path_to_template: str,
    data_product_name_kebab_case: str,
    domain: str,
    language: str,
    has_machine_learning: bool = False,
    has_flex: bool = False,
    set_type_in_infra_checks: bool = False,
) -> str:
    """Get the pre-commit configuration for the specified configuration."""
    jinja_variables = {
        "data_product_name_kebab_case": data_product_name_kebab_case,
        "domain": domain,
        "language": language,
        "has_machine_learning": has_machine_learning,
        "has_flex": has_flex,
        "set_type_in_infra_checks": set_type_in_infra_checks,
    }
    return render_jinja_template(path_to_template, jinja_variables)
