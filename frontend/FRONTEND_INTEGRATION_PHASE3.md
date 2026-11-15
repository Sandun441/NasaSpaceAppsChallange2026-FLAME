# NASA FLAME — Phase 3: Scientific Experiment Comparison Report
**Document ID:** `FRONTEND_INTEGRATION_PHASE3.md`  
**Author:** NASA FLAME Frontend Architecture & Scientific Data Visualization Team  
**Date:** November 14, 2026  
**Status:** Complete & Fully Verified  
**Runtime Environment:** React 19 • Vite 8 • Tailwind CSS v4 • Python FastAPI (Port 8000)

---

## 1. Executive Summary

Phase 3 of the **NASA FLAME** microgravity combustion intelligence platform has delivered the **Scientific Experiment Comparison Workspace**, accessible via the primary navigation as `"Experiment Comparison"`. 

The workspace empowers researchers to perform rigorous empirical comparisons between compatible NASA microgravity combustion experiments. Rather than treating all datasets as generic time-series, the engine evaluates physical dimensions, sensor compatibility, and experimental structure:
1. **Saffire Continuous Sensor Comparison:** Compares high-frequency flight sensor suites across Saffire flight samples (e.g. Saffire-III Sample 1 vs Sample 2, Sample 5, Sample 6), evaluating 61 shared measurement channels (thermocouples, radiometers, anemometers, pressure, fan speed, gas concentrations).
2. **Three Rigorous Time-Alignment Modes:**
   - **Side-by-Side Independent Timelines:** Displays independent synchronized SVG viewports with individual time coordinates and window controls.
   - **Absolute Recorded Time Overlay:** Overlays measurements using identical experimental clock timestamps ($t_{rec} = 0\text{ s}$).
   - **Verified Event-Aligned Overlay ($t_0 = \text{Ignition}$):** Shifts time axes so $t' = 0$ corresponds to documented ignition onset. **Strict scientific safeguard:** This mode is enabled *only* when physical igniter telemetry (e.g. `Igniter Current > 0.5A`) confirms the exact moment of ignition in both datasets. First recorded data points are *never* assumed to be ignition.
3. **BASS-II Discrete Experiment Comparison:** Discrete Glovebox test runs (`bass_ii_experiments`, 129 tests) are compared separately via a dedicated matrix interface, contrasting solid fuel materials (PMMA, Cotton, Nomex), flow restrictors, initial vs final oxygen concentrations, CO₂ evolution, and CO generation.
4. **Descriptive Empirical Statistics:** Directly observed numerical differences, peak maximum deltas, time-to-peak offsets, arithmetic means, start-to-end changes, and sensor missing-value counts are computed over the loaded data buffer without downsampling bias.
5. **Categorized Scientific Findings Panel:** Explicitly separates observed numerical deltas, statistical aggregates, microgravity combustion physics context, and strict data limitations/safeguards (correlation $\ne$ causation; sensor traces alone do not constitute a flammability safety rating).

All code passes `oxlint` (71 files checked, 0 warnings, 0 errors) and builds cleanly with Vite in 242ms.

---

## 2. Modified and New Files

