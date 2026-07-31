import {
  PYODIDE_INDEX_URL,
  PYODIDE_VERSION,
  PYTHON_MANIFEST_URL,
} from "./config.js";

const PYTHON_ROOT = "/home/pyodide";
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const SOURCE_COMMIT_PATTERN = /^[0-9a-f]{40}$/;
const SAFE_PATH_SEGMENT_PATTERN = /^[A-Za-z0-9._-]+$/;
const MANIFEST_KEYS = [
  "bundle_sha256",
  "packages",
  "pyodide_version",
  "schema_version",
  "source_commit",
];
const PACKAGE_KEYS = ["distribution", "files", "import_name", "role", "version"];
const FILE_KEYS = ["bytes", "path", "sha256"];
const EXPECTED_PACKAGES = [
  {
    role: "app",
    distribution: "confcurve",
    importName: "confcurve",
    version: "0.2.6",
  },
  {
    role: "core",
    distribution: "wald-inference",
    importName: "wald_inference",
    version: "0.4.2",
  },
];

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireExactKeys(value, expectedKeys, label) {
  if (!isRecord(value)) {
    throw new Error(`${label} must be an object.`);
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  if (
    actual.length !== expected.length ||
    actual.some((key, index) => key !== expected[index])
  ) {
    throw new Error(`${label} must contain exactly: ${expected.join(", ")}.`);
  }
}

function validatePackagePath(path, importName) {
  if (typeof path !== "string" || path.length === 0) {
    throw new Error("Manifest file path must be a non-empty string.");
  }
  const segments = path.split("/");
  if (
    path.startsWith("/") ||
    path.includes("\\") ||
    path.includes("?") ||
    path.includes("#") ||
    segments.some(
      (segment) =>
        segment.length === 0 ||
        segment === "." ||
        segment === ".." ||
        !SAFE_PATH_SEGMENT_PATTERN.test(segment),
    )
  ) {
    throw new Error(`Unsafe staged Python path: ${path}.`);
  }
  if (segments.length < 2 || segments[0] !== importName) {
    throw new Error(`Staged Python path must remain inside ${importName}/: ${path}.`);
  }
}

export function validatePythonManifest(manifest) {
  requireExactKeys(manifest, MANIFEST_KEYS, "Python manifest");
  if (manifest.schema_version !== 1) {
    throw new Error("Python manifest schema_version must be 1.");
  }
  if (manifest.pyodide_version !== PYODIDE_VERSION) {
    throw new Error(
      `Python manifest requires Pyodide ${manifest.pyodide_version}; expected ${PYODIDE_VERSION}.`,
    );
  }
  if (
    typeof manifest.source_commit !== "string" ||
    !SOURCE_COMMIT_PATTERN.test(manifest.source_commit)
  ) {
    throw new Error("Python manifest source_commit must be a lowercase 40-character hex SHA.");
  }
  if (
    typeof manifest.bundle_sha256 !== "string" ||
    !SHA256_PATTERN.test(manifest.bundle_sha256)
  ) {
    throw new Error("Python manifest bundle_sha256 must be a lowercase SHA-256 hex digest.");
  }
  if (
    !Array.isArray(manifest.packages) ||
    manifest.packages.length !== EXPECTED_PACKAGES.length
  ) {
    throw new Error("Python manifest must contain exactly the app and core packages.");
  }

  const seenPaths = new Set();
  EXPECTED_PACKAGES.forEach((expected, packageIndex) => {
    const packageRecord = manifest.packages[packageIndex];
    requireExactKeys(packageRecord, PACKAGE_KEYS, `Python package ${packageIndex}`);
    if (
      packageRecord.role !== expected.role ||
      packageRecord.distribution !== expected.distribution ||
      packageRecord.import_name !== expected.importName ||
      packageRecord.version !== expected.version
    ) {
      throw new Error(
        `Python package ${packageIndex} must be ${expected.role} ` +
          `${expected.distribution} ${expected.version} (${expected.importName}).`,
      );
    }
    if (!Array.isArray(packageRecord.files) || packageRecord.files.length === 0) {
      throw new Error(`${expected.distribution} must list at least one staged file.`);
    }

    packageRecord.files.forEach((fileRecord, fileIndex) => {
      requireExactKeys(
        fileRecord,
        FILE_KEYS,
        `${expected.distribution} file ${fileIndex}`,
      );
      validatePackagePath(fileRecord.path, expected.importName);
      if (seenPaths.has(fileRecord.path)) {
        throw new Error(`Duplicate staged Python path: ${fileRecord.path}.`);
      }
      seenPaths.add(fileRecord.path);
      if (typeof fileRecord.sha256 !== "string" || !SHA256_PATTERN.test(fileRecord.sha256)) {
        throw new Error(
          `Manifest SHA-256 for ${fileRecord.path} must be 64 lowercase hex characters.`,
        );
      }
      if (
        !Number.isSafeInteger(fileRecord.bytes) ||
        fileRecord.bytes < 0
      ) {
        throw new Error(`Manifest byte count for ${fileRecord.path} must be a nonnegative integer.`);
      }
    });
  });

  return manifest;
}

export function buildBundleDescriptor(fileRecords) {
  return [...fileRecords]
    .sort((left, right) => {
      if (left.path < right.path) {
        return -1;
      }
      if (left.path > right.path) {
        return 1;
      }
      return 0;
    })
    .map((fileRecord) => {
      return `${fileRecord.path}\0${fileRecord.sha256}\0${fileRecord.bytes}\n`;
    })
    .join("");
}

export async function sha256Hex(bytes, cryptoApi = globalThis.crypto) {
  if (!cryptoApi?.subtle) {
    throw new Error("Web Crypto SHA-256 is unavailable in this browser.");
  }
  const digest = await cryptoApi.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (value) => {
    return value.toString(16).padStart(2, "0");
  }).join("");
}

