from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PYODIDE_VERSION = "0.29.3"
MANIFEST_FILENAME = "manifest.json"
SOURCE_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXCLUDED_DIRECTORY_SUFFIXES = (".dist-info", ".egg-info")
EXCLUDED_DIRECTORY_NAMES = {"__pycache__"}
EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo"}
CORE_ARTIFACT_URL = (
    "https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/"
    "wald_inference-0.4.1-py3-none-any.whl"
)
CORE_ARTIFACT_SHA256 = "d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b"


class StagingError(RuntimeError):
    """Raised when the deterministic browser bundle cannot be constructed."""


@dataclass(frozen=True)
class PackageStageSpec:
    role: str
    distribution: str
    import_name: str
    expected_version: str
    artifact_url: str | None = None
    artifact_sha256: str | None = None


PACKAGE_STAGE_SPECS = (
    PackageStageSpec(
        role="app",
        distribution="confcurve",
        import_name="confcurve",
        expected_version="0.2.3",
    ),
    PackageStageSpec(
        role="core",
        distribution="wald-inference",
        import_name="wald_inference",
        expected_version="0.4.1",
        artifact_url=CORE_ARTIFACT_URL,
        artifact_sha256=CORE_ARTIFACT_SHA256,
    ),
)


def _source_commit(project_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StagingError("Could not resolve the source Git commit for browser staging.") from exc

    commit = completed.stdout.strip()
    if SOURCE_COMMIT_PATTERN.fullmatch(commit) is None:
        raise StagingError("Browser staging requires a lowercase 40-hex source Git commit.")
    return commit


def _installed_package_root(import_name: str) -> Path:
    spec = importlib.util.find_spec(import_name)
    locations = None if spec is None else spec.submodule_search_locations
    if locations is None:
        raise StagingError(f"Installed package {import_name!r} is not importable.")
    roots = [Path(location).resolve() for location in locations]
    if len(roots) != 1 or not roots[0].is_dir():
        raise StagingError(
            f"Installed package {import_name!r} must resolve to one package directory."
        )
    return roots[0]


def _installed_distribution(
    spec: PackageStageSpec,
) -> importlib.metadata.Distribution:
    try:
        distribution = importlib.metadata.distribution(spec.distribution)
    except importlib.metadata.PackageNotFoundError as exc:
        raise StagingError(f"Installed distribution {spec.distribution!r} was not found.") from exc
    if distribution.version != spec.expected_version:
        raise StagingError(
            f"Installed distribution {spec.distribution!r} has version "
            f"{distribution.version!r}; expected {spec.expected_version!r}."
        )
    return distribution


def _is_excluded(relative_path: Path) -> bool:
    directory_parts = relative_path.parts[:-1]
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in directory_parts):
        return True
    if any(part.endswith(EXCLUDED_DIRECTORY_SUFFIXES) for part in directory_parts):
        return True
    return relative_path.suffix in EXCLUDED_FILE_SUFFIXES


def _package_source_files(package_root: Path) -> list[Path]:
    files = [
        path
        for path in package_root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not _is_excluded(path.relative_to(package_root))
    ]
    return sorted(files, key=lambda path: path.relative_to(package_root).as_posix())


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _verify_locked_artifact(
    spec: PackageStageSpec,
    *,
    project_root: Path,
) -> None:
    if spec.artifact_url is None or spec.artifact_sha256 is None:
        raise StagingError(
            f"Released package {spec.distribution!r} is missing its artifact provenance."
        )

    lock_path = project_root / "uv.lock"
    try:
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise StagingError("Could not read uv.lock for core artifact verification.") from exc

    expected_name = _normalized_distribution_name(spec.distribution)
    matches = [
        package
        for package in lock.get("package", [])
        if _normalized_distribution_name(str(package.get("name", ""))) == expected_name
    ]
    if len(matches) != 1:
        raise StagingError(f"uv.lock must contain exactly one {spec.distribution!r} package entry.")
    [package] = matches
    if package.get("version") != spec.expected_version:
        raise StagingError(f"uv.lock does not pin {spec.distribution!r} {spec.expected_version!r}.")
    if package.get("source") != {"url": spec.artifact_url}:
        raise StagingError(
            f"uv.lock does not pin {spec.distribution!r} to the approved release URL."
        )

    expected_wheel = {
        "url": spec.artifact_url,
        "hash": f"sha256:{spec.artifact_sha256}",
    }
    if package.get("wheels") != [expected_wheel]:
        raise StagingError(
            f"uv.lock does not bind {spec.distribution!r} to the approved wheel checksum."
        )


