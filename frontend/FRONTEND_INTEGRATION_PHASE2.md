# NASA FLAME — Phase 2: Scientific Data Visualization Report
**Document ID:** `FRONTEND_INTEGRATION_PHASE2.md`  
**Author:** NASA FLAME Frontend Architecture & Scientific Data Visualization Team  
**Date:** November 14, 2026  
**Status:** Complete & Verified  
**Runtime Environment:** React 19 • Vite 8 • Tailwind CSS v4 • Python FastAPI (Port 8000)

---

## 1. Executive Summary

Phase 2 of the NASA FLAME intelligence platform has successfully delivered a high-performance, interactive **Scientific Data Visualization Workspace** integrated directly into the Live Dataset Explorer. 

Rather than relying on generic, third-party chart libraries with fragile React 19 dependencies, the visualization engine was constructed using a native React + SVG vector architecture. The implementation adheres strictly to microgravity combustion scientific integrity principles:
1. **Real Data Exclusivity:** All plotted points, timestamps, channels, and physical units are retrieved live from the 11 registered NASA microgravity combustion datasets via the FastAPI backend (`http://127.0.0.1:8000`). Zero mock, simulated, or fabricated measurement values are used.
2. **Discontinuity & Gap Preservation:** Sensor dropouts, blank values (`""`), and `null`/`NaN` readings split SVG line trajectories (`M ... L ...`) into disjoint segments. Missing data is never falsely interpolated with straight lines.
3. **Axis Compatibility Safeguard:** Unrelated sensor channels (e.g., Thermocouple Temperatures in `°C`, Fan Velocity in `RPM`, Chamber Pressure in `PSIA`) are prohibited from sharing a misleading single scale. The visualizer supports true **Dual Y-Axes** (Left and Right scales) for up to two compatible unit groups, and automatically surfaces scientific safeguard alerts if a researcher attempts to combine more than two incompatible physical dimensions.
4. **Experiment Matrix Specialization:** Discrete experiment-level test matrices (`bass_ii_experiments`) are **not** forced into artificial time-series plots. A dedicated multi-variable parameter comparison and gas consumption analysis workspace was constructed for BASS-II burn tests.
5. **High-Frequency Waveform Decimation:** For large sensor time series (such as Saffire-III with 20,909 records), server-side bounded pagination is combined with **Largest-Triangle-Three-Buckets (LTTB)** downsampling to preserve transient flame spikes and waveform dynamics while maintaining 60fps responsiveness.

All code passes strict linting (`oxlint` finished on 60 files with 0 warnings and 0 errors) and builds cleanly in Vite (`built in 264ms`).

---

## 2. Modified and New Files

| File Path | Status | Purpose |
| :--- | :--- | :--- |
| `frontend/src/features/dataset-explorer/utils/lttb.js` | **NEW** | Largest-Triangle-Three-Buckets (LTTB) downsampling algorithm with strict null/NaN discontinuity preservation. |
| `frontend/src/features/dataset-explorer/utils/channelUnits.js` | **NEW** | Scientific channel classifier, metadata unit resolver, physical dimension groups, and dual-axis compatibility evaluator. |
| `frontend/src/features/dataset-explorer/hooks/useVisualizationData.js` | **NEW** | React 19 hook managing server windowing, multi-channel selection state, unit compatibility, and data decimation. |
| `frontend/src/features/dataset-explorer/components/visualization/TimeSeriesChart.jsx` | **NEW** | Interactive SVG time-series chart with single/dual Y-axes, click-and-drag brush box zoom, hover crosshairs, real units, and summary statistics. |
| `frontend/src/features/dataset-explorer/components/visualization/ExperimentMatrixChart.jsx` | **NEW** | Dedicated non-time-series visualization for BASS-II 129 discrete test runs (initial vs final O₂ consumption, CO₂ evolution, CO generation, and material filters). |
| `frontend/src/features/dataset-explorer/components/visualization/ChannelSelector.jsx` | **NEW** | Categorized channel selector chips with unit tags, group selection presets, and real-time axis compatibility warnings. |
| `frontend/src/features/dataset-explorer/components/visualization/DataWindowControls.jsx` | **NEW** | Server-side window controls for large datasets (offset navigation, batch size selector, jump to start/end, and downsample toggle). |
| `frontend/src/features/dataset-explorer/components/visualization/DataVisualizerWorkspace.jsx` | **NEW** | Master visualization coordinator switching between Time-Series and Experiment Matrix modes with provenance badges. |
| `frontend/src/features/dataset-explorer/index.jsx` | **MODIFIED** | Added high-visibility view switcher between `[📈 Visualize Data (Interactive Workspace)]` and `[📋 Records Table]`. |
| `frontend/src/services/flameApi.js` | **MODIFIED** | Added `fetchRecordRange()` for multi-batch window querying and refined `API_BASE` for Vite dev proxy consistency. |

