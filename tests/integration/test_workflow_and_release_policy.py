from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = PROJECT_ROOT / ".github" / "workflows"
STAGE_SCRIPT_COMMAND = "uv run python scripts/stage_web_python.py"
CORE_VERSION = "0.4.2"
CORE_RELEASE_URL = "https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.2"
CORE_WHEEL_URL = (
    "https://github.com/reblocke/wald-inference-core/releases/download/v0.4.2/"
    "wald_inference-0.4.2-py3-none-any.whl"
)
CORE_WHEEL_SHA256 = "225331d7b9d7b70e2508eecb92851a92a8c4e245baf412a1eb0f464d85da1349"
GH_CLI_VERSION = "2.93.0"
GH_CLI_LINUX_AMD64_SHA256 = "02d1290eba130e0b896f3709ffff22e1c75a51475ddb70476a85abc6b5807af0"
EXPECTED_ACTION_PINS = {
    "actions/checkout": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "7.0.1"),
    "actions/setup-python": ("5fda3b95a4ea91299a34e894583c3862153e4b97", "7.0.0"),
    "astral-sh/setup-uv": ("c771a70e6277c0a99b617c7a806ffedaca235ff9", "9.0.0"),
    "actions/upload-artifact": ("043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "7.0.1"),
    "actions/download-artifact": ("3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c", "8.0.1"),
    "actions/configure-pages": ("45bfe0192ca1faeb007ade9deae92b16b8254a0d", "6.0.0"),
    "actions/upload-pages-artifact": ("fc324d3547104276b827a68afc52ff2a11cc49c9", "5.0.0"),
    "actions/deploy-pages": ("cd2ce8fcbc39b97be8ca5fce6e763baed58fa128", "5.0.0"),
}


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _dependabot_update_block(config: str, ecosystem: str) -> str:
    marker = f'  - package-ecosystem: "{ecosystem}"'
    start = config.index(marker)
    end = config.find("\n  - package-ecosystem:", start + len(marker))
    return config[start:] if end == -1 else config[start:end]


def _dependabot_mapping_block(update: str, key: str) -> str:
    marker = re.compile(rf"(?m)^    {re.escape(key)}:\s*$")
    matches = list(marker.finditer(update))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {key!r} mapping in the updater")
    start = matches[0].end()
    next_key = re.search(r"(?m)^    [A-Za-z0-9_-]+:\s*(?:#.*)?$", update[start:])
    end = len(update) if next_key is None else start + next_key.start()
    return update[start:end]


def _dependabot_version_ignore_rules(update: str) -> list[tuple[str, str]]:
    ignore = _dependabot_mapping_block(update, "ignore")
    rules = re.findall(
        r'^      - dependency-name: "([^"]+)"\n'
        r'^        versions: \["([^"]+)"\]$',
        ignore,
        re.MULTILINE,
    )
    if ignore.count("      - dependency-name:") != len(rules):
        raise ValueError("every ignore entry must be an exact dependency/version rule")
    if ignore.count("        versions:") != len(rules):
        raise ValueError("every ignore entry must have exactly one inline versions range")
    if update.count("      - dependency-name:") != len(rules):
        raise ValueError("dependency/version rules must not appear outside the ignore mapping")
    return rules


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

    assert "path: ./web" in workflows[".github/workflows/pages.yml"]
    assert "actions/configure-pages@" in workflows[".github/workflows/pages.yml"]
    assert "actions/upload-pages-artifact@" in workflows[".github/workflows/pages.yml"]
    assert "actions/deploy-pages@" in workflows[".github/workflows/pages.yml"]
    assert (
        "git status --porcelain --untracked-files=all" in workflows[".github/workflows/pages.yml"]
    )


