from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, Route, expect

pytestmark = pytest.mark.e2e

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "web" / "assets" / "py" / "manifest.json"


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _synthetic_manifest() -> tuple[dict[str, object], dict[str, str]]:
    contents_by_path = {
        "confcurve/__init__.py": 'APP_VERSION = "0.2.3"\n',
        "wald_inference/__init__.py": 'CORE_VERSION = "0.4.1"\n',
    }
    records = {
        path: {
            "path": path,
            "sha256": hashlib.sha256(contents.encode()).hexdigest(),
            "bytes": len(contents.encode()),
        }
        for path, contents in contents_by_path.items()
    }
    descriptor = "".join(
        f"{record['path']}\0{record['sha256']}\0{record['bytes']}\n"
        for record in sorted(records.values(), key=lambda record: record["path"])
    )
    manifest = {
        "schema_version": 1,
        "pyodide_version": "0.29.3",
        "source_commit": "a" * 40,
        "bundle_sha256": hashlib.sha256(descriptor.encode()).hexdigest(),
        "packages": [
            {
                "role": "app",
                "distribution": "confcurve",
                "import_name": "confcurve",
                "version": "0.2.3",
                "files": [records["confcurve/__init__.py"]],
            },
            {
                "role": "core",
                "distribution": "wald-inference",
                "import_name": "wald_inference",
                "version": "0.4.1",
                "files": [records["wald_inference/__init__.py"]],
            },
        ],
    }
    return manifest, contents_by_path


def _browser_validation_error(
    app_url: str,
    page: Page,
    manifest: dict[str, object],
) -> str | None:
    page.goto(f"{app_url}/assets/config.js")
    return page.evaluate(
        """
        async ({moduleUrl, manifest}) => {
          const runtime = await import(moduleUrl);
          try {
            runtime.validatePythonManifest(manifest);
            return null;
          } catch (error) {
            return error instanceof Error ? error.message : String(error);
          }
        }
        """,
        {
            "moduleUrl": f"{app_url}/assets/runtime.js?validation-test=1",
            "manifest": manifest,
        },
    )


def test_manifest_validation_rejects_incomplete_unsafe_and_invalid_records(
    app_url: str,
    page: Page,
) -> None:
    valid_manifest = {
        "schema_version": 1,
        "pyodide_version": "0.29.3",
        "source_commit": "a" * 40,
        "bundle_sha256": "b" * 64,
        "packages": [
            {
                "role": "app",
                "distribution": "confcurve",
                "import_name": "confcurve",
                "version": "0.2.3",
                "files": [
                    {
                        "path": "confcurve/__init__.py",
                        "sha256": "c" * 64,
                        "bytes": 1,
                    }
                ],
            },
            {
                "role": "core",
                "distribution": "wald-inference",
                "import_name": "wald_inference",
                "version": "0.4.1",
                "files": [
                    {
                        "path": "wald_inference/__init__.py",
                        "sha256": "d" * 64,
                        "bytes": 1,
                    }
                ],
            },
        ],
    }

    cases: list[tuple[str, dict[str, object], str]] = []

    incomplete = copy.deepcopy(valid_manifest)
    incomplete["packages"] = incomplete["packages"][:1]  # type: ignore[index]
    cases.append(("incomplete", incomplete, "exactly the app and core"))

    unsafe_path = copy.deepcopy(valid_manifest)
    unsafe_path["packages"][0]["files"][0]["path"] = "../escape.py"  # type: ignore[index]
    cases.append(("unsafe path", unsafe_path, "Unsafe staged Python path"))

    duplicate_path = copy.deepcopy(valid_manifest)
    duplicate_path["packages"][1]["files"][0]["path"] = "confcurve/__init__.py"  # type: ignore[index]
    duplicate_path["packages"][1]["import_name"] = "confcurve"  # type: ignore[index]
    cases.append(("wrong package metadata", duplicate_path, "must be core wald-inference"))

    duplicate_within_package = copy.deepcopy(valid_manifest)
    duplicate_within_package["packages"][0]["files"].append(  # type: ignore[index]
        copy.deepcopy(duplicate_within_package["packages"][0]["files"][0])  # type: ignore[index]
    )
    cases.append(("duplicate path", duplicate_within_package, "Duplicate staged Python path"))

    invalid_hash = copy.deepcopy(valid_manifest)
    invalid_hash["packages"][0]["files"][0]["sha256"] = "C" * 64  # type: ignore[index]
    cases.append(("invalid hash", invalid_hash, "64 lowercase hex characters"))

    invalid_bytes = copy.deepcopy(valid_manifest)
    invalid_bytes["packages"][0]["files"][0]["bytes"] = -1  # type: ignore[index]
    cases.append(("invalid bytes", invalid_bytes, "nonnegative integer"))

    for label, manifest, expected_message in cases:
        error = _browser_validation_error(app_url, page, manifest)
        assert error is not None, label
        assert expected_message in error, (label, error)


