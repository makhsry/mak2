### Physiochemical Population Balance Model (PBM) with Dissipative Particle Dynamics (DPD) in LAMMPS

This is a [**LAMMPS**](https://www.lammps.org/)-based implementation of a [**Physiochemical Population Balance Model (PBM)**](https://en.wikipedia.org/wiki/Population_balance_equation) using [**Dissipative Particle Dynamics (DPD)**](https://en.wikipedia.org/wiki/Dissipative_particle_dynamics) for structural evolution and [**Transition State Theory (TST)**](https://en.wikipedia.org/wiki/Transition_state_theory) for chemical kinetics.

- The code is accessible from [**here**](Writeups_20200101_PBMwDPD.zip).

The simulation models the **formation and dissociation of chemical clusters** (species types 3–23) from two primary **monomer species** (types 1 and 2). It employs a **hybrid approach**:

- **Mechanical Dynamics**: DPD potential accounts for **thermal and structural behavior**.
- **Physiochemical Kinetics**: TST-based rate constants determine the probability of **species transformation events** (Birth and Death).
- **Population Balance**: Discrete "event" counters are calculated per timestep to modify the **particle population** in-situ while preserving bead numbers or chemical stoichiometry.

**Mathematical Models**

**DPD Force Field**

The interaction between any two particles i and j is governed by three pairwise additive forces:

<strong>F</strong><sub>ij</sub> = <strong>F</strong><sub>ij</sub><sup>C</sup> + <strong>F</strong><sub>ij</sub><sup>D</sup> + <strong>F</strong><sub>ij</sub><sup>R</sup>

- **Conservative Force**:

<strong>F</strong><sup>C</sup><sub>ij</sub> = A<sub>ij</sub> w(r<sub>ij</sub>) <strong>r̂</strong><sub>ij</sub>

- **Dissipative Force**:

<strong>F</strong><sup>D</sup><sub>ij</sub> = -γ w<sup>2</sup>(r<sub>ij</sub>) (<strong>r̂</strong><sub>ij</sub> · <strong>v</strong><sub>ij</sub>) <strong>r̂</strong><sub>ij</sub>

- **Random Force**:

<strong>F</strong><sup>R</sup><sub>ij</sub> = σ w(r<sub>ij</sub>) ζ Δt<sup>-1/2</sup> <strong>r̂</strong><sub>ij</sub>

- **Weighting Function**:

w(r<sub>ij</sub>) = 1 - r<sub>ij</sub>/R<sub>c</sub> for r<sub>ij</sub> < R<sub>c</sub>
w(r<sub>ij</sub>) = 0 for r<sub>ij</sub> ≥ R<sub>c</sub>

Where A<sub>ij</sub> is the maximum repulsion, γ is the friction coefficient, σ is the noise amplitude (related to γ by σ<sup>2</sup> = 2γ k<sub>B</sub> T), and R<sub>c</sub> is the cutoff radius.

**Interaction Parameters (a<sub>ij</sub>)**

The repulsive parameters a<sub>ij</sub> used for the conservative force are derived from interaction "fingerprints" (X<sub>ij</sub>) stored in [`fingerprints_xij.lmp`](Scrapbook_20200101_PBMwDPD_fingerprints_xij.lmp):     

a<sub>ij</sub> = V<sub>1</sub> + V<sub>2</sub> · X<sub>ij</sub>

In the current implementation, V<sub>1</sub> = 1.0 and V<sub>2</sub> = 1.0, mapping energy values directly to force units.

**Transition State Theory (TST) Kinetics**

Chemical reaction rates are calculated using the Arrhenius-like Transition State Theory expression:

k = (k<sub>B</sub> T / N<sub>A</sub> h) exp(-E<sub>a</sub> / R<sub>g</sub> T)

**Physical Constants:**

- k<sub>B</sub>: Boltzmann constant (3.2976 x 10<sup>-27</sup> kcal/K)
- h: Planck constant (2.51 x 10<sup>-38</sup> kcal.s)
- N<sub>A</sub>: Avogadro constant (6.0221 x 10<sup>23</sup> /mol)
- R<sub>g</sub>: Gas constant (1.987 x 10<sup>-3</sup> kcal/K.mol)

The activation energy barriers (E<sub>a</sub>) are defined in [`fingerprints_barrier_n.lmp`](Scrapbook_20200101_PBMwDPD_fingerprints_barrier_n.lmp) for every birth (B) and death (D) event for clusters AA, BB, and AB.

**Population Balance Logic (PBM)**

The number of chemical events (n) performed at each iteration is calculated using the following discrete logic:

- **Monomer Birth (forming clusters AA or BB)**:

n<sub>birth</sub> = ⌊k<sub>B</sub> · N<sub>monomer</sub><sup>2</sup> · Δt · step⌋

- **Cluster Death (dissociating AA or BB)**:

n<sub>death</sub> = ⌊k<sub>D</sub> · N<sub>cluster</sub> · Δt · step⌋

- **Mixed Birth (forming AB clusters)**:

n<sub>mixed birth</sub> = ⌊k<sub>B</sub> · N<sub>A</sub> · N<sub>B</sub> · Δt · step⌋

*Constraint Enforcement:* n<sub>mixed birth</sub> ≤ 2 · min(N<sub>A</sub>, N<sub>B</sub>) to prevent local population exhaustion.

- **Mixed Death (dissociating AB clusters)**:

n<sub>mixed death</sub> = ⌊k<sub>D</sub> · N<sub>AB</sub> · Δt · step⌋

**Species Classification**
  
| Type | Label | Description | Mass (g/mol) | Diameter (Å) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **A** | Primary Monomer A | 122.127 | 5.9775 |
| **2** | **B** | Primary Monomer B | 206.285 | 7.5271 |
| **3–11** | **AA1–AA9** | A-A Homoclusters | 244.254 | ~7.5 |
| **12–20** | **AB1–AB9** | A-B Heteroclusters | 328.412 | ~8.6 |
| **21–23** | **BB1–BB3** | B-B Homoclusters | 412.570 | ~9.5 |

**Execution Flow**

- **Setup**: Initializes 23 atom types and constants.
- **Equilibration**: Runs NPT dynamics (Nose-Hoover barostat/thermostat) followed by NVE.
- **PBM-DYNAMICS Loop**:
   -- Updates `k` rates based on current `T`.
   -- Measures species populations (N<sub>i</sub>).
   -- Calculates n<sub>birth</sub> and n<sub>death</sub> for all 21 reactions.
   -- Executes reactions via `create_atoms` (Birth) and `delete_atoms` (Death).
   -- Updates DPD interaction parameters based on new populations.
   -- Runs N<sub>DYN</sub> steps of mechanical dynamics.

**Usage Instructions**

```bash
lmp -in Main.lmp
```

- **LAMMPS**: Must be compiled with `DPD` and `ASPHERE` packages.
- **Units**: The script uses `real` units (mass in g/mol, distance in Angstroms, time in femtoseconds, energy in kcal/mol).
- `Main.lmp`: Main control script.
- `fingerprints_xij.lmp`: Matrix of interaction fingerprints.
- `fingerprints_barrier_n.lmp`: Kinetic barriers for all species.
- `setup_constant.lmp`: Defines physical constants (k<sub>B</sub>, h, N<sub>A</sub>, R<sub>g</sub>).
- `dynamics_compute_events.lmp`: Implementation of the PBM transformation logic.