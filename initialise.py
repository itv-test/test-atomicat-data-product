#!/usr/bin/env python3
import os
from os import linesep, makedirs
from pathlib import Path
from shutil import copy
import shutil
from typing import Tuple
from jinja2 import Environment, FunctionLoader


def onboard(
    platform: str,
    domain: str,
    data_product_name_kebab_case: str,
    data_product_owner: str,
    data_custodian: str,
    technical_owner: str,
    github_dp_team: str,
    repo_path: str,
    language: str = "python",
    has_machine_learning: bool = False,
    has_flex: bool = False,
    set_type_in_infra_checks: bool = False,
):
    global data_product_name_snake_case

    data_product_name_snake_case = data_product_name_kebab_case.replace(
        "-", "_")

    jinja_environment = Environment()
    jinja_environment.globals = {
        "platform": platform,
        "domain": domain,
        "data_product_name_kebab_case": data_product_name_kebab_case,
        "data_product_name_snake_case": data_product_name_snake_case,
        "data_product_owner": data_product_owner,
        "data_custodian": data_custodian,
        "technical_owner": technical_owner,
        "github_dp_team": github_dp_team,
        "language": language,
        "has_machine_learning": has_machine_learning,
        "has_flex": has_flex,
        "set_type_in_infra_checks": set_type_in_infra_checks,
    }

    jinja_environment.loader = FunctionLoader(read_file)
    remove_dir_contents(Path(repo_path) / ".github" / "workflows")
    copy_template(repo_path)
    render_templates(jinja_environment, repo_path)
    if platform == "bartex":
        base = Path(repo_path)
        envs_base = base / "infrastructure" / "environments"
        remove_dir_contents(envs_base / "prd")
        remove_dir_contents(envs_base / "pre")
        dev_env = envs_base / "dev"
        tst_env = envs_base / "tst"

        if dev_env.exists() and not tst_env.exists():
            dev_env.rename(tst_env)
            print(f"Renamed: {dev_env} -> {tst_env}")
        elif tst_env.exists():
            print("tst environment already exists, skipping rename")
        else:
            raise RuntimeError("Expected dev environment does not exist")

    return jinja_environment


def copy_template(repo_path: str):
    path = os.getcwd()
    shutil.copytree(f"{path}/template", repo_path, dirs_exist_ok=True)


def read_file(template) -> Tuple:
    with open(template) as f:
        return (f.read(), f.name, lambda: True)


def render_templates(environment: Environment, template_path: str):
    template_files = [
        t for t in Path(template_path).glob("**/*") if t.is_file() and ".git/" not in t.as_posix()
    ]
    for f in template_files:
        new_filename = get_new_filename(f, **environment.globals)

        # Only render files / paths that are templated
        if f != new_filename:
            makedirs(name=new_filename.parent, exist_ok=True)

            if ".jinja" in f.suffix:
                with open(new_filename.as_posix(), "w") as rendered_file:
                    rendered_file.write(
                        environment.get_template(
                            f.as_posix()).render() + linesep
                    )
            else:
                copy(f, new_filename)

            # Remove template files
            f.unlink()


def get_new_filename(
        file: Path,
        **kwargs,
):
    data_product_name_kebab_case = kwargs['data_product_name_kebab_case']
    domain = kwargs['domain']

    new_file_name = (
        file.as_posix()
        .replace("change_me_data_component", data_product_name_snake_case)
        .replace("change-me-data-component", data_product_name_kebab_case)
        .replace("change_me_domain", domain)
        .removesuffix(".jinja")
    )
    return Path(new_file_name)


def remove_dir_contents(path: Path):
    if not path.exists():
        print(f"Directory does not exist, skipping: {path}")
        return

    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    print(f"Cleared: {path}")


if __name__ == "__main__":
    platform = os.environ["GHA_PLATFORM"]
    domain = os.environ["GHA_DOMAIN"]
    data_product_name_kebab_case = os.environ["GHA_PRODUCT_NAME"].lower()
    data_product_owner = os.environ["GHA_DATA_PRODUCT_OWNER"]
    data_custodian = os.environ["GHA_DATA_CUSTODIAN"]
    technical_owner = os.environ["GHA_TECHNICAL_OWNER"]
    github_dp_team = os.environ["GHA_GH_TEAM"]
    repo_path = os.environ["GHA_REPO_PATH"]

    onboard(
        platform,
        domain,
        data_product_name_kebab_case,
        data_product_owner,
        data_custodian,
        technical_owner,
        github_dp_team,
        repo_path,
    )