def test_bundle_loader_uses_no_store_and_digest_addressed_file_urls(
    app_url: str,
    page: Page,
) -> None:
    manifest, contents_by_path = _synthetic_manifest()
    page.goto(f"{app_url}/assets/config.js")
    result = page.evaluate(
        """
        async ({moduleUrl, manifest, contentsByPath}) => {
          const runtime = await import(moduleUrl);
          const requests = [];
          let activeFileFetches = 0;
          let maximumActiveFileFetches = 0;
          const fakeFetch = async (input, options) => {
            const url = new URL(String(input));
            requests.push({
              path: url.pathname,
              sha256: url.searchParams.get("sha256"),
              cache: options?.cache ?? null,
            });
            if (url.pathname.endsWith("/manifest.json")) {
              return new Response(JSON.stringify(manifest), {
                status: 200,
                headers: {"Content-Type": "application/json"},
              });
            }
            activeFileFetches += 1;
            maximumActiveFileFetches = Math.max(
              maximumActiveFileFetches,
              activeFileFetches,
            );
            await new Promise((resolve) => window.setTimeout(resolve, 5));
            activeFileFetches -= 1;
            const marker = "/assets/py/";
            const path = url.pathname.split(marker, 2)[1];
            return new Response(new TextEncoder().encode(contentsByPath[path]), {
              status: 200,
            });
          };
          const bundle = await runtime.loadVerifiedPythonBundle(
            fakeFetch,
            "https://example.test/workbench/index.html",
          );
          return {
            requests,
            paths: bundle.files.map((fileRecord) => fileRecord.path),
            bundleSha256: bundle.manifest.bundle_sha256,
            maximumActiveFileFetches,
          };
        }
        """,
        {
            "moduleUrl": f"{app_url}/assets/runtime.js?bundle-loader-test=1",
            "manifest": manifest,
            "contentsByPath": contents_by_path,
        },
    )

    assert result["bundleSha256"] == manifest["bundle_sha256"]
    assert result["paths"] == list(contents_by_path)
    assert result["maximumActiveFileFetches"] == 1
    assert all(request["cache"] == "no-store" for request in result["requests"])
    assert result["requests"][0]["path"].endswith("/assets/py/manifest.json")
    assert [
        request["path"].split("/assets/py/", maxsplit=1)[1] for request in result["requests"][1:]
    ] == list(contents_by_path)
    requested_files = {
        request["path"].split("/assets/py/", maxsplit=1)[1]: request["sha256"]
        for request in result["requests"][1:]
    }
    expected_digests = {
        file_record["path"]: file_record["sha256"]
        for package_record in manifest["packages"]
        for file_record in package_record["files"]
    }
    assert requested_files == expected_digests


def test_runtime_requests_every_manifest_file_by_digest_and_shows_verified_versions(
    app_url: str,
    page: Page,
) -> None:
    manifest = _manifest()
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))

    page.goto(app_url)
    expect(page.locator("#status-card")).to_contain_text("Curves updated", timeout=120000)

    expected_files = [
        file_record
        for package_record in manifest["packages"]
        for file_record in package_record["files"]
    ]
    requested_files: dict[str, list[str]] = {}
    for request_url in requests:
        parsed = urlparse(request_url)
        marker = "/assets/py/"
        if marker not in parsed.path or parsed.path.endswith("/manifest.json"):
            continue
        relative_path = parsed.path.split(marker, maxsplit=1)[1]
        requested_files[relative_path] = parse_qs(parsed.query).get("sha256", [])

    assert set(requested_files) == {file_record["path"] for file_record in expected_files}
    for file_record in expected_files:
        assert requested_files[file_record["path"]] == [file_record["sha256"]]

    expect(page.locator("#technical-version")).to_have_text(
        "confcurve app 0.2.3 · wald-inference core 0.4.1"
    )


def test_runtime_rejects_corrupted_file_before_import(
    app_url: str,
    page: Page,
) -> None:
    manifest = _manifest()
    target = manifest["packages"][-1]["files"][-1]

    def corrupt_staged_file(route: Route) -> None:
        upstream = route.fetch()
        corrupted = bytearray(upstream.body())
        corrupted[0] ^= 1
        route.fulfill(response=upstream, body=bytes(corrupted))

    page.route(
        f"**/assets/py/{target['path']}?sha256=*",
        corrupt_staged_file,
    )

    page.goto(app_url)

    expect(page.locator("#status-card")).to_contain_text(
        f"mismatch for staged Python file {target['path']}",
        timeout=120000,
    )
    expect(page.locator("#technical-version")).to_have_text(
        "Runtime versions pending verification."
    )
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)


def test_runtime_rejects_invalid_aggregate_before_import(
    app_url: str,
    page: Page,
) -> None:
    manifest = _manifest()
    manifest["bundle_sha256"] = "0" * 64
    page.route(
        "**/assets/py/manifest.json",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(manifest),
        ),
    )

    page.goto(app_url)

    expect(page.locator("#status-card")).to_contain_text(
        "Python bundle SHA-256 mismatch",
        timeout=120000,
    )
    expect(page.locator("#technical-version")).to_have_text(
        "Runtime versions pending verification."
    )
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)