| File Path | Status | Purpose |
| :--- | :--- | :--- |
| `frontend/src/features/experiment-comparison/utils/comparisonMath.js` | **NEW** | Ignition event detection ($t_{ign}$), descriptive statistics calculations, cross-dataset channel matching, and empirical delta metrics. |
| `frontend/src/features/experiment-comparison/hooks/useExperimentComparison.js` | **NEW** | React 19 hook managing dual-dataset loading, shared channel states, window offsets, alignment modes, and downsampling. |
| `frontend/src/features/experiment-comparison/components/ComparisonDatasetSelector.jsx` | **NEW** | Dataset A and Dataset B selectors with cross-investigation compatibility validation and quick-swap controls. |
| `frontend/src/features/experiment-comparison/components/ChannelMatcher.jsx` | **NEW** | Categorized shared channel chips with physical unit badges, compatibility indicators, and 1-click channel selection. |
| `frontend/src/features/experiment-comparison/components/ComparisonToolbar.jsx` | **NEW** | Alignment mode switcher (Side-by-Side, Absolute Overlay, Event-Aligned), window limits, and downsampling toggles. |
| `frontend/src/features/experiment-comparison/components/SideBySideView.jsx` | **NEW** | Side-by-side interactive SVG charts with independent time axes, window navigation, and crosshair tracking. |
| `frontend/src/features/experiment-comparison/components/OverlayComparisonChart.jsx` | **NEW** | Overlaid dual-curve chart with relative/recorded time axis, brush box zoom, dual-tracking crosshair tooltip, and instantaneous delta readout. |
| `frontend/src/features/experiment-comparison/components/ComparisonStatsTable.jsx` | **NEW** | Side-by-side statistical summary table showing Max, Min, Mean, Time of Peak, Net Change, and Missing Data Gaps. |
| `frontend/src/features/experiment-comparison/components/ScientificFindingsPanel.jsx` | **NEW** | Structured findings panel dividing directly observed deltas, calculated statistics, physical context, and NASA FLAME safeguards. |
| `frontend/src/features/experiment-comparison/components/BassComparisonView.jsx` | **NEW** | Dedicated discrete comparison workspace for BASS-II Glovebox test runs (fuel substrate, airflow restrictor, gas consumption deltas). |
| `frontend/src/features/experiment-comparison/index.jsx` | **NEW** | Master Experiment Comparison Workspace coordinating data flow and mode switching. |
| `frontend/src/lib/constants.js` | **MODIFIED** | Added `{ id: 'experiment-comparison', label: 'Experiment Comparison' }` to primary navigation links. |
| `frontend/src/app/App.jsx` | **MODIFIED** | Added `ExperimentComparison` import, registered in `knownTabs`, and rendered in active view switch. |
| `frontend/src/components/layout/MenuDrawer.jsx` | **MODIFIED** | Added navigation entry for Experiment Comparison in the system drawer menu. |

---

## 3. Supported Comparison Datasets & Compatibility Rules

The comparison engine enforces strict physical dimension and structural rules:

```
                               ┌───────────────────────────────────────────────┐
                               │           Experiment Comparison Mode          │
                               └──────────────────────┬────────────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
         Continuous Time-Series Mode                                   Discrete Matrix Mode
    (Saffire Sensor & Cygnus Telemetry)                             (BASS-II Glovebox Tests)
                       │                                                             │
        ┌──────────────┴──────────────┐                                ┌─────────────┴─────────────┐
        ▼                             ▼                                ▼                           ▼
Saffire Pairs                 Cygnus Pairs                       Test Run A                   Test Run B
(61 Shared Channels:          (Vehicle Engineering Telemetry:    (e.g. Test B1 - PMMA)        (e.g. Test B2 - PMMA)
 °C, mw/cm², cm/s, PSIA, %)    Relative Time, Pressure, V)        O₂, CO₂, CO, Restrictor      O₂, CO₂, CO, Restrictor
```

### 3.1 Saffire Flight Sensor Pairs (High Compatibility)
- **Datasets:** `saffire_iii_sample_1` (20,909 rows), `saffire_iii_sample_2` (4,848 rows), `saffire_sample_5` (11,363 rows), `saffire_sample_6` (11,363 rows).
- **Physical Shared Channels (61 matched channels):**
  - **Plume Temperatures:** `Plume Temp 1-6 (TC1-TC6)` in `°C`
  - **Sample Surface Temperatures:** `Sample Temp 1-6 (TC7-TC12)` in `°C`
  - **Radiometer Body Temperatures:** `Radiometer Temp 1-4` in `°C`
  - **Radiant Heat Flux:** `Radiometer 1-4` in `mw/cm²`
  - **Flow Velocity:** `Anemometer 1-2` in `cm/sec`
  - **Ventilation Velocity:** `Average Fan Speed` in `RPM`
  - **Chamber Pressure:** `Ambient Pressure` in `PSIA`
  - **Atmospheric Gas Concentrations:** `O2` in `%`, `CO2` in `%`, `Humidity` in `%`
  - **Electrical Channels:** `Igniter Voltage` in `V`, `Igniter Current` in `A`, `Avionics 24V`, `PC104 5V`
