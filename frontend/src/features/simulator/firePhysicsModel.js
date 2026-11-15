/**
 * NASA FLAME — Deterministic Combustion & Fluid Mechanics Physics Engine
 * 
 * Physics-informed mathematical model for educational simulation of microgravity 
 * and buoyant combustion. 
 *
 * NOT A VALIDATED CFD PREDICTION:
 * Uses simplified classical relationships from combustion science literature 
 * (Glassman & Yetter, Drysdale, Buckmaster & Peters, NASA Glenn Microgravity Science reports)
 * to deterministically calculate dimensionless numbers, flame dimensions, 
 * flickering frequencies, and transport regimes.
 */

// Fuel literature constants: Limiting Oxygen Index (LOI), adiabatic flame temp (K), soot yield
export const SUPPORTED_FUELS = {
  pmma: {
    id: 'pmma',
    name: 'PMMA (Polymethyl Methacrylate)',
    formula: '(C5O2H8)n',
    category: 'Thermoplastic Solid',
    refFlameTempK: 2050,
    loiPercent: 17.0, // Standard 1g LOI ~17.0%; slightly lower under slow flow in 0g
    sootTendency: 0.55,
    charLengthM: 0.020, // 20 mm characteristic dimension
    activationEnergyKj: 130,
    literatureRef: 'NASA BASS-II / Saffire-III flight experiments & ASTM D2863',
  },
  methane: {
    id: 'methane',
    name: 'Methane (CH4)',
    formula: 'CH4',
    category: 'Gaseous Hydrocarbon',
    refFlameTempK: 2220,
    loiPercent: 12.0,
    sootTendency: 0.15,
    charLengthM: 0.015,
    activationEnergyKj: 125,
    literatureRef: 'NASA Glenn Drop Tower & ISS CIR (Combustion Integrated Rack)',
  },
  ethylene: {
    id: 'ethylene',
    name: 'Ethylene (C2H4)',
    formula: 'C2H4',
    category: 'Gaseous Alkene (High Sooting)',
    refFlameTempK: 2370,
    loiPercent: 10.0,
    sootTendency: 0.85,
    charLengthM: 0.015,
    activationEnergyKj: 140,
    literatureRef: 'NASA ACME (Advanced Combustion via Microgravity Experiments)',
  },
  heptane: {
    id: 'heptane',
    name: 'Heptane (C7H16)',
    formula: 'C7H16',
    category: 'Liquid Droplet Fuel',
    refFlameTempK: 2290,
    loiPercent: 13.5,
    sootTendency: 0.65,
    charLengthM: 0.025,
    literatureRef: 'NASA FLEX (Flame Extinction Experiment) droplet burning',
  },
};

// Documented Quick Presets
export const SIMULATION_PRESETS = [
  {
    id: 'earth_ref',
    name: 'Earth Reference',
    badge: '1.0g Reference',
    description: 'Terrestrial sea-level atmosphere: buoyant upward convection and natural flickering.',
    params: {
      o2Percent: 20.95,
      gravityG: 1.0,
      tempC: 20.0,
      pressureKpa: 101.325,
      airflowVelocity: 0.0,
      fuelType: 'pmma',
    },
  },
  {
    id: 'microgravity_iss',
    name: 'NASA Microgravity ISS',
    badge: '0.0g Quiescent',
    description: 'Quiescent microgravity: buoyant convection vanishes, diffusion creates a stable spherical blue flame.',
    params: {
      o2Percent: 20.95,
      gravityG: 0.0,
      tempC: 20.0,
      pressureKpa: 101.325,
      airflowVelocity: 0.0,
      fuelType: 'pmma',
    },
  },
  {
    id: 'saffire_flow',
    name: 'Saffire Flight Flow',
    badge: '0.0g Forced Flow',
    description: 'Cygnus vehicle Saffire flight conditions: 0g with forced ventilation (0.20 m/s airflow).',
    params: {
      o2Percent: 21.0,
      gravityG: 0.0,
      tempC: 21.5,
      pressureKpa: 98.5,
      airflowVelocity: 0.20,
      fuelType: 'pmma',
    },
  },
  {
    id: 'exploration_atm',
    name: 'Exploration Atmosphere',
    badge: 'NASA Artemis Habitat',
    description: 'Planned NASA Lunar/Mars habitat: reduced pressure (56 kPa) with 34% elevated O2 to maintain normoxic partial pressure.',
    params: {
      o2Percent: 30.0, // Capped to 30% control range
      gravityG: 0.166, // Lunar gravity ~0.17g
      tempC: 22.0,
      pressureKpa: 56.0,
      airflowVelocity: 0.08,
      fuelType: 'pmma',
    },
  },
  {
    id: 'hypoxic_extinction',
    name: 'Hypoxic Extinction Limit',
    badge: 'Extinction Threshold',
    description: 'Low oxygen concentration below fuel flammability limit: chemical heat release cannot sustain reaction zone.',
    params: {
      o2Percent: 14.0,
      gravityG: 1.0,
      tempC: 20.0,
      pressureKpa: 101.325,
      airflowVelocity: 0.0,
      fuelType: 'pmma',
    },
  },
  {
    id: 'oxygen_rich',
    name: 'Oxygen-Rich Chamber',
    badge: '30% O2 Accelerated',
    description: 'Elevated oxygen concentration: elevated flame temperatures, intense radiation, and high soot output.',
    params: {
      o2Percent: 30.0,
      gravityG: 1.0,
      tempC: 20.0,
      pressureKpa: 101.325,
      airflowVelocity: 0.0,
      fuelType: 'pmma',
    },
  },
];

