from __future__ import annotations

import json
from pathlib import Path

from confcurve.staging import MANIFEST_FILENAME, stage_browser_packages


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    target_root = project_root / "web" / "assets" / "py"
    manifest = stage_browser_packages(target_root, project_root=project_root)
    summary = {
        "manifest": str(target_root / MANIFEST_FILENAME),
        "source_commit": manifest["source_commit"],
        "bundle_sha256": manifest["bundle_sha256"],
        "packages": [
            {
                "distribution": package["distribution"],
                "version": package["version"],
                "files": len(package["files"]),
            }
            for package in manifest["packages"]
        ],
    }
    print(json.dumps(summary, allow_nan=False))


if __name__ == "__main__":
    main()
