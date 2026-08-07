import pytest

from unittest.mock import call, patch

from apply_pre_commit.git_utils import (
    clone_repository,
    get_repositories_to_process,
    get_repository_information,
    list_repositories_with_topic,
    push_and_create_pull_request,
    run_gh_command,
    run_git_command,
    stage_all_changes_and_commit,
)


def test_run_gh_command() -> None:
    # Given
    command = ["some", "command"]

    # When
    with patch("apply_pre_commit.git_utils.subprocess.run") as mock_subprocess_run:
        result = run_gh_command(*command)
        mock_subprocess_run.assert_called_once_with(
            ["gh", "some", "command"],
            capture_output=True,
            text=True,
            check=True
        )

    # Then
    assert result is None


def test_run_gh_command_with_return() -> None:
    # Given
    command = ["some", "command"]

    # When
    with patch("apply_pre_commit.git_utils.subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.return_value.stdout = '{"some-key": "some-value"}'
        result = run_gh_command(*command, return_json=True)
        mock_subprocess_run.assert_called_once_with(
            ["gh", "some", "command"],
            capture_output=True,
            text=True,
            check=True
        )

    # Then
    assert result == {"some-key": "some-value"}


def test_list_repositories_with_topic() -> None:
    # Given
    github_org = "some-org"
    topic = "some-topic"
    mock_response = {
        "items": [
            {
                "name": "some-repo",
                "default_branch": "main",
                "language": "Python",
            },
            {
                "name": "other-repo-with-disallowed-language",
                "default_branch": "main",
                "language": "Rust",
            }
        ]
    }

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.return_value = mock_response
        actual_result = list_repositories_with_topic(github_org, topic)

        # Then
        expected_result = {
            "some-repo": {
                "default_branch": "main",
                "language": "Python",
            },
        }
        mock_run_gh_command.assert_called_once_with(
            "api",
            "--paginate",
            "/search/repositories?q=org:some-org+topic:some-topic",
            return_json=True,
        )
        assert actual_result == expected_result


def test_get_repository_information() -> None:
    # Given
    github_org = "some-org"
    repository = "some-repo"
    mock_response = {
        "default_branch": "main",
        "language": "Scala",
    }

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.return_value = mock_response
        actual_result = get_repository_information(github_org, repository)

        # Then
        expected_result = {
            "default_branch": "main",
            "language": "Scala",
        }
        mock_run_gh_command.assert_called_once_with(
            "api",
            "/repos/some-org/some-repo",
            return_json=True,
        )
        assert actual_result == expected_result


def test_get_repository_information_with_disallowed_language() -> None:
    # Given
    github_org = "some-org"
    repository = "some-repo"
    mock_response = {
        "default_branch": "main",
        "language": "Rust",
    }

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.return_value = mock_response
        with pytest.raises(
            RuntimeError, match="Repository some-org/some-repo has unsupported language Rust."
        ):
            get_repository_information(github_org, repository)

        # Then
        mock_run_gh_command.assert_called_once_with(
            "api",
            "/repos/some-org/some-repo",
            return_json=True,
        )


def test_get_repositories_to_process_with_repositories() -> None:
    # Given
    gitub_org = "some-org"
    repositories = "some-repo,another-repo"
    mock_responses = [
        {
            "default_branch": "main",
            "language": "Python",
        },
        {
            "default_branch": "master",
            "language": "Scala",
        },
    ]

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.side_effect = mock_responses
        actual_result = get_repositories_to_process(gitub_org, repositories=repositories)

        # Then
        gh_expected_calls = [
            call(
                "api",
                "/repos/some-org/some-repo",
                return_json=True,
            ),
            call(
                "api",
                "/repos/some-org/another-repo",
                return_json=True,
            ),
        ]
        assert mock_run_gh_command.call_args_list == gh_expected_calls

        expected_result = {
            "some-repo": {
                "default_branch": "main",
                "language": "Python",
            },
            "another-repo": {
                "default_branch": "master",
                "language": "Scala",
            },
        }
        assert actual_result == expected_result


def test_get_repositories_to_process_with_repository_topic() -> None:
    # Given
    github_org = "some-org"
    repository_topic = "some-topic"
    mock_response = {
        "items": [
            {
                "name": "some-repo",
                "default_branch": "main",
                "language": "Python",
            },
            {
                "name": "other-repo-with-disallowed-language",
                "default_branch": "main",
                "language": "Rust",
            }
        ]
    }

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.return_value = mock_response
        actual_result = get_repositories_to_process(github_org, repository_topic=repository_topic)

        # Then
        mock_run_gh_command.assert_called_once_with(
            "api",
            "--paginate",
            "/search/repositories?q=org:some-org+topic:some-topic",
            return_json=True,
        )

        expected_result = {
            "some-repo": {
                "default_branch": "main",
                "language": "Python",
            },
        }
        assert actual_result == expected_result


def test_get_repositories_to_process_with_invalid_arguments() -> None:
    # Given
    github_org = "some-org"

    # When
    with pytest.raises(
        RuntimeError,
        match="At least one of 'repositories' or 'repository-topic' must be provided."
    ):
        get_repositories_to_process(github_org)


def test_get_repositories_to_process_with_repositories_and_repository_topic() -> None:
    # Here, 'repositories' argument takes precedence over 'repository_topic' argument
    # Given
    github_org = "some-org"
    repositories = "some-repo,another-repo"
    repository_topic = "some-topic"
    mock_responses = [
        {
            "default_branch": "main",
            "language": "Python",
        },
        {
            "default_branch": "master",
            "language": "Scala",
        },
    ]

    # When
    with patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command:
        mock_run_gh_command.side_effect = mock_responses
        actual_result = get_repositories_to_process(
            github_org,
            repositories=repositories,
            repository_topic=repository_topic,
        )

        # Then
        gh_expected_calls = [
            call(
                "api",
                "/repos/some-org/some-repo",
                return_json=True,
            ),
            call(
                "api",
                "/repos/some-org/another-repo",
                return_json=True,
            ),
        ]
        assert mock_run_gh_command.call_args_list == gh_expected_calls

        expected_result = {
            "some-repo": {
                "default_branch": "main",
                "language": "Python",
            },
            "another-repo": {
                "default_branch": "master",
                "language": "Scala",
            },
        }
        assert actual_result == expected_result


def test_clone_repository():
    # Given
    fq_repository_name = "some-org/some-repo"
    target_path = "/some/path"

    # When
    with (
        patch("apply_pre_commit.git_utils.shutil.rmtree") as mock_rmtree,
        patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command,
    ):
        clone_repository(fq_repository_name, target_path)

        # Then
        mock_rmtree.assert_called_once_with(target_path, ignore_errors=True)
        mock_run_gh_command.assert_called_once_with(
            "repo", "clone", fq_repository_name, target_path
        )


def test_run_git_command() -> None:
    # Given
    command = ["some", "command"]

    # When
    with patch("apply_pre_commit.git_utils.subprocess.run") as mock_run:
        run_git_command(*command)

        # Then
        mock_run.assert_called_once_with(
            ["git", "some", "command"],
            check=True,
            cwd=None,
        )


def test_run_git_command_with_path() -> None:
    # Given
    command = ["some", "command"]
    path = "/some/path"

    # When
    with patch("apply_pre_commit.git_utils.subprocess.run") as mock_run:
        run_git_command(*command, path=path)

        # Then
        mock_run.assert_called_once_with(
            ["git", "some", "command"],
            check=True,
            cwd="/some/path",
        )


def test_stage_all_changes_and_commit() -> None:
    # Given
    commit_message = "Some commit message"

    # When
    with patch("apply_pre_commit.git_utils.run_git_command") as mock_run_git_command:
        stage_all_changes_and_commit(commit_message)

        # Then
        expected_calls = [
            call("add", ".", path=None),
            call("commit", "--allow-empty", "-m", "Some commit message", path=None),
        ]
        mock_run_git_command.assert_has_calls(expected_calls)


def test_stage_all_changes_and_commit_with_path() -> None:
    # Given
    commit_message = "Some commit message"
    path = "/some/path"

    # When
    with patch("apply_pre_commit.git_utils.run_git_command") as mock_run_git_command:
        stage_all_changes_and_commit(commit_message, path=path)

        # Then
        expected_calls = [
            call("add", ".", path="/some/path"),
            call("commit", "--allow-empty", "-m", "Some commit message", path="/some/path"),
        ]
        mock_run_git_command.assert_has_calls(expected_calls)


def test_push_and_create_pull_request():
    # Given
    gh_token = "some-gh-token"
    fq_repository_name = "some-org/some-repo"
    cloned_repository_path = "/some/path"
    target_branch_name = "some-target-branch"
    default_branch = "some-default-branch"
    commit_prefix = "Some commit prefix"

    # When
    with (
        patch("apply_pre_commit.git_utils.run_git_command") as mock_run_git_command,
        patch("apply_pre_commit.git_utils.run_gh_command") as mock_run_gh_command,
    ):
        push_and_create_pull_request(
            gh_token,
            fq_repository_name,
            cloned_repository_path,
            target_branch_name,
            default_branch,
            commit_prefix,
        )

        # Then
        expected_git_calls = [
            call(
                "remote",
                "set-url",
                "origin",
                "https://x-access-token:some-gh-token@github.com/some-org/some-repo.git",
                path="/some/path",
            ),
            call(
                "push",
                "--set-upstream", "origin",
                "some-target-branch", "--force",
                path="/some/path",
            ),
        ]
        assert mock_run_git_command.call_args_list == expected_git_calls

        mock_run_gh_command.assert_called_once_with(
            "pr",
            "create",
            "--repo", "some-org/some-repo",
            "--head", "some-target-branch",
            "--base", "some-default-branch",
            "--title", "Some commit prefix | Update pre-commit configuration and test workflow",
            "--body", "This PR updates the pre-commit configuration and test workflow and runs the new pre-commit.",
        )