/**
 * Deterministically compute fluid mechanics & combustion state
 */
export function computeFirePhysics({
  o2Percent = 21.0,
  gravityG = 1.0,
  tempC = 20.0,
  pressureKpa = 101.325,
  airflowVelocity = 0.0,
  fuelType = 'pmma',
}) {
  // Validate and clamp input bounds
  const clampedO2 = Math.max(0, Math.min(30.0, Number(o2Percent) || 21.0));
  const clampedG = Math.max(0, Math.min(1.0, Number(gravityG) || 0.0));
  const clampedTempC = Math.max(0, Math.min(100.0, Number(tempC) || 20.0));
  const clampedPressureKpa = Math.max(20.0, Math.min(150.0, Number(pressureKpa) || 101.325));
  const clampedAirflow = Math.max(0, Math.min(0.5, Number(airflowVelocity) || 0.0));
  const fuel = SUPPORTED_FUELS[fuelType] || SUPPORTED_FUELS.pmma;

  // 1. Thermodynamic & Ambient Properties
  const T_inf_K = clampedTempC + 273.15; // Ambient temperature (K)
  const P_Pa = clampedPressureKpa * 1000; // Pressure in Pascals
  const Ru = 8.314462; // Universal gas constant J/(mol*K)
  const M_air = 0.02897; // Molar mass of air kg/mol

  // Ideal Gas Ambient Density: rho = P * M / (R * T)
  const rho_inf = (P_Pa * M_air) / (Ru * T_inf_K); // ~1.20 kg/m3 at 101.3 kPa, 293 K

  // Oxygen Partial Pressure: P_O2 = (O2% / 100) * P
  const pO2_kpa = (clampedO2 / 100.0) * clampedPressureKpa;

  // Kinematic Viscosity of air (Sutherland approx scaled from 293K)
  const nu_ref = 1.516e-5; // m^2/s at 20°C, 101.3 kPa
  const nu = nu_ref * Math.pow(T_inf_K / 293.15, 1.7) * (101.325 / clampedPressureKpa);

  // Volumetric thermal expansion coefficient for ideal gas
  const beta = 1.0 / T_inf_K; // ~1/293.15 = 0.00341 1/K

  // Gravitational acceleration
  const g_eff = clampedG * 9.80665; // m/s^2

  // 2. Combustion & Flame Temperature Estimation
  // Flame temp scales with O2 concentration and pressure (adiabatic flame dependence)
  const o2Ratio = clampedO2 / 21.0;
  const pRatio = clampedPressureKpa / 101.325;
  const flameTempK = Math.round(
    fuel.refFlameTempK * Math.pow(Math.max(0.2, o2Ratio), 0.22) * Math.pow(pRatio, 0.04)
  );
  const deltaT = Math.max(50, flameTempK - T_inf_K);

  // 3. Non-Dimensional Fluid Numbers
  const L = fuel.charLengthM; // Characteristic dimension (m)

  // Grashof Number: Gr = g * beta * deltaT * L^3 / nu^2
  // Measures ratio of buoyant forces to viscous forces
  const Gr = (g_eff * beta * deltaT * Math.pow(L, 3)) / Math.pow(nu, 2);

  // Prandtl Number for air
  const Pr = 0.71;

  // Rayleigh Number: Ra = Gr * Pr
  const Ra = Gr * Pr;

  // Reynolds Number (Forced crossflow): Re = u * L / nu
  const Re = (clampedAirflow * L) / nu;

  // Richardson Number: Ri = Gr / Re^2
  // Ri >> 1 -> Buoyancy dominated; Ri << 1 -> Forced convection dominated
  const Ri = Re > 0.01 ? Gr / Math.pow(Re, 2) : (Gr > 0 ? 999.0 : 0.0);

  // 4. Characteristic Timescales (Diffusion vs Buoyant Convection)
  // Binary diffusion coefficient of O2 in N2: D ~ 2.1e-5 m^2/s at 293K
  const D_o2 = 2.1e-5 * Math.pow(T_inf_K / 293.15, 1.75) * (101.325 / clampedPressureKpa);
  const tau_diff = Math.pow(L, 2) / D_o2; // Diffusive transport timescale ~seconds

  // Characteristic buoyant convection velocity: u_buoy ~ sqrt(g * L * deltaT / T_inf)
  const u_buoy = g_eff > 0.001 ? Math.sqrt((g_eff * L * deltaT) / T_inf_K) : 0.0;
  const tau_conv = u_buoy > 0.001 ? L / u_buoy : 999.0;

  // 5. Buckmaster-Peters / Cetegen Flame Flickering Frequency (1g Natural Puffing)
  // f ~ 1.5 * sqrt(g / D_flame) for buoyant diffusion flames
  const naturalFlickerHz = clampedG > 0.05
    ? 1.5 * Math.sqrt(g_eff / L) * Math.min(1.5, Math.pow(o2Ratio, 0.3))
    : 0.0;

  // 6. Extinction Check
  // Low oxygen extinction: if O2% < fuel LOI, reaction cannot sustain itself
  const isHypoxicExtinct = clampedO2 < fuel.loiPercent;
  // Low pressure extinction limit (< 25 kPa for typical diffusion flames)
  const isLowPressureExtinct = clampedPressureKpa < 25.0;
  const isExtinct = isHypoxicExtinct || isLowPressureExtinct;

  // 7. Scientific Combustion Regime Classification
  let regimeId = 'BUOYANCY_DOMINATED';
  let regimeName = 'Buoyancy-Dominated Elongated Plume';
  let regimeBadgeColor = 'bg-orange-100 text-orange-800 border-orange-300';
  let regimeSummary = '';

  if (isExtinct) {
    regimeId = 'EXTINCT';
    regimeName = isHypoxicExtinct ? 'Hypoxic Extinction Quench' : 'Low-Pressure Extinction Limit';
    regimeBadgeColor = 'bg-rose-100 text-rose-800 border-rose-300';
    regimeSummary = isHypoxicExtinct
      ? `Oxygen concentration (${clampedO2.toFixed(1)}%) is below the Limiting Oxygen Index (LOI = ${fuel.loiPercent}%) for ${fuel.name}. Chemical heat release is insufficient to overcome conductive heat losses, extinguishing the flame.`
      : `Ambient pressure (${clampedPressureKpa.toFixed(1)} kPa) is below the critical flammability limit (~25 kPa). Molecular collision frequency drops below the threshold required for sustained chain branching.`;
  } else if (clampedG <= 0.05 && clampedAirflow <= 0.03) {
    regimeId = 'MICROGRAVITY_DIFFUSION';
    regimeName = 'Quiescent Microgravity Diffusion Sphere';
    regimeBadgeColor = 'bg-sky-100 text-sky-800 border-sky-300';
    regimeSummary = 'At near-zero gravity (g ≈ 0), buoyant upward acceleration vanishes (Gr ≈ 0). Transport of oxygen to the reaction zone is governed entirely by molecular diffusion, resulting in a stable, spherical/hemispherical flame with suppressed soot formation and predominant blue chemiluminescent emission.';
  } else if (clampedG <= 0.05 && clampedAirflow > 0.03) {
    regimeId = 'MICROGRAVITY_FORCED_FLOW';
    regimeName = 'Microgravity Forced Convection Wake (Saffire Regime)';
    regimeBadgeColor = 'bg-indigo-100 text-indigo-800 border-indigo-300';
    regimeSummary = `In microgravity with forced ventilation (u = ${clampedAirflow.toFixed(2)} m/s, Re = ${Math.round(Re)}), low-speed airflow feeds oxidizer to the trailing boundary layer, forming a steady elongated wake without buoyant flickering. This matches observed NASA Saffire flight experiment behavior.`;
  } else if (clampedG > 0.05 && clampedAirflow > 0.15 && Ri < 1.0) {
    regimeId = 'FORCED_CONVECTION';
    regimeName = 'Forced-Convection Deflected Flame';
    regimeBadgeColor = 'bg-amber-100 text-amber-800 border-amber-300';
    regimeSummary = `Forced crossflow dominates natural buoyancy (Richardson Ri = ${Ri.toFixed(2)} < 1.0). The flame is deflected horizontally downstream in the air stream with convective cooling along the leading edge.`;
  } else if (clampedG > 0.05 && clampedG < 0.4) {
    regimeId = 'PARTIAL_GRAVITY';
    regimeName = 'Partial-Gravity Transition (Lunar/Martian)';
    regimeBadgeColor = 'bg-teal-100 text-teal-800 border-teal-300';
    regimeSummary = `Intermediate gravity (g = ${clampedG.toFixed(2)}g, Gr = ${Math.round(Gr)}). Buoyancy is weak but non-zero: the flame exhibits moderate elongation with dampened flickering, bridging diffusion-dominated and buoyant regimes.`;
  } else {
    regimeId = 'BUOYANCY_DOMINATED';
    regimeName = 'Earth 1g Buoyancy-Dominated Plume';
    regimeBadgeColor = 'bg-orange-100 text-orange-800 border-orange-300';
    regimeSummary = `Strong gravity-induced buoyant acceleration (g = ${clampedG.toFixed(2)}g, Rayleigh Ra = ${Ra.toExponential(2)}) drives a vigorous upward convective plume. Hot combustion gases accelerate upward, inducing periodic shear instabilities that produce characteristic flame flickering (~${naturalFlickerHz.toFixed(1)} Hz).`;
  }

  // 8. Visual Animation Mapping Parameters (Derived deterministically)
  // Elongation aspect ratio: 1.0 = perfect circle/sphere, 3.2 = elongated Earth flame
  const visualAspectRatio = isExtinct
    ? 0.0
    : 1.0 + Math.pow(clampedG, 0.6) * 1.8 + (clampedAirflow > 0 ? 0.4 : 0.0);

  // Radius / Flame size factor based on O2, Pressure, and Fuel
  const baseFlameRadius = isExtinct
    ? 0.0
    : 32 + (clampedO2 / 30.0) * 18 + (clampedPressureKpa / 101.3) * 6;

  // Blue chemiluminescence vs yellow soot radiation ratio
  // 0g suppresses soot inception; high 1g buoyancy concentrates soot in the hot tip
  const blueChemiRatio = isExtinct
    ? 0.0
    : Math.max(0.1, 1.0 - clampedG * 0.7 - fuel.sootTendency * 0.35 + (1.0 - o2Ratio) * 0.2);

  const sootYellowRatio = isExtinct
    ? 0.0
    : Math.min(1.0, Math.max(0.05, clampedG * 0.8 + fuel.sootTendency * 0.4 + (o2Ratio - 1.0) * 0.3));

  // Visual tilt angle from airflow
  const flowTiltDeg = Math.min(45, clampedAirflow * 90.0);

  return {
    // Inputs echoing
    o2Percent: clampedO2,
    gravityG: clampedG,
    tempC: clampedTempC,
    pressureKpa: clampedPressureKpa,
    airflowVelocity: clampedAirflow,
    fuel,

    // Calculated Thermodynamic & Fluid Mechanics Properties
    T_inf_K: Math.round(T_inf_K * 10) / 10,
    rho_inf: Math.round(rho_inf * 1000) / 1000,
    pO2_kpa: Math.round(pO2_kpa * 10) / 10,
    nu: nu,
    g_eff: Math.round(g_eff * 100) / 100,
    flameTempK,
    deltaT: Math.round(deltaT),

    // Non-Dimensional Numbers
    Gr: Math.round(Gr),
    Ra: Math.round(Ra),
    Re: Math.round(Re * 10) / 10,
    Ri: Math.round(Ri * 10) / 10,

    // Timescales & Dynamics
    tau_diff: Math.round(tau_diff * 10) / 10,
    tau_conv: Math.round(tau_conv * 10) / 10,
    naturalFlickerHz: Math.round(naturalFlickerHz * 10) / 10,

    // Extinction & Regime
    isExtinct,
    isHypoxicExtinct,
    isLowPressureExtinct,
    regimeId,
    regimeName,
    regimeBadgeColor,
    regimeSummary,

    // Visual animation driving parameters
    visual: {
      aspectRatio: visualAspectRatio,
      radius: baseFlameRadius,
      blueChemiRatio: Math.max(0, Math.min(1, blueChemiRatio)),
      sootYellowRatio: Math.max(0, Math.min(1, sootYellowRatio)),
      flickerAmp: clampedG > 0.05 ? 0.08 + clampedG * 0.12 : 0.01,
      flickerFreq: naturalFlickerHz,
      flowTiltDeg,
    },
  };
}