def _verify_distribution_direct_url(
    distribution: importlib.metadata.Distribution,
    spec: PackageStageSpec,
) -> None:
    if spec.artifact_url is None or spec.artifact_sha256 is None:
        raise StagingError(
            f"Released package {spec.distribution!r} is missing its artifact provenance."
        )
    raw_direct_url = distribution.read_text("direct_url.json")
    if raw_direct_url is None:
        raise StagingError(
            f"Installed distribution {spec.distribution!r} has no direct_url.json provenance."
        )
    try:
        direct_url = json.loads(raw_direct_url)
    except json.JSONDecodeError as exc:
        raise StagingError(
            f"Installed distribution {spec.distribution!r} has invalid direct_url.json."
        ) from exc
    if not isinstance(direct_url, dict) or direct_url.get("url") != spec.artifact_url:
        raise StagingError(
            f"Installed distribution {spec.distribution!r} did not come from the "
            "approved release URL."
        )
    archive_info = direct_url.get("archive_info")
    if not isinstance(archive_info, dict):
        raise StagingError(
            f"Installed distribution {spec.distribution!r} has invalid archive provenance."
        )
    recorded_hash = archive_info.get("hash")
    if recorded_hash is not None and recorded_hash != f"sha256={spec.artifact_sha256}":
        raise StagingError(
            f"Installed distribution {spec.distribution!r} reports a different artifact checksum."
        )


def _record_sha256(contents: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(contents).digest()).rstrip(b"=").decode()


def _verified_distribution_source_files(
    distribution: importlib.metadata.Distribution,
    spec: PackageStageSpec,
) -> tuple[Path, list[tuple[Path, bytes]]]:
    package_root_from_metadata = Path(distribution.locate_file(spec.import_name))
    if package_root_from_metadata.is_symlink():
        raise StagingError(
            f"Installed distribution {spec.distribution!r} package root must not be a symlink."
        )
    package_root_from_metadata = package_root_from_metadata.resolve()
    import_root = _installed_package_root(spec.import_name)
    if import_root != package_root_from_metadata:
        raise StagingError(
            f"Importable package {spec.import_name!r} does not match the installed "
            f"{spec.distribution!r} distribution root."
        )

    distribution_files = distribution.files
    if distribution_files is None:
        raise StagingError(f"Installed distribution {spec.distribution!r} has no RECORD file list.")

    verified: list[tuple[Path, bytes]] = []
    for record in distribution_files:
        record_path = Path(str(record))
        if (
            record_path.is_absolute()
            or ".." in record_path.parts
            or not record_path.parts
            or record_path.parts[0] != spec.import_name
        ):
            continue
        package_relative = Path(*record_path.parts[1:])
        if not package_relative.parts:
            raise StagingError(
                f"Installed distribution {spec.distribution!r} has an invalid package RECORD."
            )
        if record.hash is None or record.hash.mode != "sha256" or record.size is None:
            raise StagingError(
                f"Installed distribution {spec.distribution!r} has an incomplete RECORD "
                f"entry for {record_path.as_posix()!r}."
            )

        source_path = Path(distribution.locate_file(record))
        expected_path = package_root_from_metadata / package_relative
        if source_path.is_symlink() or source_path.resolve() != expected_path.resolve():
            raise StagingError(
                f"Installed distribution {spec.distribution!r} RECORD path "
                f"{record_path.as_posix()!r} escapes its package root."
            )
        if not source_path.is_file():
            raise StagingError(
                f"Installed distribution {spec.distribution!r} RECORD file "
                f"{record_path.as_posix()!r} is missing."
            )

        contents = source_path.read_bytes()
        if len(contents) != record.size:
            raise StagingError(
                f"Installed distribution {spec.distribution!r} file "
                f"{record_path.as_posix()!r} does not match its RECORD size."
            )
        if _record_sha256(contents) != record.hash.value:
            raise StagingError(
                f"Installed distribution {spec.distribution!r} file "
                f"{record_path.as_posix()!r} does not match its RECORD sha256."
            )
        verified.append((package_relative, contents))

    if not verified:
        raise StagingError(
            f"Installed distribution {spec.distribution!r} contains no recorded package files."
        )
    recorded_paths = {relative for relative, _ in verified}
    filesystem_paths = {
        path.relative_to(package_root_from_metadata)
        for path in _package_source_files(package_root_from_metadata)
    }
    if filesystem_paths != recorded_paths:
        raise StagingError(
            f"Installed package {spec.import_name!r} contains files not exactly listed in RECORD."
        )
    verified.sort(key=lambda item: item[0].as_posix())
    return package_root_from_metadata, verified


