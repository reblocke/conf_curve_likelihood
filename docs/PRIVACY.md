# Privacy

The integrated workbench runs its calculations in the browser. It has no application backend,
account system, telemetry, analytics, advertising, or tracking pixel.

## Input and state boundary

- Entered numerical values remain in browser memory and are not added to the URL.
- The app does not use local storage, session storage, IndexedDB, cookies, or a service worker.
- Exports occur only after an explicit user action and are created locally as downloads or
  clipboard text.
- The app neither requires nor is designed for patient-level data or protected health information.
  Use synthetic or publication-level values.

## Network boundary

The initial static app and staged Python packages are served from GitHub Pages. Pyodide, NumPy,
SciPy, and Plotly static runtime assets are fetched from the documented CDNs. Entered numerical
values are not included in those requests or transmitted to an application server.

Any future backend, persistence, telemetry, input-bearing URL, external export, or new network
destination requires an explicit privacy/data-flow decision and updated tests before adoption.

Public issue and pull-request reports must use synthetic values and omit credentials, sensitive
data, private study materials, and protected health information. Vulnerability details use the
private process in `SECURITY.md`, not public coordination surfaces.
