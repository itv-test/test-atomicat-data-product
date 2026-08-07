import argparse
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

import yaml

from apply_pre_commit.git_utils import (
    get_repositories_to_process,
    clone_repository,
    push_and_create_pull_request,
    run_git_command,
    stage_all_changes_and_commit,
)
from apply_pre_commit.template_utils import (
    get_and_render_pre_commit_config,
    get_and_render_test_workflow,
)


def configure_logger() -> None:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def main(args=None) -> None:
    configure_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--github-org",
        type=str,
        required=True,
        help="GitHub organization to filter repositories by.",
    )
    parser.add_argument(
        "--repositories",
        type=str,
        required=False,
        help=(
            "Comma-separated list of repositories to process. If not provided, all "
            "repositories with the specified topic will be processed."
        ),
    )
    parser.add_argument(
        "--repository-topic",
        type=str,
        required=False,
        help="Topic to filter repositories by.",
    )
    parser.add_argument(
        "--path-to-config-template",
        type=str,
        required=False,
        default="template/.pre-commit-config.yaml.jinja",
        help="Path to the pre-commit config template, relative to the repository root.",
    )
    parser.add_argument(
        "--path-to-test-workflow-template",
        type=str,
        required=False,
        default="template/.github/workflows/test.yml.jinja",
        help="Path to the test workflow template, relative to the repository root.",
    )
    parser.add_argument(
        "--target-branch-name",
        type=str,
        required=False,
        default="cde-000-update-pre-commit-config",
        help="Name of the branch to create for the changes.",
    )
    parser.add_argument(
        "--commit-and-pr-prefix",
        type=str,
        required=False,
        default="CDE-000 | XX",
        help="Prefix for the commit messages and PR title.",
    )
    parser.add_argument(
        "--skip-authenticate-per-repo",
        required=False,
        help=(
            "Whether to skip authentication with each repository using a GitHub token. "
            "Set false for local testing."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--push-and-create-pull-requests",
        required=False,
        help="Whether to push changes and create pull requests for them.",
        action="store_true",
    )
    parser.add_argument(
        "--root-local-path",
        type=str,
        required=False,
        default="/tmp",
        help="Root local path for repository operations.",
    )
    args = parser.parse_args(args=args)

    path_to_test_workflow_template = Path(__file__).parents[5] / args.path_to_test_workflow_template
    path_to_config_template = Path(__file__).parents[5] / args.path_to_config_template

    process_repositories(
        args.github_org,
        args.repositories,
        args.repository_topic,
        path_to_test_workflow_template,
        path_to_config_template,
        args.target_branch_name,
        args.commit_and_pr_prefix,
        args.push_and_create_pull_requests,
        args.root_local_path,
    )


def run_pre_commit_all_files(
    path: str = None,
) -> None:
    """Run a pre-commit on all files."""
    subprocess.run(["pre-commit", "run", "--all-files"], check=True, cwd=path)


def process_repositories(
    github_org: str,
    repositories: Dict[str, Any],
    repository_topic: str,
    path_to_test_workflow_template: str,
    path_to_config_template: str,
    target_branch_name: str,
    commit_prefix: str,
    push_and_create_pull_requests: bool,
    root_local_path: str,
    gh_token: str = None,
) -> None:
    """Process the specified repositories to update and run their pre-commit configuration and test workflow."""
    if gh_token is None:
        gh_token = os.environ["GH_TOKEN"]

    logging.info("Parsing list of repositories and getting repository information...")
    repositories = get_repositories_to_process(
        github_org,
        repositories,
        repository_topic,
    )
    logging.info(f"Found {len(repositories)} repositories to process: {', '.join(repositories.keys())}.")

    logging.info("Starting processing of repositories...")
    failed_repositories = []

    for repository_name, repository_information in repositories.items():
        logging.info(f"Processing repository {repository_name}...")
        try:
            process_repository(
                github_org,
                repository_name,
                repository_information,
                path_to_test_workflow_template,
                path_to_config_template,
                target_branch_name,
                commit_prefix,
                push_and_create_pull_requests,
                root_local_path,
                gh_token,
            )

        except Exception as e:
            logging.error(f"Failed to process repository {repository_name}: {e}.")
            failed_repositories.append(repository_name)
            continue

        logging.info(f"Successfully processed repository {repository_name}.")

    if failed_repositories:
        logging.error(
            f"Failed to process the following repositories: {', '.join(failed_repositories)}. "
            "Review the logs for more details."
        )
        raise RuntimeError("One or more repositories failed to process.")
    else:
        logging.info("Successfully processed all repositories.")


def process_repository(
    github_org: str,
    repository_name: str,
    repository_information: Dict[str, Any],
    path_to_test_workflow_template: str,
    path_to_config_template: str,
    target_branch_name: str,
    commit_prefix: str,
    push_and_create_pull_requests: bool,
    root_local_path: str,
    gh_token: str,
) -> None:
    """Process a single repository to update and run its pre-commit configuration and test workflow."""
    fq_repository_name = f"{github_org}/{repository_name}"
    default_branch = repository_information["default_branch"]
    language = repository_information["language"].lower()
    cloned_repository_path = f"{root_local_path}/repos/{github_org}/{repository_name}"
    test_workflow_path = f"{cloned_repository_path}/.github/workflows/test.yml"

    logging.info(f"Cloning repository {fq_repository_name} to {cloned_repository_path}...")
    clone_repository(fq_repository_name, cloned_repository_path)
    has_machine_learning = shutil.os.path.exists(f"{cloned_repository_path}/machine-learning")
    has_flex = shutil.os.path.exists(f"{cloned_repository_path}/flex")

    # Assume every repo has a test workflow we can extract some attributes from
    logging.info(f"Extracting attributes from test workflow in repository {fq_repository_name}...")
    with open(test_workflow_path, "r") as f:
        test_workflow = yaml.safe_load(f)
    data_product_name = test_workflow["jobs"]["infra-checks"]["with"]["data-product-name"]
    domain = test_workflow["jobs"]["infra-checks"]["with"]["domain"]
    set_type_in_infra_checks = "type" in test_workflow["jobs"]["infra-checks"]["with"]

    logging.info(f"Creating branch {target_branch_name} in repository {fq_repository_name}...")
    run_git_command(
        "checkout", "-b", target_branch_name, default_branch,
        path=cloned_repository_path,
    )

    logging.info(f"Updating test workflow in repository {fq_repository_name}...")
    test_workflow = get_and_render_test_workflow(
        path_to_test_workflow_template,
        data_product_name,
        domain,
        language,
        has_machine_learning,
        has_flex,
        set_type_in_infra_checks,
    )
    with open(
        f"{root_local_path}/repos/{github_org}/{repository_name}/.github/workflows/test.yml", "w"
    ) as f:
        f.write(test_workflow)
    stage_all_changes_and_commit(f"{commit_prefix} | Update test workflow", path=cloned_repository_path)

    logging.info(f"Updating pre-commit configuration in repository {fq_repository_name}...")
    pre_commit_config = get_and_render_pre_commit_config(path_to_config_template, language)
    with open(f"{root_local_path}/repos/{github_org}/{repository_name}/.pre-commit-config.yaml", "w") as f:
        f.write(pre_commit_config)
    stage_all_changes_and_commit(
        f"{commit_prefix} | Update pre-commit configuration", path=cloned_repository_path
    )

    # Run the pre-commit, don't worry about failures here, output is captured in the logs
    logging.info(f"Running pre-commit in repository {fq_repository_name}...")
    try:
        run_pre_commit_all_files(cloned_repository_path)
    except Exception:
        pass
    stage_all_changes_and_commit(f"{commit_prefix} | Run pre-commit", path=cloned_repository_path)

    if push_and_create_pull_requests:
        logging.info(f"Pushing changes and creating PR in repository {fq_repository_name}...")
        push_and_create_pull_request(
            gh_token,
            fq_repository_name,
            cloned_repository_path,
            target_branch_name,
            default_branch,
            commit_prefix,
        )


if __name__ == "__main__":
    main()
