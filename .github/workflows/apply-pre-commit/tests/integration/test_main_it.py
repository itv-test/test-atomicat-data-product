import os
import subprocess
from textwrap import dedent, indent

import jinja2
from pathlib import Path
from unittest.mock import call, patch

from apply_pre_commit.main import process_repositories

RESOURCES_DIR = Path(__file__).parent / "resources"


def simulate_cloned_repository(
    fq_repository_name: str,
    target_path: str,
    has_machine_learning_and_flex: bool = False,
) -> None:
    workflows_path = f"{target_path}/.github/workflows"
    os.makedirs(workflows_path)
    if has_machine_learning_and_flex:
        os.makedirs(f"{target_path}/machine-learning")
        os.makedirs(f"{target_path}/flex")

    data_product_name = fq_repository_name.split('/')[1]

    # Use Jinja to render an existing, data-product-specific test workflow
    with open(f"{RESOURCES_DIR}/original_test.yml.jinja", "r") as f:
        template_content = f.read()
    template = jinja2.Template(template_content)
    context = {"data_product_name": data_product_name}
    with open(f"{workflows_path}/test.yml", "w") as f:
        f.write(template.render(context))

    # Initialize a git repository
    subprocess.run(["git", "init", "-b", "main"], check=True, cwd=target_path)
    subprocess.run(["git", "add", "."], check=True, cwd=target_path)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=target_path)


def get_expected_test_workflow(
    data_product_name: str,
    language: str,
    has_machine_learning_and_flex: bool,
) -> str:
    workflow_content = dedent(f"""
        jobs:
          infra-checks:
            with:
              data-product-name: {data_product_name}
              domain: some-domain

          some-validation:
            uses: some-workflow.yml
            with:
              data-product-name: {data_product_name}
              domain: some-domain
              run-{"scala" if language == "Scala" else "other"}: false
    """)
    if has_machine_learning_and_flex:
        workflow_content += indent(dedent(f"""
        machine-learning-validation:
          uses: some-ml-validation-workflow.yml
          with:
            data-product-name: {data_product_name}
            domain: some-domain

        flex-validation:
          uses: some-flex-validation-workflow.yml
          with:
            data-product-name: {data_product_name}
            domain: some-domain
        """), "  ")
    workflow_content += indent(dedent("""
        check-completion:
          needs:
            - infra-checks
            - some-validation"""), "  ")
    if has_machine_learning_and_flex:
        workflow_content += indent(dedent("""
        - machine-learning-validation
        - flex-validation
        """), "      ")

    return workflow_content.strip() + "\n"


def get_expected_pre_commit_config(
    language: str,
) -> str:
    pre_commit_config_content = dedent("""
        repos:
          - repo: https://github.com/some_org/some_repo
            rev: 1.0.0
            hooks:
              - id: some-hook
        """).strip()
    if language == "Scala":
        pre_commit_config_content += "\n" + indent(dedent("""
            - repo: https://github.com/some_other_org/some_repo
              rev: v1.0.0
              hooks:
                - id: some-scala-hook
            """).strip(), "  ")
    pre_commit_config_content += "\n" + indent(dedent("""
        - repo: https://github.com/a_third_org/some_repo
          rev: v1.0.0
          hooks:
            - id: some-hook
     """).strip(), "  ")

    return pre_commit_config_content.strip() + "\n"