- **Supported Alignment Modes:** Side-by-Side, Recorded Time Overlay, Event-Aligned Overlay ($t_0 = \text{Ignition}$).

### 3.2 Cygnus Spacecraft Telemetry Pairs (Telemetry Suite Mode)
- **Datasets:** `telemetry_cygnus_smoke_detector_data` (3,844 rows), `telemetry_cygnus_pressure_data` (3,844 rows), `telemetry_cygnus_temperature_data` (3,844 rows).
- **Time Axis:** `Relative Time (s)`.
- **Supported Alignment Modes:** Side-by-Side, Recorded Time Overlay. (Event-aligned mode is automatically disabled because Cygnus vehicle engineering telemetry did not record igniter trigger events).

### 3.3 BASS-II Discrete Glovebox Runs (Discrete Matrix Mode)
- **Dataset:** `bass_ii_experiments` (129 rows).
- **Structure:** Non-time-series discrete test matrix.
- **Comparison Parameters:** Solid fuel substrate (PMMA film thickness, Cotton, Nomex), flow restrictor index (1, 2, 3), initial and final O₂ % by vol, net O₂ consumed, CO₂ evolution, CO generation (ppm), and high-speed video frames shot.

---

## 4. Data Alignment Methodology

NASA FLAME implements three distinct time-alignment strategies:

### 4.1 Side-by-Side Independent Timelines
- Renders Dataset A and Dataset B in isolated, parallel viewports.
- Each dataset preserves its native recorded time coordinates $t_A$ and $t_B$.
- Features independent window navigation controls (`Prev Window` / `Next Window`) so researchers can inspect different experimental phases simultaneously (e.g. pre-ignition baseline on Sample 1 while viewing peak steady-state flame propagation on Sample 2).

### 4.2 Absolute Recorded Time Overlay
- Projects both datasets onto a shared time axis starting at experimental clock $t = 0\text{ s}$.
- Preserves the chronological offset between tests as recorded by the ground data acquisition system.

### 4.3 Verified Event-Aligned Overlay ($t_0 = \text{Ignition}$)
- **The Problem:** In NASA Saffire tests, data acquisition begins during pre-test calibration. In Saffire-III Sample 1, pre-test baseline lasted ~66 seconds before ignition, whereas in Sample 2, ignition occurred at ~60 seconds. Directly overlaying them at $t=0\text{ s}$ misaligns the ignition pulse by 6.0 seconds.
- **Scientific Solution:**
  1. `detectIgnitionTimestamp` parses physical igniter telemetry (`Igniter Current > 0.5 A` or `Igniter Power Enable == 1`).
  2. For Saffire-III Sample 1: $t_{ign, A} = 66.00\text{ s}$.
  3. For Saffire-III Sample 2: $t_{ign, B} = 60.03\text{ s}$.
  4. Time axes are shifted:
     $$t'_A = t_A - t_{ign, A}, \quad t'_B = t_B - t_{ign, B}$$
  5. The chart displays a prominent green vertical marker at $t' = 0\text{ s}$ representing the exact moment of igniter energization, enabling researchers to compare flame growth rates ($dT/dt$), steady-state durations, and extinction times on an identical physical basis.
- **Strict Rule:** If either dataset lacks documented ignition telemetry (e.g. Cygnus vehicle telemetry), the event-alignment button is disabled with an explanatory tooltip.

---

## 5. Descriptive Calculation Methodology

All descriptive measurements are calculated over the loaded data buffer using real numeric values:

