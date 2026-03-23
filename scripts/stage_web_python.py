from __future__ import annotations

from pathlib import Path

from confcurve.stage import stage_web_python_package


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    target_dir = project_root / "web" / "assets" / "py" / "confcurve"
    stage_web_python_package(target_dir=target_dir)


if __name__ == "__main__":
    main()