def test_process_repositories_with_repositories(
    tmp_path: Path,
    mock_environment_variables: None,
) -> None:
    # Given
    root_dir = tmp_path.as_posix()

    github_org = "some-org"
    repositories = "repo-one,repo-two"
    repository_topic = None
    path_to_test_workflow_template = f"{RESOURCES_DIR}/test.yml.jinja"
    path_to_config_template = f"{RESOURCES_DIR}/.pre-commit-config.yaml.jinja"
    target_branch_name = "some-branch"
    commit_prefix = "Some commit prefix"
    push_and_create_pull_requests = True

    # Simulate pre-cloning repositories
    simulate_cloned_repository("some-org/repo-one", f"{root_dir}/repos/some-org/repo-one")
    simulate_cloned_repository("some-org/repo-two", f"{root_dir}/repos/some-org/repo-two", has_machine_learning_and_flex=True)

    mock_run_gh_side_effects = [
        # Mock getting repository info for 'repo-one'
        {
            "default_branch": "main",
            "language": "Python",
        },
        # Mock getting repository info for 'repo-two'
        {
            "default_branch": "main",
            "language": "Scala",
        },
    ]

    # When
    with (
        patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command,
        patch("apply_pre_commit.main.clone_repository") as mock_clone_repository,
        patch("apply_pre_commit.main.run_pre_commit_all_files") as mock_run_pre_commit_all_files,
        patch("apply_pre_commit.main.push_and_create_pull_request") as mock_push_and_create_pull_request,
    ):
        mock_run_gh_command.side_effect = mock_run_gh_side_effects

        process_repositories(
            github_org,
            repositories,
            repository_topic,
            path_to_test_workflow_template,
            path_to_config_template,
            target_branch_name,
            commit_prefix,
            push_and_create_pull_requests,
            root_local_path=root_dir,
        )

        # Then
        # Check the correct calls were made to 'run_gh_command'
        expected_run_gh_calls = [
            call("api", "/repos/some-org/repo-one", return_json=True),
            call("api", "/repos/some-org/repo-two", return_json=True),
        ]
        assert mock_run_gh_command.call_args_list == expected_run_gh_calls

        # Check the correct calls were made to 'clone_repository'
        expected_clone_repository_calls = [
            call("some-org/repo-one", f"{root_dir}/repos/some-org/repo-one"),
            call("some-org/repo-two", f"{root_dir}/repos/some-org/repo-two"),
        ]
        assert mock_clone_repository.call_args_list == expected_clone_repository_calls

        # Check the correct calls were made to 'run_pre_commit_all_files'
        expected_run_pre_commit_all_files_calls = [
            call(f"{root_dir}/repos/some-org/repo-one"),
            call(f"{root_dir}/repos/some-org/repo-two"),
        ]
        assert mock_run_pre_commit_all_files.call_args_list == expected_run_pre_commit_all_files_calls

        # Check the correct calls were made to 'push_and_create_pull_request'
        expected_push_and_create_pull_request_calls = [
            call("some-token", "some-org/repo-one", f"{root_dir}/repos/some-org/repo-one", "some-branch", "main", "Some commit prefix"),
            call("some-token", "some-org/repo-two", f"{root_dir}/repos/some-org/repo-two", "some-branch", "main", "Some commit prefix"),
        ]
        assert mock_push_and_create_pull_request.call_args_list == expected_push_and_create_pull_request_calls

        # Check the test workflow for each repository was updated correctly
        with open(f"{root_dir}/repos/some-org/repo-one/.github/workflows/test.yml", "r") as f:
            actual_workflow_first_repo = f.read()
        with open(f"{root_dir}/repos/some-org/repo-two/.github/workflows/test.yml", "r") as f:
            actual_workflow_second_repo = f.read()
        expected_workflow_first_repo = get_expected_test_workflow("repo-one", "Python", False)
        expected_workflow_second_repo = get_expected_test_workflow("repo-two", "Scala", True)
        assert actual_workflow_first_repo == expected_workflow_first_repo
        assert actual_workflow_second_repo == expected_workflow_second_repo

        # Check the pre-commit configuration for each repository was updated correctly
        with open(f"{root_dir}/repos/some-org/repo-one/.pre-commit-config.yaml", "r") as f:
            actual_pre_commit_config_first_repo = f.read()
        with open(f"{root_dir}/repos/some-org/repo-two/.pre-commit-config.yaml", "r") as f:
            actual_pre_commit_config_second_repo = f.read()
        expected_pre_commit_config_first_repo = get_expected_pre_commit_config("Python")
        expected_pre_commit_config_second_repo = get_expected_pre_commit_config("Scala")
        assert actual_pre_commit_config_first_repo == expected_pre_commit_config_first_repo
        assert actual_pre_commit_config_second_repo == expected_pre_commit_config_second_repo


