#!/usr/bin/env python3
import os
from subprocess import run, CalledProcessError

component_name_kebab_case = os.environ["GH_REPO_NAME"].lower()
platform = os.environ["GHA_PLATFORM"]
domain = os.environ["GHA_DOMAIN"]
github_dp_team = os.environ["GHA_GH_TEAM"]


def apply():
    configure_topics()
    add_oidc_claim()
    add_safe_settings()
    try:
        add_repo_collaborators()
    except CalledProcessError:
        print(
            "Unable to add collaborators.",
            "This is likely because the repo permissions are being managed by Safe Settings.",
        )
    add_environments()


def configure_topics():
    run(
        f"""gh repo edit itv-test/{component_name_kebab_case}
   --add-topic '{platform}'
   --add-topic 'data-{domain}'""".replace(
            "\n", ""
        ),
        shell=True,
        check=True,
    )


def add_repo_collaborators():
    admin_team = "ctc-data-admins" if domain == "commercial" else "central-data-admins"
    run(
        f"""
            echo '{{"permission": "admin"}}' | \
                gh api --silent -X PUT "orgs/itv-test/teams/{admin_team}/repos/itv-test/{component_name_kebab_case}" --input - &&\
            echo '{{"permission": "push"}}' | \
                gh api --silent -X PUT "orgs/itv-test/teams/central-data-platform/repos/itv-test/{component_name_kebab_case}" --input - &&\
            echo '{{"permission": "push"}}' | \
                gh api --silent -X PUT "orgs/itv-test/teams/cde/repos/itv-test/{component_name_kebab_case}" --input - &&\
            echo '{{"permission": "maintain"}}' | \
                gh api --silent -X PUT "orgs/itv-test/teams/{github_dp_team}/repos/itv-test/{component_name_kebab_case}" --input -
        """,
        shell=True,
        check=True,
    )


def add_oidc_claim():
    run(
        f"""
            echo '{{"include_claim_keys":["repo"],"use_default":false}}' | \
                gh api --silent -X PUT repos/itv-test/{component_name_kebab_case}/actions/oidc/customization/sub --input -
        """,
        shell=True,
        check=True,
    )


def add_safe_settings():
    suborg = "data-product-commercial-default" if domain == "commercial" else "data-product-central-default"
    run(
        f"""
            echo '{{"properties":[{{"property_name":"safe-settings-suborg","value":"{suborg}"}}]}}' | \
                gh api --silent -X PATCH repos/itv-test/{component_name_kebab_case}/properties/values --input -
        """,
        shell=True,
        check=True,
    )


def add_environments():
    if domain == "commercial":
        team_id = 12135412 # cde change me
    else:
        team_id = 12846227 # Data Mesh - Commercial change me

    for env in ["dev", "dev-access"]:
        run(
            f"""
                gh api --silent -X PUT repos/itv-test/{component_name_kebab_case}/environments/{env}
            """,
            shell=True,
            check=True,
        )
    for env in ["prd-access", "pre-access"]:
        run(
            f"""
                echo '{{"reviewers":[{{"type":"Team","id":{team_id}}}],"deployment_branch_policy":{{"protected_branches":false,"custom_branch_policies":true}}}}' | \
                    gh api --silent -X PUT repos/itv-test/{component_name_kebab_case}/environments/{env} --input -
                echo '{{"name":"main","type":"branch"}}' | \
                    gh api --silent -X POST repos/itv-test/{component_name_kebab_case}/environments/{env}/deployment-branch-policies --input -
            """,
            shell=True,
            check=True,
        )
    for env in ["prd", "pre"]:
        run(
            f"""
                echo '{{"reviewers":[{{"type":"Team","id":{team_id}}}],"deployment_branch_policy":{{"protected_branches":false,"custom_branch_policies":true}}}}' | \
                    gh api --silent -X PUT repos/itv-test/{component_name_kebab_case}/environments/{env} --input -
                echo '{{"name":"v*.*.*","type":"tag"}}' | \
                    gh api --silent -X POST repos/itv-test/{component_name_kebab_case}/environments/{env}/deployment-branch-policies --input -
            """,
            shell=True,
            check=True,
        )

if __name__ == "__main__":
    apply()
