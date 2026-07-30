from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_SOURCE = PROJECT_ROOT / "web" / "assets" / "config.js"
RUNTIME_SOURCE = PROJECT_ROOT / "web" / "assets" / "runtime.js"
INDEX_SOURCE = PROJECT_ROOT / "web" / "index.html"
E2E_CONFTEST_SOURCE = PROJECT_ROOT / "tests" / "e2e" / "conftest.py"


def test_browser_runtime_uses_the_generated_manifest_without_a_hardcoded_file_list() -> None:
    config_source = CONFIG_SOURCE.read_text(encoding="utf-8")
    runtime_source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert 'PYTHON_MANIFEST_URL = "./assets/py/manifest.json"' in config_source
    assert "PYTHON_PACKAGE_FILES" not in config_source
    assert "PYTHON_PACKAGE_FILES" not in runtime_source
    assert '"core.py"' not in runtime_source
    assert '"design.py"' not in runtime_source
    assert '"web_contract.py"' not in runtime_source


def test_browser_runtime_fetches_uncached_digest_addressed_files_and_verifies_before_import() -> (
    None
):
    runtime_source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert 'searchParams.set("sha256", fileRecord.sha256)' in runtime_source
    assert runtime_source.count('{ cache: "no-store" }') == 2
    assert 'subtle.digest("SHA-256", bytes)' in runtime_source
    assert "buildBundleDescriptor(verifiedFiles)" in runtime_source
    assert "for (const fileRecord of manifestFiles)" in runtime_source
    assert "Promise.all(" not in runtime_source

    verify_index = runtime_source.index("const verifiedBundle = await loadVerifiedPythonBundle();")
    pyodide_index = runtime_source.index(
        "const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });"
    )
    write_index = runtime_source.index(
        "await installVerifiedPythonFiles(pyodide, verifiedBundle.files);"
    )
    import_index = runtime_source.index("from confcurve import compute_curves")
    assert verify_index < pyodide_index < write_index < import_index


def test_browser_has_a_noninferential_technical_version_footer() -> None:
    index_source = INDEX_SOURCE.read_text(encoding="utf-8")
    runtime_source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert 'id="technical-version"' in index_source
    assert "Runtime versions pending verification." in index_source
    assert "showVerifiedVersions(verifiedBundle.manifest, runtimeVersions)" in runtime_source
    assert "CurveResponse" not in runtime_source


def test_e2e_server_does_not_block_on_an_unread_access_log_pipe() -> None:
    conftest_source = E2E_CONFTEST_SOURCE.read_text(encoding="utf-8")

    assert "stdout=subprocess.DEVNULL" in conftest_source
    assert "stdout=subprocess.PIPE" not in conftest_source
