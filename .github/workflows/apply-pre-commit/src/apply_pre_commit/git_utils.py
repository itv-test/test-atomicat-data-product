import json
import shutil
import subprocess
from typing import Any, Dict

ALLOWED_LANGUAGES = {"Python", "Scala"}


def run_gh_command(
    *args: str,
    return_json: bool = False,
) -> Any:
    """Run a gh CLI command and parse the JSON response."""
    result = subprocess.run(["gh", *args], capture_output=True, check=True, text=True)
    if return_json:
        return json.loads(result.stdout)


def list_repositories_with_topic(
    org: str,
    topic: str,
    allowed_languages: set = ALLOWED_LANGUAGES,
) -> Dict[str, str]:
    """List all repositories in the specified GitHub organization with the specified topic.
    Allowed languages are those supported by the pre-commit template."""
    response = run_gh_command(
        "api",
        "--paginate",
        f"/search/repositories?q=org:{org}+topic:{topic}",
        return_json=True,
    )

    return {
        repo["name"]: {
            "default_branch": repo["default_branch"],
            "language": repo["language"],
        }
        for repo in response.get("items", [])
        if repo["language"] in allowed_languages
    }


def get_repository_information(
    org: str,
    repo: str,
    allowed_languages: set = ALLOWED_LANGUAGES,
) -> Dict[str, Any]:
    """Get information about a specific repository."""
    response = run_gh_command("api", f"/repos/{org}/{repo}", return_json=True)

    if response["language"] not in allowed_languages:
        raise RuntimeError(
            f"Repository {org}/{repo} has unsupported language {response['language']}."
        )

    return {
        "default_branch": response["default_branch"],
        "language": response["language"],
    }


def get_repositories_to_process(
    github_org: str,
    repositories: str = None,
    repository_topic: str = None,
) -> Dict[str, str]:
    """Get the list of repositories to process based on the provided arguments."""
    if not (repositories or repository_topic):
        raise RuntimeError(
            "At least one of 'repositories' or 'repository-topic' must be provided."
        )

    if repositories:
        repositories = {
            repo_name: get_repository_information(github_org, repo_name)
            for repo_name in repositories.split(",")
        }
    else:
        repositories = list_repositories_with_topic(github_org, repository_topic)

    return repositories


def clone_repository(
    fq_repository_name: str,
    target_path: str,
) -> None:
    """Clone the specified repository to the target path."""
    shutil.rmtree(target_path, ignore_errors=True)
    run_gh_command("repo", "clone", fq_repository_name, target_path)


def run_git_command(
    *args: str,
    path: str = None,
) -> None:
    """Run a git CLI command."""
    subprocess.run(["git", *args], check=True, cwd=path)


def stage_all_changes_and_commit(
    commit_message: str,
    path: str = None,
) -> None:
    run_git_command("add", ".", path=path)
    run_git_command("commit", "--allow-empty", "-m", commit_message, path=path)


def push_and_create_pull_request(
    gh_token: str,
    fq_repository_name: str,
    cloned_repository_path: str,
    target_branch_name: str,
    default_branch: str,
    commit_prefix: str,
) -> None:
    """Push the changes to the remote repository and create a pull request."""
    run_git_command(
        "remote",
        "set-url",
        "origin",
        f"https://x-access-token:{gh_token}@github.com/{fq_repository_name}.git",
        path=cloned_repository_path,
    )
    run_git_command(
        "push", "--set-upstream",
        "origin", target_branch_name,
        "--force",
        path=cloned_repository_path,
    )
    run_gh_command(
        "pr",
        "create",
        "--repo", fq_repository_name,
        "--head", target_branch_name,
        "--base", default_branch,
        "--title", f"{commit_prefix} | Update pre-commit configuration and test workflow",
        "--body", "This PR updates the pre-commit configuration and test workflow and runs the new pre-commit.",
    )