def _file_record(relative_path: str, contents: bytes) -> dict[str, str | int]:
    return {
        "path": relative_path,
        "bytes": len(contents),
        "sha256": hashlib.sha256(contents).hexdigest(),
    }


def _stage_package(
    spec: PackageStageSpec,
    temporary_root: Path,
    *,
    project_root: Path,
) -> dict[str, Any]:
    distribution = _installed_distribution(spec)
    if spec.role == "core":
        _verify_locked_artifact(spec, project_root=project_root)
        _verify_distribution_direct_url(distribution, spec)
        _, source_entries = _verified_distribution_source_files(distribution, spec)
    else:
        package_root = _installed_package_root(spec.import_name)
        expected_package_root = (project_root / "src" / spec.import_name).resolve()
        if package_root != expected_package_root:
            raise StagingError(
                f"App package {spec.import_name!r} must resolve to "
                f"{expected_package_root}, not {package_root}."
            )
        source_entries = [
            (source_path.relative_to(package_root), source_path.read_bytes())
            for source_path in _package_source_files(package_root)
        ]
    if not source_entries:
        raise StagingError(f"Installed package {spec.import_name!r} contains no stageable files.")

    records: list[dict[str, str | int]] = []
    for package_relative, contents in source_entries:
        bundle_relative = Path(spec.import_name, package_relative).as_posix()
        destination = temporary_root / bundle_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
        records.append(_file_record(bundle_relative, contents))

    records.sort(key=lambda record: str(record["path"]))
    return {
        "role": spec.role,
        "distribution": spec.distribution,
        "import_name": spec.import_name,
        "version": distribution.version,
        "files": records,
    }


def _bundle_sha256(packages: list[dict[str, Any]]) -> str:
    records = sorted(
        (record for package in packages for record in package["files"]),
        key=lambda record: str(record["path"]),
    )
    digest = hashlib.sha256()
    for record in records:
        digest.update((f"{record['path']}\0{record['sha256']}\0{record['bytes']}\n").encode())
    return digest.hexdigest()


def _replace_directory(temporary_root: Path, target_root: Path) -> None:
    backup_root = target_root.with_name(f".{target_root.name}-previous")
    if backup_root.exists():
        if backup_root.is_dir():
            shutil.rmtree(backup_root)
        else:
            backup_root.unlink()

    had_target = target_root.exists()
    if had_target:
        os.replace(target_root, backup_root)
    try:
        os.replace(temporary_root, target_root)
    except BaseException:
        if had_target and backup_root.exists() and not target_root.exists():
            os.replace(backup_root, target_root)
        raise
    if backup_root.exists():
        shutil.rmtree(backup_root)


def stage_browser_packages(
    target_root: Path,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Atomically stage installed app/core packages and a deterministic manifest."""

    resolved_target = target_root.resolve()
    resolved_project = project_root.resolve()
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_target.name}-stage-",
            dir=resolved_target.parent,
        )
    )
    try:
        packages = [
            _stage_package(
                spec,
                temporary_root,
                project_root=resolved_project,
            )
            for spec in PACKAGE_STAGE_SPECS
        ]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "pyodide_version": PYODIDE_VERSION,
            "source_commit": _source_commit(resolved_project),
            "bundle_sha256": _bundle_sha256(packages),
            "packages": packages,
        }
        manifest_text = json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        (temporary_root / MANIFEST_FILENAME).write_text(
            f"{manifest_text}\n",
            encoding="utf-8",
        )
        _replace_directory(temporary_root, resolved_target)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return manifest
