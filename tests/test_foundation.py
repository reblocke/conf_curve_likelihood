from __future__ import annotations

from pathlib import Path


def test_web_shell_exists() -> None:
    assert (Path("web") / "index.html").exists()


def test_package_root_exists() -> None:
    assert (Path("src") / "confcurve" / "__init__.py").exists()
