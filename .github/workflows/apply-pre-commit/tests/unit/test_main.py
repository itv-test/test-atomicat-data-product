from unittest.mock import patch

from apply_pre_commit.main import run_pre_commit_all_files


def test_run_pre_commit_all_files(
    mock_environment_variables: None,
) -> None:
    # Given
    path = "some/path"

    # When
    with patch("apply_pre_commit.main.subprocess.run") as mock_subprocess_run:
        run_pre_commit_all_files(path)
        mock_subprocess_run.assert_called_once_with(
            ["pre-commit", "run", "--all-files"],
            check=True,
            cwd=path,
        )
