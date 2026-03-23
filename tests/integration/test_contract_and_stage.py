from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from confcurve.stage import PACKAGE_FILES, package_root, stage_web_python_package


def test_stage_web_python_package_copies_source_files(tmp_path: Path) -> None:
    written = stage_web_python_package(tmp_path)

    assert [path.name for path in written] == PACKAGE_FILES

    source_dir = package_root()
    for file_name in PACKAGE_FILES:
        assert (tmp_path / file_name).read_text(encoding="utf-8") == (
            source_dir / file_name
        ).read_text(encoding="utf-8")


def test_committed_staged_python_package_matches_source() -> None:
    source_dir = package_root()
    staged_dir = Path("web") / "assets" / "py" / "confcurve"

    for file_name in PACKAGE_FILES:
        assert (staged_dir / file_name).read_text(encoding="utf-8") == (
            source_dir / file_name
        ).read_text(encoding="utf-8")


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
