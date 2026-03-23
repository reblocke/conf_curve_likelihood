from __future__ import annotations

from pathlib import Path
from shutil import copyfile

PACKAGE_FILES = [
    "__init__.py",
    "core.py",
    "models.py",
    "web_contract.py",
]


def package_root() -> Path:
    return Path(__file__).resolve().parent


def stage_web_python_package(target_dir: Path) -> list[Path]:
    """Copy the browser-consumed Python package into the staged web directory."""

    source_dir = package_root()
    target_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []
    for file_name in PACKAGE_FILES:
        source_path = source_dir / file_name
        target_path = target_dir / file_name
        copyfile(source_path, target_path)
        written_files.append(target_path)
    return written_files