async function loadPythonManifest(fetchImplementation, baseUrl) {
  const manifestUrl = new URL(PYTHON_MANIFEST_URL, baseUrl);
  const response = await fetchImplementation(manifestUrl, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load Python manifest (${response.status}).`);
  }

  let manifest;
  try {
    manifest = await response.json();
  } catch {
    throw new Error("Python manifest is not valid JSON.");
  }
  return {
    manifest: validatePythonManifest(manifest),
    manifestUrl,
  };
}

export async function loadVerifiedPythonBundle(
  fetchImplementation = globalThis.fetch,
  baseUrl = document.baseURI,
) {
  const { manifest, manifestUrl } = await loadPythonManifest(fetchImplementation, baseUrl);
  const manifestFiles = manifest.packages.flatMap((packageRecord) => {
    return packageRecord.files;
  });

  const verifiedFiles = [];
  for (const fileRecord of manifestFiles) {
    const fileUrl = new URL(fileRecord.path, manifestUrl);
    fileUrl.searchParams.set("sha256", fileRecord.sha256);
    const response = await fetchImplementation(fileUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(
        `Failed to load staged Python file ${fileRecord.path} (${response.status}).`,
      );
    }

    const contents = new Uint8Array(await response.arrayBuffer());
    if (contents.byteLength !== fileRecord.bytes) {
      throw new Error(
        `Byte-count mismatch for staged Python file ${fileRecord.path}: ` +
          `expected ${fileRecord.bytes}, received ${contents.byteLength}.`,
      );
    }
    const actualSha256 = await sha256Hex(contents);
    if (actualSha256 !== fileRecord.sha256) {
      throw new Error(`SHA-256 mismatch for staged Python file ${fileRecord.path}.`);
    }
    verifiedFiles.push({
      path: fileRecord.path,
      sha256: actualSha256,
      bytes: contents.byteLength,
      contents,
    });
  }

  const bundleDescriptor = buildBundleDescriptor(verifiedFiles);
  const actualBundleSha256 = await sha256Hex(new TextEncoder().encode(bundleDescriptor));
  if (actualBundleSha256 !== manifest.bundle_sha256) {
    throw new Error(
      `Python bundle SHA-256 mismatch: expected ${manifest.bundle_sha256}, ` +
        `received ${actualBundleSha256}.`,
    );
  }

  return { manifest, files: verifiedFiles };
}

async function installVerifiedPythonFiles(pyodide, verifiedFiles) {
  for (const fileRecord of verifiedFiles) {
    const destination = `${PYTHON_ROOT}/${fileRecord.path}`;
    const parentDirectory = destination.slice(0, destination.lastIndexOf("/"));
    pyodide.FS.mkdirTree(parentDirectory);
    pyodide.FS.writeFile(destination, fileRecord.contents);
  }

  await pyodide.runPythonAsync(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);
}

async function verifyRuntimeVersions(pyodide, manifest) {
  const runtimeVersionsJson = await pyodide.runPythonAsync(`
import json
import confcurve
import wald_inference

json.dumps(
    {
        "app": confcurve.__version__,
        "core": wald_inference.__version__,
    },
    allow_nan=False,
)
`);
  const runtimeVersions = JSON.parse(runtimeVersionsJson);
  const appPackage = manifest.packages[0];
  const corePackage = manifest.packages[1];
  if (
    runtimeVersions.app !== appPackage.version ||
    runtimeVersions.core !== corePackage.version
  ) {
    throw new Error(
      `Imported Python versions do not match the verified manifest: ` +
        `app ${runtimeVersions.app}, core ${runtimeVersions.core}.`,
    );
  }
  return Object.freeze(runtimeVersions);
}

function showVerifiedVersions(manifest, runtimeVersions) {
  const versionElement = document.getElementById("technical-version");
  if (!versionElement) {
    return;
  }
  versionElement.textContent =
    `${manifest.packages[0].distribution} app ${runtimeVersions.app} · ` +
    `${manifest.packages[1].distribution} core ${runtimeVersions.core}`;
}

export async function ensureRuntime(runtimeState, setStatus) {
  if (runtimeState.readyPromise) {
    return runtimeState.readyPromise;
  }

  runtimeState.readyPromise = (async () => {
    setStatus("loading", "Verifying the staged Python runtime.");
    const verifiedBundle = await loadVerifiedPythonBundle();
    setStatus("loading", "Loading Pyodide, NumPy, and SciPy in the browser.");
    const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
    await pyodide.loadPackage(["numpy", "scipy"]);
    await installVerifiedPythonFiles(pyodide, verifiedBundle.files);
    const runtimeVersions = await verifyRuntimeVersions(pyodide, verifiedBundle.manifest);
    await pyodide.runPythonAsync(`
import json
from confcurve import compute_curves

def compute_curves_json(payload_json):
    return json.dumps(compute_curves(json.loads(payload_json)), allow_nan=False)
`);
    runtimeState.pyodide = pyodide;
    runtimeState.computeCurvesJson = pyodide.globals.get("compute_curves_json");
    runtimeState.packageManifest = verifiedBundle.manifest;
    runtimeState.versions = runtimeVersions;
    showVerifiedVersions(verifiedBundle.manifest, runtimeVersions);
    setStatus("ready", "Scientific runtime ready.");
    return runtimeState;
  })();

  return runtimeState.readyPromise;
}