def test_process_repositories_with_repository_topic(
    tmp_path: Path,
    mock_environment_variables: None,
) -> None:
    # Given
    root_dir = tmp_path.as_posix()

    github_org = "some-org"
    repositories = None
    repository_topic = "some-topic"
    path_to_test_workflow_template = f"{RESOURCES_DIR}/test.yml.jinja"
    path_to_config_template = f"{RESOURCES_DIR}/.pre-commit-config.yaml.jinja"
    target_branch_name = "some-branch"
    commit_prefix = "Some commit prefix"
    push_and_create_pull_requests = True

    # Simulate pre-cloning repositories
    simulate_cloned_repository("some-org/repo-one", f"{root_dir}/repos/some-org/repo-one")
    simulate_cloned_repository("some-org/repo-two", f"{root_dir}/repos/some-org/repo-two", has_machine_learning_and_flex=True)

    mock_run_gh_response = {
        "items": [
            {
                "name": "repo-one",
                "default_branch": "main",
                "language": "Python",
            },
            {
                "name": "repo-two",
                "default_branch": "main",
                "language": "Scala",
            }
        ]
    }

    # When
    with (
        patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command,
        patch("apply_pre_commit.main.clone_repository") as mock_clone_repository,
        patch("apply_pre_commit.main.run_pre_commit_all_files") as mock_run_pre_commit_all_files,
        patch("apply_pre_commit.main.push_and_create_pull_request") as mock_push_and_create_pull_request,
    ):
        mock_run_gh_command.return_value = mock_run_gh_response

        process_repositories(
            github_org,
            repositories,
            repository_topic,
            path_to_test_workflow_template,
            path_to_config_template,
            target_branch_name,
            commit_prefix,
            push_and_create_pull_requests,
            root_local_path=root_dir,
        )

        # Then
        # Check the correct calls were made to 'run_gh_command'
        expected_run_gh_calls = [
            call("api", "--paginate", "/search/repositories?q=org:some-org+topic:some-topic", return_json=True),
        ]
        assert mock_run_gh_command.call_args_list == expected_run_gh_calls

        # Check the correct calls were made to 'clone_repository'
        expected_clone_repository_calls = [
            call("some-org/repo-one", f"{root_dir}/repos/some-org/repo-one"),
            call("some-org/repo-two", f"{root_dir}/repos/some-org/repo-two"),
        ]
        assert mock_clone_repository.call_args_list == expected_clone_repository_calls

        # Check the correct calls were made to 'run_pre_commit_all_files'
        expected_run_pre_commit_all_files_calls = [
            call(f"{root_dir}/repos/some-org/repo-one"),
            call(f"{root_dir}/repos/some-org/repo-two"),
        ]
        assert mock_run_pre_commit_all_files.call_args_list == expected_run_pre_commit_all_files_calls

        # Check the correct calls were made to 'push_and_create_pull_request'
        expected_push_and_create_pull_request_calls = [
            call("some-token", "some-org/repo-one", f"{root_dir}/repos/some-org/repo-one", "some-branch", "main", "Some commit prefix"),
            call("some-token", "some-org/repo-two", f"{root_dir}/repos/some-org/repo-two", "some-branch", "main", "Some commit prefix"),
        ]
        assert mock_push_and_create_pull_request.call_args_list == expected_push_and_create_pull_request_calls

        # Check the test workflow for each repository was updated correctly
        with open(f"{root_dir}/repos/some-org/repo-one/.github/workflows/test.yml", "r") as f:
            actual_workflow_first_repo = f.read()
        with open(f"{root_dir}/repos/some-org/repo-two/.github/workflows/test.yml", "r") as f:
            actual_workflow_second_repo = f.read()
        expected_workflow_first_repo = get_expected_test_workflow("repo-one", "Python", False)
        expected_workflow_second_repo = get_expected_test_workflow("repo-two", "Scala", True)
        assert actual_workflow_first_repo == expected_workflow_first_repo
        assert actual_workflow_second_repo == expected_workflow_second_repo

        # Check the pre-commit configuration for each repository was updated correctly
        with open(f"{root_dir}/repos/some-org/repo-one/.pre-commit-config.yaml", "r") as f:
            actual_pre_commit_config_first_repo = f.read()
        with open(f"{root_dir}/repos/some-org/repo-two/.pre-commit-config.yaml", "r") as f:
            actual_pre_commit_config_second_repo = f.read()
        expected_pre_commit_config_first_repo = get_expected_pre_commit_config("Python")
        expected_pre_commit_config_second_repo = get_expected_pre_commit_config("Scala")
        assert actual_pre_commit_config_first_repo == expected_pre_commit_config_first_repo
        assert actual_pre_commit_config_second_repo == expected_pre_commit_config_second_repo
