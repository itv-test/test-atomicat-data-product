#!/usr/bin/env python3
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from subprocess import run
import json
import sys
import os


def latest_release(repo: str) -> str:
    cmd = [
        "gh",
        "api",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        f"/repos/{repo}/releases/latest",
    ]
    result = run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to fetch latest release:", result.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    tag_name = data.get("tag_name", "")
    return tag_name


ROOT = Path(__file__).parent.resolve()       # Script repo root
TEMPLATES = ROOT                              # templates are in repo root

TARGET_ROOT = Path(os.environ.get("GHA_REPO_PATH", "")).resolve()
if not TARGET_ROOT.exists():
    sys.exit(f"GHA_REPO_PATH does not exist: {TARGET_ROOT}")

MODULES_FILE = ROOT / "modules.yaml"

with open(MODULES_FILE) as f:
    modules_cfg = yaml.safe_load(f)
domain = os.environ.get("GHA_DOMAIN", "cortex")
modules = {}

for name, cfg in modules_cfg.items():
    if cfg.get("mock"):
        modules[name] = {"source": "mock"}
        continue

    # Use pinned version if present, else fetch latest release
    tag = cfg.get("pinned") or latest_release(cfg["repo"])
    if not tag.startswith("v"):
        tag = f"v{tag}"

    major = int(tag.lstrip("v").split(".")[0])
    if major > cfg.get("max_major", 999):
        sys.exit(f"{name}: major version cap exceeded ({tag})")

    path = cfg.get("path", "").strip("/")
    base = f"github.com/{cfg['repo']}//{path}" if path else f"github.com/{cfg['repo']}//"

    modules[name] = {
        "source": f"{base}?ref={tag}"
    }

env = Environment(
    loader=FileSystemLoader(TEMPLATES),
    trim_blocks=True,
    lstrip_blocks=True,
)

RENDERS = {
    "main.core.tf.j2": "infrastructure/terraform/core/main.tf",
    "main.data_access.tf.j2": "infrastructure/terraform/data_access/main.tf",
}

for template_name, output_path in RENDERS.items():
    template_path = TEMPLATES / template_name
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        continue

    print(f"Rendering template: {template_name}")
    template = env.get_template(template_name)
    rendered = template.render(
        modules=modules,
        domain=domain)

    out = TARGET_ROOT / output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered)
    print(f"✔ Rendered {out.resolve()}")
