from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGE_SCRIPT_COMMAND = "uv run python scripts/stage_web_python.py"
CORE_VERSION = "0.4.1"
CORE_RELEASE_URL = "https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1"
CORE_WHEEL_URL = (
    "https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/"
    "wald_inference-0.4.1-py3-none-any.whl"
)
CORE_WHEEL_SHA256 = "d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b"


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
    assert re.search(
        r"(?m)^portfolio-links:\n\tuv run python scripts/check_portfolio_links.py$", makefile
    )
    assert re.search(r"(?m)^verify:.*\bportfolio-links\b.*\btest\b.*\be2e\b", makefile)
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
        assert "actions/checkout@v7" in workflow, path
        assert "actions/setup-python@v7" in workflow, path
        assert "astral-sh/setup-uv@v9.0.0" in workflow, path

    assert "path: ./web" in workflows[".github/workflows/pages.yml"]
    assert "actions/configure-pages@v6" in workflows[".github/workflows/pages.yml"]
    assert "actions/upload-pages-artifact@v5" in workflows[".github/workflows/pages.yml"]
    assert "actions/deploy-pages@v5" in workflows[".github/workflows/pages.yml"]
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
        "scripts/check_portfolio_links.py --live",
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
        "actions/download-artifact@v8",
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
    assert pyproject["project"]["version"] == "0.2.5"

    citation = _read("CITATION.cff")
    changelog = _read("CHANGELOG.md")
    assert "version: 0.2.5" in citation
    assert 'date-released: "2026-07-30"' in citation
    assert "## [0.2.5] - 2026-07-30" in changelog
    release_notes = changelog.split("## [0.2.5] - 2026-07-30", 1)[1].split(
        "## [0.2.4] - 2026-07-30", 1
    )[0]
    for required_release_detail in (
        "docs/SCIENTIFIC_SCOPE.md",
        "docs/VALIDATION.md",
        "wald-inference` v0.4.1",
        "B01-B08",
        "compatibility-curve",
        "wald-likelihood-support",
        "critical-effect-size",
        "type-s-m-calibrator",
        "precision-guardrail-planner",
        "docs/MAINTENANCE.md",
        "backward compatible",
        "not clinical validation or scientific revalidation",
    ):
        assert required_release_detail in release_notes

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


def test_migration_records_do_not_retain_superseded_v023_release_claims() -> None:
    metadata_audit = _read("docs/migration/METADATA_AUDIT.md")
    migration_log = _read("docs/migration/MIGRATION_LOG.md")
    combined = f"{metadata_audit}\n{migration_log}"

    for stale_claim in (
        "v0.2.3 release-candidate state",
        "v0.2.3 is gated on CI/review and an annotated tag",
        "completion requires the tagged release",
        "Pending at candidate source time",
        "Planned annotated `v0.2.3` prerelease",
        "To be published by the v0.2.3 release workflow",
        "v0.2.3 tag, release assets, Pages deployment, and independent rerun remain pending",
        "Core and app releases intentionally remain GitHub prereleases until",
    ):
        assert stale_claim not in combined

    for release_evidence in (
        "427d425d16f847a9462ef0084d96841137995512",
        "30561596025",
        "30561595983",
        "30562484672",
        "8a5a07687ba4b5cfa093266264a8911b2f56968b55e33ca0b772db07da4d82dd",
        "e16e0cbfe85a83bf1b347a3a606cc747136e6ef86288133bb2caa65f07a5d54f",
        "d3844f4d39cfca845ec6452d2d7a6df640e40acaa49fbe8d2a5e8ea42f89f2b1",
    ):
        assert release_evidence in migration_log


def test_current_core_publication_state_is_stable_and_app_state_is_distinct() -> None:
    readme = _read("README.md")
    migration_log = _read("docs/migration/MIGRATION_LOG.md")
    changelog = _read("CHANGELOG.md")
    normalized_migration_log = " ".join(migration_log.split())

    assert "| Release status observed 2026-07-30 | GitHub stable release |" in readme
    assert (
        "Core v0.4.1 was subsequently promoted to a stable GitHub release"
        in normalized_migration_log
    )
    assert (
        "Focused and integrated apps remain explicitly experimental prereleases"
        in normalized_migration_log
    )
    assert "retaining this integrated app's experimental GitHub-prerelease status" in changelog


def test_scientific_repository_documentation_matrix_is_complete() -> None:
    required_paths = (
        "README.md",
        "LICENSE",
        "CITATION.cff",
        "AGENTS.md",
        "CHANGELOG.md",
        "docs/SCIENTIFIC_SCOPE.md",
        "docs/VALIDATION.md",
        "docs/PRIVACY.md",
        "docs/DECISIONS.md",
        "docs/MAINTENANCE.md",
        "llms.txt",
    )
    for relative_path in required_paths:
        path = PROJECT_ROOT / relative_path
        assert path.is_file() and path.stat().st_size > 0, relative_path

    scientific_scope = _read("docs/SCIENTIFIC_SCOPE.md")
    validation = _read("docs/VALIDATION.md")
    readme = _read("README.md")
    assert "**Task question:**" in readme
    assert "Observed-data reconstruction" in scientific_scope
    assert "Design calibration" in scientific_scope
    assert "wald-inference` 0.4.1" in scientific_scope
    assert "not scientifically or clinically validated" in scientific_scope
    assert "pre-split-baseline-2026-07-29" in validation
    assert "rtol=1e-12" in validation
    assert "make verify" in validation
    assert "portfolio audit" in validation


def test_integrated_role_maintenance_and_request_routing_are_explicit() -> None:
    readme = _read("README.md")
    maintenance = _read("docs/MAINTENANCE.md")
    privacy = _read("docs/PRIVACY.md")
    core_checklist = _read("docs/CORE_UPGRADE_CHECKLIST.md")
    feature_template = _read(".github/ISSUE_TEMPLATE/feature_request.md")
    pull_request_template = _read(".github/PULL_REQUEST_TEMPLATE.md")
    html = _read("web/index.html")

    for surface in (readme, maintenance, html):
        assert "https://reblocke.github.io/wald-inference-tools/" in surface
    for focused_repository in (
        "compatibility-curve",
        "wald-likelihood-support",
        "critical-effect-size",
        "type-s-m-calibrator",
        "precision-guardrail-planner",
    ):
        assert focused_repository in readme
        assert focused_repository in feature_template
        assert focused_repository in html
    for heading in (
        "## Supported changes",
        "## Normally out of scope",
        "## Compatibility policy",
        "## Future archival criteria",
    ):
        assert heading in maintenance
    assert "feature-frozen" in maintenance
    assert "Archival is a human decision" in maintenance
    for boundary in ("local storage", "session storage", "IndexedDB", "cookies", "telemetry"):
        assert boundary in privacy
    assert "not included in those requests or transmitted" in privacy
    assert "make golden-check" in core_checklist
    assert "make portfolio-links" in pull_request_template
    assert "Integrated Wald Inference Workbench" in html
    assert "not an exact profile-likelihood tool" in html
    assert "posterior calculator" in html
    assert "clinical" in html
