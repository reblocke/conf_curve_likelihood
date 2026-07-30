from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import confcurve.staging as staging
from confcurve.stage import PACKAGE_FILES, package_root, stage_web_python_package
from confcurve.staging import StagingError, stage_browser_packages

CORE_VERSION = staging.PACKAGE_STAGE_SPECS[1].expected_version


def test_stage_web_python_package_copies_source_files(tmp_path: Path) -> None:
    written = stage_web_python_package(tmp_path)

    assert [path.name for path in written] == PACKAGE_FILES

    source_dir = package_root()
    for file_name in PACKAGE_FILES:
        assert (tmp_path / file_name).read_text(encoding="utf-8") == (
            source_dir / file_name
        ).read_text(encoding="utf-8")


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _bundle_sha256(manifest: dict[str, object]) -> str:
    packages = manifest["packages"]
    assert isinstance(packages, list)
    records = sorted(
        (
            record
            for package in packages
            for record in package["files"]  # type: ignore[index]
        ),
        key=lambda record: record["path"],
    )
    payload = "".join(
        f"{record['path']}\0{record['sha256']}\0{record['bytes']}\n" for record in records
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _record_hash(contents: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(contents).digest())
    return encoded.rstrip(b"=").decode()


def _fake_core_distribution(
    tmp_path: Path,
    *,
    direct_url: str = staging.CORE_ARTIFACT_URL,
    lock_hash: str = staging.CORE_ARTIFACT_SHA256,
) -> tuple[importlib.metadata.PathDistribution, Path, Path]:
    site_packages = tmp_path / "site-packages"
    package_root = site_packages / "wald_inference"
    dist_info = site_packages / f"wald_inference-{CORE_VERSION}.dist-info"
    project_root = tmp_path / "project"
    package_root.mkdir(parents=True)
    dist_info.mkdir()
    project_root.mkdir()

    package_contents = f'__version__ = "{CORE_VERSION}"\n'.encode()
    (package_root / "__init__.py").write_bytes(package_contents)
    (dist_info / "METADATA").write_text(
        (f"Metadata-Version: 2.4\nName: wald-inference\nVersion: {CORE_VERSION}\n"),
        encoding="utf-8",
    )
    (dist_info / "direct_url.json").write_text(
        json.dumps({"url": direct_url, "archive_info": {}}),
        encoding="utf-8",
    )
    (dist_info / "RECORD").write_text(
        (
            "wald_inference/__init__.py,"
            f"sha256={_record_hash(package_contents)},{len(package_contents)}\n"
            f"wald_inference-{CORE_VERSION}.dist-info/RECORD,,\n"
        ),
        encoding="utf-8",
    )
    (project_root / "uv.lock").write_text(
        (
            "version = 1\n\n"
            "[[package]]\n"
            'name = "wald-inference"\n'
            f'version = "{CORE_VERSION}"\n'
            f'source = {{ url = "{staging.CORE_ARTIFACT_URL}" }}\n'
            "wheels = [\n"
            "    { "
            f'url = "{staging.CORE_ARTIFACT_URL}", '
            f'hash = "sha256:{lock_hash}"'
            " },\n"
            "]\n"
        ),
        encoding="utf-8",
    )
    return importlib.metadata.PathDistribution(dist_info), package_root, project_root


def _use_fake_core_distribution(
    monkeypatch: pytest.MonkeyPatch,
    distribution: importlib.metadata.PathDistribution,
    import_root: Path,
) -> None:
    monkeypatch.setattr(
        staging.importlib.metadata,
        "distribution",
        lambda name: distribution,
    )
    monkeypatch.setattr(
        staging.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(submodule_search_locations=[str(import_root)]),
    )


def test_browser_stage_is_complete_deterministic_and_removes_stale_files(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    target_root = tmp_path / "assets" / "py"

    first_manifest = stage_browser_packages(target_root, project_root=project_root)
    first_snapshot = _tree_snapshot(target_root)
    manifest_path = target_root / "manifest.json"
    parsed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert parsed_manifest == first_manifest
    assert list(parsed_manifest) == [
        "schema_version",
        "pyodide_version",
        "source_commit",
        "bundle_sha256",
        "packages",
    ]
    assert parsed_manifest["schema_version"] == 1
    assert parsed_manifest["pyodide_version"] == "0.29.3"
    assert len(parsed_manifest["source_commit"]) == 40
    assert parsed_manifest["source_commit"] == parsed_manifest["source_commit"].lower()
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert parsed_manifest["source_commit"] == source_commit

    packages = parsed_manifest["packages"]
    assert [
        (package["role"], package["distribution"], package["import_name"], package["version"])
        for package in packages
    ] == [
        ("app", "confcurve", "confcurve", "0.2.5"),
        ("core", "wald-inference", "wald_inference", CORE_VERSION),
    ]

    all_record_paths: list[str] = []
    for package in packages:
        assert list(package) == [
            "role",
            "distribution",
            "import_name",
            "version",
            "files",
        ]
        assert package["files"] == sorted(
            package["files"],
            key=lambda record: record["path"],
        )

        import_spec = importlib.util.find_spec(package["import_name"])
        assert import_spec is not None
        assert import_spec.submodule_search_locations is not None
        [source_root_text] = import_spec.submodule_search_locations
        source_root = Path(source_root_text).resolve()

        for record in package["files"]:
            assert list(record) == ["path", "bytes", "sha256"]
            record_path = record["path"]
            all_record_paths.append(record_path)
            staged_contents = (target_root / record_path).read_bytes()
            source_relative = Path(record_path).relative_to(package["import_name"])
            assert staged_contents == (source_root / source_relative).read_bytes()
            assert record["bytes"] == len(staged_contents)
            assert record["sha256"] == hashlib.sha256(staged_contents).hexdigest()

    assert all_record_paths == sorted(all_record_paths)
    assert "manifest.json" not in all_record_paths
    assert parsed_manifest["bundle_sha256"] == _bundle_sha256(parsed_manifest)
    assert not any(
        path.name == "__pycache__"
        or path.name.endswith((".dist-info", ".egg-info"))
        or path.suffix in {".pyc", ".pyo"}
        for path in target_root.rglob("*")
    )

    stale_path = target_root / "confcurve" / "stale.py"
    stale_path.write_text("stale = True\n", encoding="utf-8")
    second_manifest = stage_browser_packages(target_root, project_root=project_root)

    assert second_manifest == first_manifest
    assert _tree_snapshot(target_root) == first_snapshot
    assert not stale_path.exists()


def test_app_stage_rejects_an_import_shadow_outside_the_source_commit_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    shadow_root = tmp_path / "shadow" / "confcurve"
    shadow_root.mkdir(parents=True)
    (shadow_root / "__init__.py").write_text('__version__ = "0.2.5"\n', encoding="utf-8")
    monkeypatch.setattr(staging, "_installed_package_root", lambda import_name: shadow_root)

    with pytest.raises(StagingError, match="must resolve to"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[0],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_core_stage_rejects_pythonpath_shadowing_of_the_distribution_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distribution, _, project_root = _fake_core_distribution(tmp_path)
    shadow_root = tmp_path / "shadow" / "wald_inference"
    shadow_root.mkdir(parents=True)
    (shadow_root / "__init__.py").write_text(
        f'__version__ = "{CORE_VERSION}"\n',
        encoding="utf-8",
    )
    _use_fake_core_distribution(monkeypatch, distribution, shadow_root)

    with pytest.raises(StagingError, match="does not match the installed"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[1],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_core_stage_rejects_a_recorded_file_mutated_after_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distribution, package_root, project_root = _fake_core_distribution(tmp_path)
    original = (package_root / "__init__.py").read_bytes()
    (package_root / "__init__.py").write_bytes(b"x" * len(original))
    _use_fake_core_distribution(monkeypatch, distribution, package_root)

    with pytest.raises(StagingError, match="does not match its RECORD sha256"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[1],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_core_stage_rejects_an_unrecorded_package_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distribution, package_root, project_root = _fake_core_distribution(tmp_path)
    (package_root / "injected.py").write_text("untrusted = True\n", encoding="utf-8")
    _use_fake_core_distribution(monkeypatch, distribution, package_root)

    with pytest.raises(StagingError, match="not exactly listed in RECORD"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[1],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_core_stage_rejects_wrong_direct_release_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distribution, package_root, project_root = _fake_core_distribution(
        tmp_path,
        direct_url="https://example.invalid/untrusted.whl",
    )
    _use_fake_core_distribution(monkeypatch, distribution, package_root)

    with pytest.raises(StagingError, match="approved release URL"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[1],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_core_stage_rejects_wrong_locked_wheel_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distribution, package_root, project_root = _fake_core_distribution(
        tmp_path,
        lock_hash="0" * 64,
    )
    _use_fake_core_distribution(monkeypatch, distribution, package_root)

    with pytest.raises(StagingError, match="approved wheel checksum"):
        staging._stage_package(
            staging.PACKAGE_STAGE_SPECS[1],
            tmp_path / "stage",
            project_root=project_root,
        )


def test_browser_stage_imports_both_packages_from_staged_tree(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    target_root = tmp_path / "assets" / "py"
    stage_browser_packages(target_root, project_root=project_root)

    environment = {**os.environ, "PYTHONPATH": str(target_root)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "import confcurve, wald_inference; "
                f"root = Path({str(target_root)!r}).resolve(); "
                "assert Path(confcurve.__file__).resolve().is_relative_to(root); "
                "assert Path(wald_inference.__file__).resolve().is_relative_to(root); "
                "print(confcurve.__version__, wald_inference.__version__)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
    )

    assert result.stdout.strip() == f"0.2.5 {CORE_VERSION}"


def test_browser_runtime_rejects_nonstandard_json_numbers() -> None:
    runtime_source = (Path("web") / "assets" / "runtime.js").read_text(encoding="utf-8")

    assert "json.dumps(compute_curves(json.loads(payload_json)), allow_nan=False)" in runtime_source


def test_staged_package_supports_top_level_import(tmp_path: Path) -> None:
    package_dir = tmp_path / "confcurve"
    stage_web_python_package(package_dir)

    environment = {**os.environ, "PYTHONPATH": str(tmp_path)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import confcurve; print('compute_curves' in confcurve.__all__)",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.stdout.strip() == "True"
