import { PYODIDE_INDEX_URL, PYTHON_PACKAGE_FILES } from "./config.js";

async function installLocalPythonPackage(pyodide) {
  pyodide.FS.mkdirTree("/home/pyodide/confcurve");

  for (const fileName of PYTHON_PACKAGE_FILES) {
    const response = await fetch(`./assets/py/confcurve/${fileName}`);
    if (!response.ok) {
      throw new Error(`Failed to load staged Python file: ${fileName}`);
    }
    const source = await response.text();
    pyodide.FS.writeFile(`/home/pyodide/confcurve/${fileName}`, source);
  }

  await pyodide.runPythonAsync(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);
}

export async function ensureRuntime(runtimeState, setStatus) {
  if (runtimeState.readyPromise) {
    return runtimeState.readyPromise;
  }

  runtimeState.readyPromise = (async () => {
    setStatus("loading", "Loading Pyodide, NumPy, and SciPy in the browser.");
    const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
    await pyodide.loadPackage(["numpy", "scipy"]);
    await installLocalPythonPackage(pyodide);
    await pyodide.runPythonAsync(`
import json
from confcurve import compute_curves

def compute_curves_json(payload_json):
    return json.dumps(compute_curves(json.loads(payload_json)))
`);
    runtimeState.pyodide = pyodide;
    runtimeState.computeCurvesJson = pyodide.globals.get("compute_curves_json");
    setStatus("ready", "Scientific runtime ready.");
    return runtimeState;
  })();

  return runtimeState.readyPromise;
}
