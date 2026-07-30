from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGE_SCRIPT_COMMAND = "uv run python scripts/stage_web_python.py"
CORE_VERSION = "0.1.1"
CORE_RELEASE_URL = "https://github.com/reblocke/wald-inference-core/releases/tag/v0.1.1"
CORE_WHEEL_URL = (
    "https://github.com/reblocke/wald-inference-core/releases/download/v0.1.1/"
    "wald_inference-0.1.1-py3-none-any.whl"
)
CORE_WHEEL_SHA256 = "95bc10d770836544d726362c401032e0640a5a9ec1573f043add7f6bd3a65457"


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_makefile_owns_the_single_stage_entrypoint_and_serve_stages_first() -> None:
    makefile = _read("Makefile")

    assert re.search(
        rf"(?m)^stage-web:\n\t{re.escape(STAGE_SCRIPT_COMMAND)}$",
        makefile,
    )
    for target in ("test", "e2e", "serve"):
        assert re.search(rf"(?m)^{target}:.*\bstage-web\b", makefile)
    assert re.search(r"(?m)^verify:.*\btest\b.*\be2e\b", makefile)
    assert "web/assets/py" in makefile


def test_ci_pages_and_release_call_make_stage_web_only() -> None:
    workflow_paths = (
        ".github/workflows/ci.yml",
        ".github/workflows/pages.yml",
        ".github/workflows/release.yml",
    )
    workflows = {path: _read(path) for path in workflow_paths}

    for path, workflow in workflows.items():
        assert "run: make stage-web" in workflow, path
        assert STAGE_SCRIPT_COMMAND not in workflow, path

    assert "path: ./web" in workflows[".github/workflows/pages.yml"]
    assert (
        "git status --porcelain --untracked-files=all" in workflows[".github/workflows/pages.yml"]
    )


def test_generated_browser_python_is_ignored_and_not_tracked() -> None:
    assert "/web/assets/py/" in _read(".gitignore").splitlines()
    tracked = subprocess.run(
        ["git", "ls-files", "web/assets/py"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert tracked == ""


def test_tag_release_workflow_is_verified_and_does_not_publish_to_pypi() -> None:
    workflow = _read(".github/workflows/release.yml")

    required = (
        'tags:\n      - "v*"',
        "uv sync --locked",
        "must be an annotated tag",
        "make fmt-check",
        "make lint",
        "make stage-web",
        "make golden-check",
        'pytest -q -m "not e2e"',
        "playwright install --with-deps chromium webkit",
        "Run full Chromium browser suite",
        "pytest -q -m e2e",
        "--browser chromium",
        "Run WebKit initial-render smoke test",
        "test_initial_render_loads_pyodide_and_plots",
        "--browser webkit",
        "web/assets/py/manifest.json",
        "git archive",
        "cmp ",
        "sha256sum",
        "browser-stage-manifest.json",
        "--verify-tag",
        "--prerelease",
        "--notes-file",
        r"capture && /^\[[^]]+\]:/ { exit }",
    )
    for value in required:
        assert value in workflow
    assert workflow.count("git archive") == 2
    lowered = workflow.lower()
    assert "pypi" not in lowered
    assert "twine" not in lowered
    assert "uv publish" not in lowered

    browser_install = workflow.index("playwright install --with-deps chromium webkit")
    chromium_suite = workflow.index("Run full Chromium browser suite")
    webkit_smoke = workflow.index("Run WebKit initial-render smoke test")
    bundle_build = workflow.index("Build deterministic release bundle")
    bundle_upload = workflow.index("Upload verified release bundle")
    assert browser_install < chromium_suite < webkit_smoke < bundle_build < bundle_upload
    assert re.search(r"(?m)^  release:\n    needs: verify-build$", workflow)


def test_release_metadata_and_core_provenance_are_synchronized() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    assert pyproject["project"]["version"] == "0.1.1"

    citation = _read("CITATION.cff")
    changelog = _read("CHANGELOG.md")
    assert "version: 0.1.1" in citation
    assert 'date-released: "2026-07-29"' in citation
    assert "## [0.1.1] - 2026-07-29" in changelog

    provenance_surfaces = (
        _read("pyproject.toml"),
        _read("README.md"),
        changelog,
        _read("docs/adr/0002-released-core-and-generated-browser-stage.md"),
    )
    assert CORE_WHEEL_URL in provenance_surfaces[0]
    for surface in provenance_surfaces:
        assert CORE_WHEEL_SHA256 in surface
    for surface in provenance_surfaces[1:]:
        assert CORE_RELEASE_URL in surface

    decisions = _read("docs/DECISIONS.md")
    migration_log = _read("docs/migration/MIGRATION_LOG.md")
    llms = _read("llms.txt")
    assert f"`wald-inference` v{CORE_VERSION}" in decisions
    assert f"`wald-inference` v{CORE_VERSION}" in migration_log
    assert f"Numerical core: wald-inference {CORE_VERSION}" in llms
    for surface in (migration_log, llms):
        assert CORE_WHEEL_SHA256 in surface
