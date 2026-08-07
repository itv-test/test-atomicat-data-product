import pytest


@pytest.fixture
def mock_environment_variables(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GH_TOKEN", "some-token")