| Metric | Mathematical Formula | Description |
| :--- | :--- | :--- |
| **Maximum Recorded Value** | $Y_{max} = \max_{i \in \text{valid}} \{ y_i \}$ | Highest physical measurement recorded in the window. |
| **Time of Maximum** | $t_{max} = t \text{ where } y(t) = Y_{max}$ | Experimental timestamp at which peak occurred. |
| **Minimum Recorded Value** | $Y_{min} = \min_{i \in \text{valid}} \{ y_i \}$ | Lowest physical measurement recorded in the window. |
| **Arithmetic Mean** | $\bar{Y} = \frac{1}{N_{valid}} \sum_{i=1}^{N_{valid}} y_i$ | Average measurement level across the loaded window. |
| **Peak Difference** | $\Delta_{peak} = Y_{max, A} - Y_{max, B}$ | Empirical difference between peak values. |
| **Time-to-Peak Offset** | $\Delta t_{peak} = t_{max, A} - t_{max, B}$ | Difference in time taken to reach peak measurement. |
| **Net Window Change** | $\Delta_{window} = y(t_{end}) - y(t_{start})$ | Change between final and initial valid readings. |
| **Valid / Missing Count** | $N_{valid}, N_{missing}$ | Count of valid readings vs. null/blank/NaN gaps. |

*Note:* Calculations are executed on the raw buffered points and are completely unaffected by visualization downsampling.

---

## 6. Scientific Validation Safeguards

To prevent misinterpretation of microgravity combustion telemetry:
1. **Zero Fake Ignition:** The application never assumes index 0 represents ignition, and never fabricates ignition times.
2. **Discontinuity Preservation:** Empty readings, missing sensor channels, and null values break SVG line trajectories (`M ... L ...`), rendering visible gaps rather than misleading linear connections.
3. **Investigation Granularity Isolation:** Attempting to compare a continuous sensor series (Saffire) against an experiment matrix (BASS-II) surfaces an immediate safeguard alert:
   > *"Scientific Safeguard: Investigation Granularity Mismatch. A continuous sensor time-series cannot be mathematically compared directly against an experiment test matrix. Please select datasets from the same category."*
4. **Physical Interpretation Nuance:** The findings panel explicitly warns researchers that:
   - *Correlation does not imply causation.*
   - *Differences in temperature or heat flux may stem from sample geometry, flow velocity, or radiometer distance rather than material flammability.*
   - *Sensor traces alone do not constitute a definitive spacecraft material safety rating.*

---

## 7. Verification & Testing Results

| Test Suite | Command / Verification Target | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Linting Verification** | `npm run lint` (`oxlint`) | **PASSED (0 warnings, 0 errors)** | Checked all 71 files across the codebase. |
| **Production Build** | `npm run build` (`vite build`) | **PASSED (242ms)** | Built production bundle (`dist/assets/index-BszqqD-n.js` 496.93 kB, gzip: 124.34 kB). |
| **Ignition Detection Test** | Node.js unit test with synthetic igniter telemetry | **PASSED** | Correctly identified $t_{ign} = 3.0\text{ s}$ on `Igniter Current > 0.5A` trigger; returned `null` when no trigger existed. |
| **Descriptive Statistics Test** | Node.js unit test on synthetic data with null gaps | **PASSED** | Correctly computed min (24.5), max (350.8), mean (160.10), timeOfMax (4.0s), and missingCount (1). |
| **Live Saffire API Integration** | Live backend query on Sample 1 vs Sample 2 | **PASSED** | Successfully matched 61 shared channels. Sample 1 Plume Temp 1 max: 25.02°C; Sample 2 max: 23.59°C; Peak Delta: +1.43°C. |
| **Live BASS-II API Integration** | Live backend query on BASS-II Test B1 vs B2 | **PASSED** | Successfully computed delta O₂ consumed: Test B1 = 0.00% (quenched/no burn), Test B2 = 20.60% (vigorous burn). |
| **Navigation & UI Test** | HTTP GET `http://localhost:5173` | **PASSED (200 OK)** | "Experiment Comparison" navigation tab active and accessible. |

---

## 8. Remaining Considerations & Next Steps

1. **Multi-Channel Overlay:** Currently, the comparison workspace overlays one shared channel at a time (e.g. Plume Temp 1) to maintain clean readability. Future phases could support paired overlays of multiple thermocouples (e.g. Plume Temp 1–6) using coordinated color groups.
2. **Quality Report Flag Annotations:** When the backend validation summary flags specific channels as having negative readings or sensor saturation, displaying visual warning markers directly on the time axis would provide added investigator context.
3. **Data Export:** Exporting the compared time series and descriptive statistical deltas to CSV or JSON formats for scientific publications.