---

## 3. Dataset & Channel Mappings

The 11 registered NASA datasets were mapped to appropriate visualization modes, time axes, and physical unit groups:

### 3.1 Saffire Calibrated Sensor Series (Continuous Time-Series Mode)
- **Datasets:** `saffire_iii_sample_1` (20,909 rows), `saffire_iii_sample_2` (4,848 rows), `saffire_sample_5` (11,363 rows), `saffire_sample_6` (11,363 rows), `saffire_sample_7` (9,710 rows), `saffire_sample_8` (10,839 rows).
- **Time Axis:** `Elapsed Time (s)` (monotonic experimental time in seconds).
- **Physical Channel Groups & Units:**
  - **Temperature (`°C`):** Plume Thermocouples `Plume Temp 1-6 (TC1-TC6)`, Sample Thermocouples `Sample Temp 1-6 (TC7-TC12)`, Radiometer Body Temps `Radiometer Temp 1-4`, `Test Section Inlet Temp`.
  - **Radiant Heat Flux (`mw/cm²`):** `Radiometer 1`, `Radiometer 2`, `Radiometer 3`, `Radiometer 4`.
  - **Chamber Pressure (`PSIA`):** `Ambient Pressure`.
  - **Flow Velocity (`cm/sec`):** `Anemometer 1`, `Anemometer 2`.
  - **Ventilation Speed (`RPM`):** `Average Fan Speed`.
  - **Gas Concentration (`%`):** `O2`, `CO2`, `Humidity`.
  - **Electrical Signals (`V`, `A`):** `Igniter Voltage`, `Igniter Current`, `Avionics 24V`, `PC104 5V`.

### 3.2 Cygnus Spacecraft Telemetry (Continuous Time-Series Mode)
- **Datasets:**
  - `telemetry_cygnus_smoke_detector_data` (3,844 rows): `Relative Time (s)` vs `FIZ 2 Smoke Detector Obscuration (V)` and `Scatterometer (V)`.
  - `telemetry_cygnus_pressure_data` (3,844 rows): `Relative Time (s)` vs `PCM EPS 1 Press (psi)`, `PCM EPS 2 Press (psi)`, `PCM EPS 3 Press (psi)`.
  - `telemetry_cygnus_temperature_data` (3,844 rows): `Relative Time (s)` vs `PCM Air Temp (degC)`.
  - `telemetry_saffire_data` (47 rows): `Relative Time (s)` vs Radiometers, Anemometers, Fan Tachometer, Smoke Wire, and Igniter voltages.
- **Time Axis:** `Relative Time (s)`. Note: Telemetry datasets feature non-zero start offsets and minor backward step screenings documented in metadata notes.

### 3.3 BASS-II Microgravity Glovebox Experiments (Discrete Matrix Mode)
- **Dataset:** `bass_ii_experiments` (129 rows).
- **Granularity:** `experiment` (non-continuous discrete test runs).
- **X-Axis:** `Test no.` (B1 through B129).
- **Material Filter:** Grouping by solid fuel substrate (`100 micron PMMA film`, `Nomex`, `Cotton`, `Cast PMMA`, etc.).
- **Parameters Compared:**
  - Initial vs. Final Oxygen Concentration (`calibrated initial O2 % by vol` vs `calibrated final O2 % by vol`).
  - CO₂ Evolution (`Initial CO2 % by vol` vs `Final CO2 % by vol`).
  - Carbon Monoxide Generation (`Initial CO (ppm)` vs `Final CO (ppm)`).
  - Video Frames (`total frames shot`).

---

## 4. Data Loading, Bounding & Downsampling Strategy

Microgravity sensor streams contain tens of thousands of data points at high sampling frequencies. To prevent browser memory exhaustion, DOM bloat, or UI freezing:

1. **Server-Side Range Queries (`fetchRecordRange`):**
   - The FastAPI backend imposes a hard limit of `limit <= 1000` per request.
   - `flameApi.fetchRecordRange` was implemented to query consecutive 1,000-record batches when extended windows are requested (e.g. 2,000 or 3,000 points), assembling them into a single continuous buffer.
2. **Time Window Controls (`DataWindowControls`):**
   - Researchers can navigate windows across the dataset: `Start (0 - 1,000)`, `Prev Window`, `Next Window`, and `End (Total - 1,000)`.
   - Window sizes are configurable: 500, 1,000, 2,000, or 3,000 points.
