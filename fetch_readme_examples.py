import os
import yaml
import requests
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
TEMPLATES = ROOT
TARGET_ROOT = Path(os.environ.get("GHA_REPO_PATH", "")).resolve()
if not TARGET_ROOT.exists():
    sys.exit(f"GHA_REPO_PATH does not exist: {TARGET_ROOT}")
MODULES_FILE = ROOT / "modules.yaml"
OUTPUT_FILE = TARGET_ROOT / "CONTRIBUTING.md"

BEGIN_MARKER = "<!-- BEGIN EXAMPLE -->"
END_MARKER = "<!-- END EXAMPLE -->"

DEFAULT_BRANCH = "main"


def load_modules():
    with open(MODULES_FILE, "r") as f:
        return yaml.safe_load(f)


def fetch_readme(repo, path):
    url = f"https://raw.githubusercontent.com/{repo}/{DEFAULT_BRANCH}/{path}/README.md"

    headers = {}

    # Use token if available (for private repos)
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise FileNotFoundError(
            f"Could not fetch README ({response.status_code}): {url}"
        )

    return response.text


def extract_example_section(content, source_label):
    if BEGIN_MARKER not in content or END_MARKER not in content:
        print(f"⚠ Skipping {source_label} (no markers found)")
        return None

    section = content.split(BEGIN_MARKER)[1].split(END_MARKER)[0]
    return section.strip()


def build_combined_section(modules):
    sections = []

    for module_name, module_data in modules.items():
        if module_data.get("mock"):
            print(f"Skipping {module_name} (mock)")
            continue

        repo = module_data["repo"]
        path = module_data["path"]

        print(f"Fetching {module_name} from {repo}/{path}")

        readme_content = fetch_readme(repo, path)

        section = extract_example_section(
            readme_content,
            f"{repo}/{path}"
        )

        if section:
            sections.append(f"\n{section}")

    return "\n\n---\n\n".join(sections)


def update_output_file(new_content):
    with open(OUTPUT_FILE, "r") as f:
        content = f.read()

    if BEGIN_MARKER not in content or END_MARKER not in content:
        raise ValueError("Markers not found in CONTRIBUTING.md")

    before = content.split(BEGIN_MARKER)[0]
    after = content.split(END_MARKER)[1]

    updated = (
        before
        + BEGIN_MARKER
        + "\n\n"
        + new_content
        + "\n\n"
        + END_MARKER
        + after
    )

    with open(OUTPUT_FILE, "w") as f:
        f.write(updated)

    print("CONTRIBUTING.md updated successfully")


def main():
    modules = load_modules()
    combined_content = build_combined_section(modules)
    update_output_file(combined_content)


if __name__ == "__main__":
    main()