def test_workflows_pin_reviewed_external_actions_to_full_shas() -> None:
    use_value_pattern = re.compile(r"^\s*(?:-\s+)?uses:\s+(?P<value>\S+)(?:\s+#.*)?$")
    external_use_pattern = re.compile(
        r"^\s*(?:-\s+)?uses:\s+"
        r"(?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)"
        r"@(?P<sha>[0-9a-f]{40})"
        r"\s+#\s+v(?P<version>\d+\.\d+\.\d+)\s*$"
    )
    violations: list[str] = []
    seen_pins: dict[str, set[tuple[str, str]]] = {}
    workflows = sorted(
        {*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")},
    )

    for workflow in workflows:
        for line_number, line in enumerate(
            workflow.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if "uses:" not in line:
                continue
            parsed_use = use_value_pattern.fullmatch(line)
            if parsed_use is None:
                violations.append(f"{workflow.name}:{line_number}:{line.strip()}")
                continue
            if parsed_use.group("value").startswith("./"):
                continue
            parsed_external = external_use_pattern.fullmatch(line)
            if parsed_external is None:
                violations.append(f"{workflow.name}:{line_number}:{line.strip()}")
                continue
            action = parsed_external.group("action")
            pin = (parsed_external.group("sha"), parsed_external.group("version"))
            seen_pins.setdefault(action, set()).add(pin)

    assert violations == []
    assert seen_pins == {action: {pin} for action, pin in EXPECTED_ACTION_PINS.items()}


def test_workflow_permissions_check_ids_credentials_and_release_cache_are_fail_closed() -> None:
    ci = _read(".github/workflows/ci.yml")
    pages = _read(".github/workflows/pages.yml")
    release = _read(".github/workflows/release.yml")

    assert "permissions:\n  contents: read" in ci
    assert "group: ci-${{ github.workflow }}-${{ github.ref }}" in ci
    assert "cancel-in-progress: true" in ci
    for job_name in ("test", "e2e_chromium", "e2e_webkit_smoke"):
        assert f"    name: {job_name}" in ci

    assert "permissions: {}" in pages
    assert "build:\n    name: build\n    permissions:\n      contents: read" in pages
    assert (
        "deploy:\n"
        "    name: deploy\n"
        "    needs: build\n"
        "    permissions:\n"
        "      pages: write # Required to publish the verified Pages artifact.\n"
        "      id-token: write # Required for the Pages deployment identity token." in pages
    )
    build_block, deploy_block = pages.split("\n  deploy:", maxsplit=1)
    assert "id-token: write" not in build_block
    assert "pages: write" not in build_block
    assert "actions/configure-pages@" not in build_block
    assert "contents: read" not in deploy_block
    assert "actions/configure-pages@" in deploy_block

    assert "permissions: {}" in release
    assert (
        "verify-build:\n    name: verify-build\n    permissions:\n      contents: read" in release
    )
    verify_build_block, publish_block = release.split("\n  release:", maxsplit=1)
    assert "enable-cache: true" not in verify_build_block
    assert "enable-cache: false" in verify_build_block
    assert release.count("contents: write") == 1
    assert release.count("attestations: read") == 1
    assert "attestations: read" not in verify_build_block
    assert (
        "release:\n"
        "    name: release\n"
        "    needs: verify-build\n"
        "    permissions:\n"
        "      contents: write # Required only to create and publish the verified release.\n"
        "      attestations: read # Required to verify the immutable release and asset "
        "attestations." in release
    )
    assert "contents: read" not in publish_block

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            {*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")},
        )
    )
    checkout_count = workflow_text.count("uses: actions/checkout@")
    assert checkout_count > 0
    assert workflow_text.count("persist-credentials: false") == checkout_count


def test_release_verifies_annotated_main_contained_tag_before_repository_execution() -> None:
    release = _read(".github/workflows/release.yml")
    version_parse = (
        "python -I -c 'import tomllib; "
        'print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])\''
    )

    assert 'git cat-file -t "$GITHUB_REF_NAME"' in release
    assert 'git rev-parse "$GITHUB_REF_NAME^{commit}"' in release
    assert "/git/ref/tags/${GITHUB_REF_NAME}" in release
    assert 'git rev-parse "refs/tags/$GITHUB_REF_NAME"' in release
    assert "--jq '.tag'" in release
    assert ".verification.verified" not in release
    assert ".verification.reason" not in release
    assert "--jq '.object.sha'" in release
    assert "--jq '.object.type'" in release
    assert ')" = "commit"' in release
    assert '"https://github.com/${GITHUB_REPOSITORY}.git"' in release
    assert "+refs/heads/main:refs/remotes/origin/main" in release
    assert 'git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/main' in release
    assert version_parse in release
    assert 'test "$package_version" = "$version"' in release
    assert 'grep -Fx "version: $version" CITATION.cff' in release

    remote_tag = release.index("/git/ref/tags/${GITHUB_REF_NAME}")
    protected_main = release.index("git merge-base --is-ancestor")
    setup_python = release.index("actions/setup-python@")
    setup_uv = release.index("astral-sh/setup-uv@")
    version = release.index(version_parse)
    install = release.index("uv sync --locked")
    execute = release.index("make fmt-check")
    assert remote_tag < protected_main < setup_python < setup_uv < version < install < execute


def test_release_is_exact_draft_first_stable_and_postpublish_immutable() -> None:
    release = _read(".github/workflows/release.yml")
    publish = release[release.index("\n  release:") :]

    assert "/immutable-releases" not in release
    assert "RELEASE_SETTINGS_READ_TOKEN" not in release
    assert publish.count("GH_TOKEN: ${{ github.token }}") == 3
    assert '--prefix="conf_curve_likelihood-$version/"' in release
    assert '"$assets/browser-stage-manifest.json"' in release
    assert "sha256sum --check SHA256SUMS" in release
    assert "actions/upload-artifact@" in release
    assert "actions/download-artifact@" in release
    assert 'test "$(find release-bundle/assets -maxdepth 1 -type f | wc -l)" -eq 3' in release
    assert "--draft" in release
    assert "--verify-tag" in release
    assert "--prerelease" not in release
    assert 'awk -v version="$version"' in release
    assert "--notes-file release-bundle/release-notes.md" in release
    assert "--notes-file CHANGELOG.md" not in release
    assert "jq --exit-status --join-output '.body'" in release
    assert "cmp --silent release-bundle/release-notes.md" in release
    assert "GH_REPO: ${{ github.repository }}" in release
    assert "gh release download" in release
    assert "diff --recursive --brief release-bundle/assets remote-release-assets" in release
    assert "--draft=false" in release
    assert "--json isImmutable" in release
    assert "gh release verify" in release
    assert "gh release verify-asset" in release
    assert (
        publish.index("gh release create")
        < publish.index("gh release download")
        < publish.index("--draft=false")
        < publish.index("gh release verify")
    )


def test_release_notes_must_contain_non_whitespace_before_transfer_and_publish() -> None:
    release = _read(".github/workflows/release.yml")

    assert "grep -q '[^[:space:]]' \"$bundle/release-notes.md\"" in release
    assert "grep -q '[^[:space:]]' \"release-bundle/release-notes.md\"" in release
    assert "test -s release-bundle/release-notes.md" not in release
    assert 'test -s "$bundle/release-notes.md"' not in release

    def notes_pass_guard(notes: str) -> bool:
        result = subprocess.run(
            ["grep", "-q", "[^[:space:]]"],
            input=notes,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    for notes in ("", " ", "\t", "\n", " \t\r\n"):
        assert not notes_pass_guard(notes)
    for notes in ("Release note", "\n- Preserve exact release provenance.\n"):
        assert notes_pass_guard(notes)


def test_release_installs_checksummed_github_cli_before_credentialed_commands() -> None:
    release = _read(".github/workflows/release.yml")

    assert f'GH_CLI_VERSION: "{GH_CLI_VERSION}"' in release
    assert f'GH_CLI_LINUX_AMD64_SHA256: "{GH_CLI_LINUX_AMD64_SHA256}"' in release
    assert release.count("Install checksummed GitHub CLI") == 2
    assert release.count("sha256sum --check --strict -") == 2
    assert release.count("Confirm the checksummed GitHub CLI is selected") == 2
    assert release.index("Install checksummed GitHub CLI") < release.index(
        "Verify the annotated remote tag and event commit"
    )
    publish = release[release.index("\n  release:") :]
    assert publish.index("Confirm the checksummed GitHub CLI is selected") < publish.index(
        "gh release create"
    )


def test_dependabot_covers_locked_python_and_actions_without_auto_merge() -> None:
    dependabot = _read(".github/dependabot.yml")
    pyproject = tomllib.loads(_read("pyproject.toml"))
    uv_update = _dependabot_update_block(dependabot, "uv")
    actions_update = _dependabot_update_block(dependabot, "github-actions")

    assert dependabot.count('interval: "weekly"') == 2
    assert dependabot.count("default-days: 7") == 2
    assert "python-dependencies:" in dependabot
    assert "github-actions:" in dependabot
    assert [
        dependency
        for dependency in pyproject["project"]["dependencies"]
        if dependency.startswith(("numpy", "scipy"))
    ] == [
        "numpy>=2.2.5,<2.3",
        "scipy>=1.14.1,<1.15",
    ]
    version_ignore_rules = _dependabot_version_ignore_rules(uv_update)
    assert version_ignore_rules == [
        ("numpy", ">=2.3"),
        ("scipy", ">=1.15"),
    ]
    assert 'dependency-name: "numpy"' not in actions_update
    assert 'dependency-name: "scipy"' not in actions_update
    assert "automerge" not in dependabot.lower()


def test_dependabot_version_ignore_regression_rejects_structural_mutations() -> None:
    dependabot = _read(".github/dependabot.yml")
    expected_rules = [
        ("numpy", ">=2.3"),
        ("scipy", ">=1.15"),
    ]
    numpy_rule = '      - dependency-name: "numpy"\n        versions: [">=2.3"]\n'
    scipy_rule = '      - dependency-name: "scipy"\n        versions: [">=1.15"]\n'
    ignore_block = f"    ignore:\n{numpy_rule}{scipy_rule}"

    renamed_ignore = dependabot.replace("    ignore:", "    allow:", 1)
    with pytest.raises(ValueError, match="exactly one 'ignore' mapping"):
        _dependabot_version_ignore_rules(
            _dependabot_update_block(renamed_ignore, "uv"),
        )

    missing_ignore = dependabot.replace(ignore_block, "", 1)
    with pytest.raises(ValueError, match="exactly one 'ignore' mapping"):
        _dependabot_version_ignore_rules(
            _dependabot_update_block(missing_ignore, "uv"),
        )

    moved_rule = dependabot.replace(
        ignore_block,
        f"    ignore:\n{numpy_rule}    proposed-version-rules:\n{scipy_rule}",
        1,
    )
    with pytest.raises(ValueError, match="outside the ignore mapping"):
        _dependabot_version_ignore_rules(
            _dependabot_update_block(moved_rule, "uv"),
        )

    mispaired_range = dependabot.replace(
        'versions: [">=1.15"]',
        'versions: [">=2.3"]',
        1,
    )
    assert (
        _dependabot_version_ignore_rules(
            _dependabot_update_block(mispaired_range, "uv"),
        )
        != expected_rules
    )


def test_public_coordination_files_preserve_scope_and_private_reporting() -> None:
    security = _read("SECURITY.md")
    normalized_security = " ".join(security.lower().split())
    contributing = _read("CONTRIBUTING.md")
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")
    engineering_issue = _read(".github/ISSUE_TEMPLATE/engineering-bug.yml")
    accessibility_issue = _read(".github/ISSUE_TEMPLATE/accessibility-report.yml")
    security_contact = _read(".github/ISSUE_TEMPLATE/security-contact.yml")
    feature_request = _read(".github/ISSUE_TEMPLATE/feature_request.md")
    pull_request = _read(".github/PULL_REQUEST_TEMPLATE.md")

    assert "/security/advisories/new" in security
    assert "Do not disclose vulnerability details in a public issue" in security
    assert "protected health information" in security.lower()
    assert "synthetic" in security.lower()
    assert "does not establish clinical decision support" in normalized_security
    assert "sole numerical and formula authority" in contributing
    assert "B01–B08" in contributing
    assert "feature-frozen" in contributing
    assert "release_settings_read_token" not in contributing.lower()
    assert "blank_issues_enabled: false" in issue_config
    assert "/security/advisories/new" in issue_config
    assert "protected health information" in engineering_issue.lower()
    assert "behavior owned by this repository" in engineering_issue.lower()
    assert "authoritative upstream" in engineering_issue.lower()
    assert "assistive technology" in accessibility_issue.lower()
    assert "protected health information" in accessibility_issue.lower()
    assert "include no vulnerability details" in security_contact.lower()
    assert "protected health information" in security_contact.lower()
    assert "feature-frozen" in feature_request
    assert "SECURITY.md" in feature_request
    assert "All 22 B01–B08 cases pass" in pull_request
    assert "make verify" in pull_request
    assert "make portfolio-links" in pull_request


def test_current_release_docs_match_credential_free_annotated_tag_policy() -> None:
    current_docs = (
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        PROJECT_ROOT / "docs" / "MAINTENANCE.md",
        PROJECT_ROOT / "docs" / "VALIDATION.md",
    )
    for path in current_docs:
        text = path.read_text(encoding="utf-8")
        assert "RELEASE_SETTINGS_READ_TOKEN" not in text
        assert re.search(r"\bsigned\b", text, flags=re.IGNORECASE) is None

    decisions = _read("docs/DECISIONS.md")
    assert "2026-07-31: Release automation uses only the job-scoped GitHub token" in decisions
    assert "supersedes only those two requirements" in decisions
    assert "GitHub-verified signed annotated tag" in decisions


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
        "--draft",
        "--notes-file",
        "actions/download-artifact@",
        r"capture && /^\[[^]]+\]:/ { exit }",
    )
    for value in required:
        assert value in workflow
    assert workflow.count("git archive") == 2
    lowered = workflow.lower()
    assert "pypi" not in lowered
    assert "twine" not in lowered
    assert "uv publish" not in lowered
    assert "--prerelease" not in workflow

    browser_install = workflow.index("playwright install --with-deps chromium webkit")
    chromium_suite = workflow.index("Run full Chromium browser suite")
    webkit_smoke = workflow.index("Run WebKit initial-render smoke test")
    bundle_build = workflow.index("Build deterministic release bundle")
    bundle_upload = workflow.index("Upload verified release bundle")
    assert browser_install < chromium_suite < webkit_smoke < bundle_build < bundle_upload
    assert re.search(
        r"(?m)^  release:\n    name: release\n    needs: verify-build$",
        workflow,
    )


def test_release_metadata_and_core_provenance_are_synchronized() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    assert pyproject["project"]["version"] == "0.2.6"

    citation = _read("CITATION.cff")
    changelog = _read("CHANGELOG.md")
    assert "version: 0.2.6" in citation
    assert 'date-released: "2026-07-31"' in citation
    assert "## [0.2.6] - 2026-07-31" in changelog
    release_notes = changelog.split("## [0.2.6] - 2026-07-31", 1)[1].split(
        "## [0.2.5] - 2026-07-30", 1
    )[0]
    for required_release_detail in (
        "docs/SCIENTIFIC_SCOPE.md",
        "docs/VALIDATION.md",
        "wald-inference` v0.4.2",
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


def test_dev_security_versions_preserve_frozen_pytest_provenance() -> None:
    expected = {
        "idna": "3.15",
        "pygments": "2.20.0",
        "pytest": "9.0.3",
        "requests": "2.33.0",
        "urllib3": "2.7.0",
    }
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dev_requirements = set(pyproject["dependency-groups"]["dev"])
    assert {f"{name}=={version}" for name, version in expected.items()} <= dev_requirements

    lock = tomllib.loads(_read("uv.lock"))
    locked_versions = {package["name"]: package["version"] for package in lock["package"]}
    assert {name: locked_versions[name] for name in expected} == expected

    golden_manifest = json.loads(_read("tests/golden/manifest.json"))
    assert golden_manifest["versions"]["pytest"] == "9.0.2"
    golden_script = _read("scripts/golden_baseline.py")
    assert '"confcurve": "0.1.0"' in golden_script
    assert '"pytest": "9.0.2"' in golden_script


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

    assert "| Release status observed 2026-07-31 | GitHub stable immutable release |" in readme
    assert (
        "Core v0.4.2 was published as a stable immutable GitHub release" in normalized_migration_log
    )
    assert "no tag or release exists from this candidate change" in normalized_migration_log
    assert "not clinical validation or scientific revalidation" in changelog


def test_scientific_repository_documentation_matrix_is_complete() -> None:
    required_paths = (
        "README.md",
        "LICENSE",
        "CITATION.cff",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
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
    assert "wald-inference` 0.4.2" in scientific_scope
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