3. **Largest-Triangle-Three-Buckets (LTTB) Decimation:**
   - Standard linear decimation (picking every $N$-th point) risks skipping narrow ignition spikes, flame extinction thresholds, and peak temperatures.
   - LTTB splits the series into equal buckets and retains the point in each bucket that maximizes the triangular area formed with adjacent points, strictly preserving visual peaks and valleys.
   - **Discontinuity-Aware LTTB:** When null values or gaps are encountered, `downsampleTimeSeries` splits data into continuous valid runs, decimate each run proportionally, and re-inserts the null gap markers.

---

## 5. Scientific Validation Safeguards

To prevent misinterpretation of experimental combustion results:
1. **Zero False Interpolation:** SVG paths are split into subpaths on `null`, `""`, or `NaN` values. Missing sensor readings appear as visible gaps rather than artificial linear trends.
2. **Dual-Axis Physical Dimension Restriction:**
   - Single Unit selected $\rightarrow$ 1 Y-Axis (e.g. `[°C]`).
   - Two Units selected $\rightarrow$ 2 Y-Axes (Left Axis = `[°C]`, Right Axis = `[mw/cm²]`).
   - Three or more Units selected $\rightarrow$ The chart blocks combining them on one plot and displays a warning:
     > *"Physical Unit Conflict: Selected channels span X incompatible units ([°C], [mw/cm²], [PSIA]). Unrelated physical quantities cannot be plotted on a single chart without misleading axis distortion. Please deselect incompatible channels to maintain scientific rigor."*
3. **Provenance & Verification Flags:**
   - Provenance badges clearly display `Validation: pending review` and `Discontinuities Preserved (Zero Interpolation)`.
   - Source Excel worksheet and row references are preserved.

---

## 6. Interactive Features Implemented

1. **Click-and-Drag Brush Box Zoom:**
   - Researchers can click and drag across any time interval on the chart canvas.
   - The time window instantly zooms to the selected range.
   - A `Reset Zoom` button restores the active window bounds.
2. **Precision Crosshair Cursor & Hover Tooltip:**
   - A vertical tracking crosshair displays exact time down to milliseconds (`t = 124.500 s`).
   - Tooltip details each selected channel's exact floating-point value and physical unit.
   - Highlighting circles mark the exact sensor coordinates on active curves.
3. **Telemetry Summary Statistics:**
   - Below the chart canvas, a live summary table computes `Min`, `Max`, `Mean`, `Valid Readings`, and `Data Gaps` for every selected channel in the active window.
4. **Interactive Channel Legend:**
   - Clicking any channel badge in the legend toggles its visibility without removing it from the selection.

---

## 7. Verification & Testing Results

| Test Category | Command / Action | Result | Verification Notes |
| :--- | :--- | :--- | :--- |
| **Linting Check** | `npm run lint` (`oxlint`) | **PASSED (0 warnings, 0 errors)** | Checked all 60 project files. Resolved React 19 `react(set-state-in-effect)` by deriving channel selections during render. |
| **Production Build** | `npm run build` (`vite build`) | **PASSED (264ms)** | Clean production bundle generated (`dist/assets/index-CVn6Gc6-.js` 433 kB, gzip: 112 kB). |
| **LTTB Gap Preservation** | Node.js unit verification | **PASSED** | Verified that LTTB algorithm retains null boundaries and gap count without dropping missing intervals. |
| **Unit Categorization** | Node.js unit verification | **PASSED** | Verified correct assignment of `°C`, `mw/cm²`, `psi`, `RPM`, `%`, and `V`. Dual-axis and triple-axis conflict detection confirmed. |
| **FastAPI Connectivity** | `GET http://localhost:5173/api/health` | **PASSED (200 OK)** | Vite dev proxy forwarded health check to FastAPI backend; returned 11 datasets, validation pending. |
| **Saffire III Time Series** | `GET /api/datasets/saffire_iii_sample_1/records?limit=5` | **PASSED (200 OK)** | Confirmed 20,909 records accessible via paginated windowing. |
| **BASS-II Matrix Data** | `GET /api/datasets/bass_ii_experiments/records?limit=5` | **PASSED (200 OK)** | Confirmed 129 discrete test runs with fuel materials, flow restrictor, initial and final O₂/CO₂/CO values. |

---

## 8. Remaining Considerations & Next Steps

1. **Export Capabilities:** Add 1-click export of the active zoomed time window to CSV or high-resolution vector SVG for scientific publication figures.
2. **Multi-Run Overlay:** Allow side-by-side comparison of two distinct Saffire samples (e.g. Saffire III Sample 1 vs Sample 2) on synchronized relative ignition timelines.
3. **Scientific Quality Reports:** Integrate the backend quality reports (`quality_report` JSON/CSV) to annotate known sensor saturation or ignition failure intervals directly on the timeline.
