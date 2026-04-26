### _Draft_: Physiochemical Population Balance Model (PBM) with Dissipative Particle Dynamics (DPD) in LAMMPS

This is a [**LAMMPS**](https://www.lammps.org/)-based implementation of a [**Physiochemical Population Balance Model (PBM)**](https://en.wikipedia.org/wiki/Population_balance_equation) using [**Dissipative Particle Dynamics (DPD)**](https://en.wikipedia.org/wiki/Dissipative_particle_dynamics) for structural evolution and [**Transition State Theory (TST)**](https://en.wikipedia.org/wiki/Transition_state_theory) for chemical kinetics.

This simulation setup is for **cocrystalization of ibuprofen and nicotinamide**. The simulation models the **formation and dissociation of chemical clusters** (species types 3–23) from two primary **monomer species** (types 1 and 2). It employs a **hybrid approach**:

- **Mechanical Dynamics**: DPD potential accounts for **thermal and structural behavior**.
- **Physiochemical Kinetics**: TST-based rate constants determine the probability of **species transformation events** (Birth and Death).
- **Population Balance**: Discrete "event" counters are calculated per timestep to modify the **particle population** in-situ while preserving bead numbers or chemical stoichiometry.

**DPD Part**

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

The repulsive parameters a<sub>ij</sub> used for the conservative force are derived from interaction "fingerprints" (X<sub>ij</sub>) stored in `fingerprints_xij.lmp`:     

a<sub>ij</sub> = V<sub>1</sub> + V<sub>2</sub> · X<sub>ij</sub>

In the current implementation, V<sub>1</sub> = 1.0 and V<sub>2</sub> = 1.0, mapping energy values directly to force units.

**TST Part**

Chemical reaction rates are calculated using the Arrhenius-like Transition State Theory expression:

k = (k<sub>B</sub> T / N<sub>A</sub> h) exp(-E<sub>a</sub> / R<sub>g</sub> T)

**Physical Constants:**

- k<sub>B</sub>: Boltzmann constant (3.2976 x 10<sup>-27</sup> kcal/K)
- h: Planck constant (2.51 x 10<sup>-38</sup> kcal.s)
- N<sub>A</sub>: Avogadro constant (6.0221 x 10<sup>23</sup> /mol)
- R<sub>g</sub>: Gas constant (1.987 x 10<sup>-3</sup> kcal/K.mol)

The activation energy barriers (E<sub>a</sub>) are defined in `fingerprints_barrier_n.lmp` for every birth (B) and death (D) event for clusters AA, BB, and AB.

**PBM Part**

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

#### Scripts

- **`Main.lmp`**
```bash
# main  
#------------------------------------------------------
units real 
# 			mass = grams/mole
# 			distance = Angstroms
# 			time = femtoseconds
# 			energy = kcal/mol
# 			velocity = Angstroms/femtosecond
# 			force = (kcal/mol)/Angstrom
# 			torque = kcal/mol
# 			temperature = Kelvin
# 			pressure = atmospheres
# 			density = g/cm^3
#------------------------------------------------------
timer full 
variable start timer
#------------------------------------------------------
variable dt equal 1
timestep ${dt}
dimension 3
boundary p p p
#------------------------------------------------------
atom_style hybrid atomic sphere dpd
atom_modify map array sort 1 100
#------------------------------------------------------
newton on
#------------------------------------------------------
variable T equal 300.0 
variable P equal 1.0 
#------------------------------------------------------
variable RcG equal 12.5
variable RcGc equal 10*${RcG}
#------------------------------------------------------
variable seed equal 20240526
#------------------------------------------------------
variable dampP equal 500  
variable dampT equal 100  
variable dumping equal 1000 
variable thermoing equal 100  
variable nDYN equal 100000    
#------------------------------------------------------
comm_modify vel yes cutoff ${RcGc}
neighbor ${RcG} nsq
neigh_modify delay 0 every 1 check yes binsize ${RcGc}
#------------------------------------------------------
include setup_constant.lmp
include fingerprints_xij.lmp
include fingerprints_aij.lmp
#------------------------------------------------------
include setup_n0.lmp
#------------------------------------------------------
variable L equal 1000 # gets updated during NPT
#------------------------------------------------------
variable box_xhi equal ${L}/2 
variable box_xlo equal -${L}/2 
variable box_yhi equal ${L}/2
variable box_ylo equal -${L}/2
variable box_zhi equal ${L}/2
variable box_zlo equal -${L}/2
#------------------------------------------------------
region BOX block ${box_xlo} ${box_xhi} ${box_ylo} ${box_yhi} ${box_zlo} ${box_zhi}
#------------------------------------------------------
create_box 23 BOX
#------------------------------------------------------
pair_style dpd ${T} ${RcG} ${seed}
#------------------------------------------------------
include setup_potential.lmp
#------------------------------------------------------
create_atoms 1 random ${n0_1} ${seed} NULL overlap ${RcG} maxtry 1000000
create_atoms 2 random ${n0_2} ${seed} NULL overlap ${RcG} maxtry 1000000
#------------------------------------------------------
include fingerprints_mass.lmp
include fingerprints_diameter.lmp
include fingerprints_label.lmp
#------------------------------------------------------
velocity all create ${T} ${seed} 
run 0
velocity all scale ${T} 
#------------------------------------------------------
minimize 1.0e-6 1.0e-8 1000 10000 
#------------------------------------------------------
dump DUMP all custom ${dumping} pre.* id type mass diameter x y z vx vy vz fx fy fz
#------------------------------------------------------
fix NPT all npt temp ${T} ${T} ${dampT} iso ${P} ${P} ${dampP}
#------------------------------------------------------
thermo ${thermoing}
thermo_style custom step atoms temp press density
#------------------------------------------------------
run ${nDYN}
#------------------------------------------------------
unfix NPT
undump DUMP 
#------------------------------------------------------
variable dumping equal 100
variable thermoing equal 10  
variable nDYN equal 1000
#------------------------------------------------------
dump DUMP all custom ${dumping} post.* id type mass diameter x y z vx vy vz fx fy fz
#------------------------------------------------------
thermo ${thermoing}
thermo_style custom step atoms temp press density
#------------------------------------------------------
fix NVE all nve
fix fixP all box/relax iso ${P}
#fix NVT all nvt temp ${T} ${T} 10
#------------------------------------------------------
reset_timestep 0
#------------------------------------------------------
variable iterations equal 0
variable iterationsMAX equal ${nDYN}
#--------------------------------------------- ---------
include fingerprints_barrier_n.lmp
#------------------------------------------------------
label DYN 
variable iterations equal ${iterations}+1
#------------------------------------------------------
include dynamics_compute_kinetic.lmp
#------------------------------------------------------
include dynamics_create_groups.lmp
#------------------------------------------------------
include dynamics_compute_n_groups.lmp
#------------------------------------------------------
include dynamics_compute_events.lmp
#------------------------------------------------------
include dynamics_clean_groups.lmp
#------------------------------------------------------ 
include dynamics_create_groups.lmp
#------------------------------------------------------
include dynamics_compute_n_groups.lmp
#------------------------------------------------------
include dynamics_clean_groups.lmp
#------------------------------------------------------
delete_atoms overlap 0.5 all all
reset_atoms id sort yes
#------------------------------------------------------
if ${iterations}>=${iterationsMAX} then 'jump SELF END'
#------------------------------------------------------ 
velocity all scale ${T} 
#------------------------------------------------------
run ${nDYN}
#------------------------------------------------------
jump SELF DYN 
#------------------------------------------------------
label END
#------------------------------------------------------
variable stop timer
print "Elapsed time: $(v_stop-v_start:%.6f)"
print "ALL DONE" 
#------------------------------------------------------
# End of file
```

- **`_setup_constant.lmp`**
```bash
variable kB equal 3.297623483e-27	#kcal/K
variable h equal 1.054571817e-34 #J.s
variable h equal ${h}*0.000239006 #kcal.s
variable Rg equal 1.98720425864083e-3 #kcal/(K.mol)
variable nAv equal 6.02214076e23 #/mol
```

- **`fingerprints_mass.lmp`**
```bash
# values in grams/mole
mass 1 122.127
mass 2 206.285
mass 3 244.254
mass 4 244.254
mass 5 244.254
mass 6 244.254
mass 7 244.254
mass 8 244.254
mass 9 244.254
mass 10 244.254
mass 11 244.254
mass 12 328.412
mass 13 328.412
mass 14 328.412
mass 15 328.412
mass 16 328.412
mass 17 328.412
mass 18 328.412
mass 19 328.412
mass 20 328.412
mass 21 412.57
mass 22 412.57
mass 23 412.57
```

- **`fingerprints_label.lmp`**
```bash
labelmap atom 1 A
labelmap atom 2 B
labelmap atom 3 AA1
labelmap atom 4 AA2
labelmap atom 5 AA3
labelmap atom 6 AA4
labelmap atom 7 AA5
labelmap atom 8 AA6
labelmap atom 9 AA7
labelmap atom 10 AA8
labelmap atom 11 AA9
labelmap atom 12 AB1
labelmap atom 13 AB2
labelmap atom 14 AB3
labelmap atom 15 AB4
labelmap atom 16 AB5
labelmap atom 17 AB6
labelmap atom 18 AB7
labelmap atom 19 AB8
labelmap atom 20 AB9
labelmap atom 21 BB1
labelmap atom 22 BB2
labelmap atom 23 BB3
```

- **`setup_n0.lmp`**
```bash
variable n0_1 equal 10000
variable n0_2 equal 10000
variable n0_3 equal 0
variable n0_4 equal 0
variable n0_5 equal 0
variable n0_6 equal 0
variable n0_7 equal 0
variable n0_8 equal 0
variable n0_9 equal 0
variable n0_10 equal 0
variable n0_11 equal 0
variable n0_12 equal 0
variable n0_13 equal 0
variable n0_14 equal 0
variable n0_15 equal 0
variable n0_16 equal 0
variable n0_17 equal 0
variable n0_18 equal 0
variable n0_19 equal 0
variable n0_20 equal 0
variable n0_21 equal 0
variable n0_22 equal 0
variable n0_23 equal 0
```

- **`dynamics_create_groups.lmp`**
```bash
group nA type 1
group nB type 2
group nAA1 type 3
group nAA2 type 4
group nAA3 type 5
group nAA4 type 6
group nAA5 type 7
group nAA6 type 8
group nAA7 type 9
group nAA8 type 10
group nAA9 type 11
group nAB1 type 12
group nAB2 type 13
group nAB3 type 14
group nAB4 type 15
group nAB5 type 16
group nAB6 type 17
group nAB7 type 18
group nAB8 type 19
group nAB9 type 20
group nBB1 type 21
group nBB2 type 22
group nBB3 type 23
```

- **`setup_potential.lmp`**
```bash
lines = []
lines.append("# inputs_potential")
lines.append("# aij 		A (force units)")
lines.append("# aij 		gamma (force/velocity units) / (1A/fs)")
lines.append("# RcG 		cutoff (distance units)")
# Pattern: pair_coeff i j ${a_i_j} ${a_i_j} ${RcG}
for i in range(1, 24):
    for j in range(1, 24):
        lines.append(f"pair_coeff {i} {j} ${{a_{i}_{j}}} ${{a_{i}_{j}}} ${{RcG}}")
content = "\n".join(lines) + "\n"
with open("setup_potential.lmp", "w") as f:
    f.write(content)
```

- **`dynamics_compute_natoms.lmp`**
```bash
lines = []
lines.append("variable nA0 atom type==1")
lines.append("variable nB0 atom type==2")
for i in range(1, 10):
    lines.append(f"variable nAA{i}0 atom type=={2+i}")
for i in range(1, 10):
    lines.append(f"variable nAB{i}0 atom type=={11+i}")
for i in range(1, 4):
    lines.append(f"variable nBB{i}0 atom type=={20+i}")
lines.append("variable nTot equal atoms")
content = "\n".join(lines) + "\n"
with open("dynamics_compute_natoms.lmp", "w") as f:
    f.write(content)
```

- **`dynamics_clean_groups.lmp`**
```bash
lines = []
for g in ["nA", "nB"]:
    lines.append(f"group {g} delete")
for i in range(1, 10):
    lines.append(f"group nAA{i} delete")
for i in range(1, 10):
    lines.append(f"group nAB{i} delete")
for i in range(1, 4):
    lines.append(f"group nBB{i} delete")
content = "\n".join(lines) + "\n"
with open("dynamics_clean_groups.lmp", "w") as f:
    f.write(content)
```

- **`dynamics_compute_n_groups.lmp`**
```bash
lines = []
lines.append("variable nA0 equal count(nA)")
lines.append("variable nB0 equal count(nB)")
for i in range(1, 10):
    lines.append(f"variable nAA{i}0 equal count(nAA{i})")
for i in range(1, 10):
    lines.append(f"variable nAB{i}0 equal count(nAB{i})")
for i in range(1, 4):
    lines.append(f"variable nBB{i}0 equal count(nBB{i})")
content = "\n".join(lines) + "\n"
with open("dynamics_compute_n_groups.lmp", "w") as f:
    f.write(content)
```

- **`dynamics_compute_events.lmp`**
```bash 
def generate_aa_block(i):
    lines = []
    lines.append(f"#--- AA{i} --- B")
    lines.append(f"variable nAA{i}_B equal round(${{kAA{i}eB}}*(${{nA0}})*(${{nA0}})*(step*dt))")
    lines.append(f"if ${{nAA{i}_B}}>${{nA0}} then 'variable nAA{i}_B equal ${{nA0}}'")
    lines.append(f"create_atoms {3+i} random ${{nAA{i}_B}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    lines.append(f"delete_atoms random count ${{nAA{i}_B}} yes nA NULL ${{seed}} compress yes")
    lines.append(f"#--- AA{i} --- D ")
    lines.append(f"variable nAA{i}_D equal round(${{kAA{i}eD}}*(${{nAA{i}0}})*(step*dt))")
    lines.append(f"variable dummy equal ${{nAA{i}0}}+${{nAA{i}_B}}")
    lines.append(f"if ${{nAA{i}_D}}>${{dummy}} then 'variable nAA{i}_D equal ${{dummy}}'")
    lines.append(f"delete_atoms random count ${{nAA{i}_D}} yes nAA{i} NULL ${{seed}} compress yes")
    lines.append(f"create_atoms 1 random ${{nAA{i}_D}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    return lines

def generate_bb_block(i):
    lines = []
    lines.append(f"#--- BB{i} --- B")
    lines.append(f"variable nBB{i}_B equal round(${{kBB{i}eB}}*(${{nB0}})*(${{nB0}})*(step*dt))")
    lines.append(f"if ${{nBB{i}_B}}>${{nB0}} then 'variable nBB{i}_B equal ${{nB0}}'")
    lines.append(f"create_atoms {20+i} random ${{nBB{i}_B}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    lines.append(f"delete_atoms random count ${{nBB{i}_B}} yes nB NULL ${{seed}} compress yes")
    lines.append(f"#--- BB{i} --- D ")
    lines.append(f"variable nBB{i}_D equal round(${{kBB{i}eD}}*(${{nBB{i}0}})*(step*dt))")
    lines.append(f"variable dummy equal ${{nBB{i}0}}+${{nBB{i}_B}}")
    lines.append(f"if ${{nBB{i}_D}}>${{dummy}} then 'variable nBB{i}_D equal ${{dummy}}'")
    lines.append(f"delete_atoms random count ${{nBB{i}_D}} yes nBB{i} NULL ${{seed}} compress yes")
    lines.append(f"create_atoms 2 random ${{nBB{i}_D}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    return lines

def generate_ab_block(i):
    lines = []
    lines.append(f"#--- AB{i} --- B")
    lines.append(f"variable STU equal ${{nA0}}")
    lines.append(f"if ${{nA0}}>${{nB0}} then 'variable STU equal ${{nB0}}'")
    lines.append(f"variable stuSUM equal 2*${{STU}}")
    lines.append(f"if ${{nB0}}>${{nA0}} then 'variable STU equal ${{nA0}}'")
    lines.append(f"variable stuSUM equal 2*${{STU}}")
    lines.append(f"variable nAB{i}_B equal round(${{kAB{i}eB}}*(${{nA0}})*(${{nB0}})*(step*dt))")
    lines.append(f"if ${{nAB{i}_B}}>${{stuSUM}} then 'variable nAB{i}_B equal ${{stuSUM}}'")
    lines.append(f"create_atoms {11+i} random ${{nAB{i}_B}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    lines.append(f"variable dummy equal round(${{nAB{i}_B}}/2)")
    lines.append(f"variable DEL equal ${{dummy}}")
    lines.append(f"if ${{dummy}}>${{nA0}} then 'variable DEL equal ${{nA0}}'")
    lines.append(f"delete_atoms random count ${{DEL}} yes nA NULL ${{seed}} compress yes")
    lines.append(f"variable DEL equal ${{dummy}}")
    lines.append(f"if ${{dummy}}>${{nB0}} then 'variable DEL equal ${{nB0}}'")
    lines.append(f"delete_atoms random count ${{DEL}} yes nB NULL ${{seed}} compress yes")
    lines.append(f"#--- AB{i} --- D ")
    lines.append(f"variable nAB{i}_D equal round(${{kAB{i}eD}}*(${{nAB{i}0}})*(step*dt))")
    lines.append(f"variable dummy equal ${{nAB{i}0}}+${{nAB{i}_B}}")
    lines.append(f"if ${{nAB{i}_D}}>${{dummy}} then 'variable nAB{i}_D equal ${{dummy}}'")
    lines.append(f"delete_atoms random count ${{nAB{i}_D}} yes nAB{i} NULL ${{seed}} compress yes")
    lines.append(f"variable dummy equal round(${{nAB{i}_D}}/2)")
    lines.append(f"create_atoms 1 random ${{dummy}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    lines.append(f"create_atoms 2 random ${{dummy}} ${{seed}} NULL overlap ${{RcG}} maxtry 1000000")
    return lines

lines = []
for i in range(1, 10):
    lines.extend(generate_aa_block(i))
for i in range(1, 4):
    lines.extend(generate_bb_block(i))
for i in range(1, 10):
    lines.extend(generate_ab_block(i))
content = "\n".join(lines) + "\n"
with open("dynamics_compute_events.lmp", "w") as f:
    f.write(content)
```

- **`dynamics_compute_kinetic.lmp`**
```bash
def generate_kinetic_var(prefix, indices, event):
    """Generate kinetic rate variable for given indices"""
    lines = []
    formula = "((${kB}*${T})/(${nAv}*${h}))*exp(-1*${" + prefix + "{i}{event}}/${Rg}*${T}))"
    for i in indices:
        lines.append(f"variable k{prefix}{i}{event} equal {formula.format(prefix=prefix, i=i, event=event)}")
    return lines

lines = []
bb_indices = [1, 2, 3]
lines.extend(generate_kinetic_var("BB", bb_indices, "eB"))
lines.extend(generate_kinetic_var("BB", bb_indices, "eD"))
aa_indices = range(1, 10)
lines.extend(generate_kinetic_var("AA", aa_indices, "eB"))
lines.extend(generate_kinetic_var("AA", aa_indices, "eD"))
ab_indices = range(1, 10)
lines.extend(generate_kinetic_var("AB", ab_indices, "eB"))
lines.extend(generate_kinetic_var("AB", ab_indices, "eD"))
content = "\n".join(lines) + "\n"
with open("dynamics_compute_kinetic.lmp", "w") as f:
    f.write(content)
```

- **`fingerprints_barrier_n.lmp`**
```bash
# values in kcal/mol
variable BB1eB equal -0.737801637078771
variable BB2eB equal -0.8979483363452747
variable BB3eB equal -0.7440735622408844
variable BB1eD equal 0.21948571428571428
variable BB2eD equal -0.8983735516105027
variable BB3eD equal -0.8895503348570212
variable AA1eB equal 0.012
variable AA2eB equal -0.894280854682683
variable AA3eB equal -0.8803550547464654
variable AA4eB equal -0.9012969065589453
variable AA5eB equal 0.0025142857142857133
variable AA6eB equal 0.0
variable AA7eB equal 0.00028571428571428595
variable AA8eB equal 0.005714285714285714
variable AA9eB equal -0.8795046242160092
variable AA1eD equal 0.11542857142857144
variable AA2eD equal -0.9882002763899224
variable AA3eD equal -0.9839481237376421
variable AA4eD equal -0.9555118528755182
variable AA5eD equal 0.20977142857142855
variable AA6eD equal 0.9073142857142859
variable AA7eD equal 0.6710285714285714
variable AA8eD equal 0.6920571428571429
variable AA9eD equal -1.0
variable AB1eB equal -0.0
variable AB2eB equal -0.7216434570001062
variable AB3eB equal -0.8377803763155096
variable AB4eB equal 0.05182857142857143
variable AB5eB equal -0.6771553098756244
variable AB6eB equal 0.09228571428571429
variable AB7eB equal 0.014114285714285713
variable AB8eB equal -0.7530030828106727
variable AB9eB equal -0.793823748272563
variable AB1eD equal -0.7845221643456999
variable AB2eD equal 0.9423428571428571
variable AB3eD equal 0.26542857142857146
variable AB4eD equal 1.0
variable AB5eD equal 0.8278285714285715
variable AB6eD equal 0.019714285714285712
variable AB7eD equal 0.9756571428571428
variable AB8eD equal 0.7879428571428572
variable AB9eD equal 0.5866857142857144
```

- **`fingerprints_barrier.lmp`**
```bash
# values in kcal/mol
variable BB1eB equal -5.051 
variable BB2eB equal -2.038
variable BB3eB equal -4.933
variable BB1eD equal 4.002
variable BB2eD equal -2.03
variable BB3eD equal -2.196
variable AA1eB equal 0.371
variable AA2eB equal -2.107
variable AA3eB equal -2.369
variable AA4eB equal -1.975
variable AA5eB equal 0.205
variable AA6eB equal 0.161
variable AA7eB equal 0.166
variable AA8eB equal 0.261
variable AA9eB equal -2.385
variable AA1eD equal 2.181
variable AA2eD equal -0.34
variable AA3eD equal -0.42
variable AA4eD equal -0.955
variable AA5eD equal 3.832
variable AA6eD equal 16.039
variable AA7eD equal 11.904
variable AA8eD equal 12.272
variable AA9eD equal -0.118   
variable AB1eB equal -18.932
variable AB2eB equal -5.355
variable AB3eB equal -3.170
variable AB4eB equal 1.068
variable AB5eB equal -6.192
variable AB6eB equal 1.776
variable AB7eB equal 0.408
variable AB8eB equal -4.765
variable AB9eB equal -3.997
variable AB1eD equal -4.172 
variable AB2eD equal 16.652
variable AB3eD equal 4.806
variable AB4eD equal 17.661
variable AB5eD equal 14.648
variable AB6eD equal 0.506
variable AB7eD equal 17.235
variable AB8eD equal 13.95
variable AB9eD equal 10.428
```

- **`fingerprints_diameter.lmp`**
```bash
# values in Angstroms
set atom 1 diameter 5.97750435
set atom 2 diameter 7.527140692
set atom 3 diameter 7.555461624
set atom 4 diameter 7.55813719
set atom 5 diameter 7.577145998
set atom 6 diameter 7.559808456
set atom 7 diameter 7.559362858
set atom 8 diameter 7.496453246
set atom 9 diameter 7.535558436
set atom 10 diameter 7.562258312
set atom 11 diameter 7.552560956
set atom 12 diameter 8.62901177
set atom 13 diameter 8.585012618
set atom 14 diameter 8.637553154
set atom 15 diameter 8.640879718
set atom 16 diameter 8.62370761
set atom 17 diameter 8.657389314
set atom 18 diameter 8.67273602
set atom 19 diameter 8.645737018
set atom 20 diameter 8.657304374
set atom 21 diameter 9.525393326
set atom 22 diameter 9.543391444
set atom 23 diameter 9.552469752
```

- **`fingerprints_aij.lmp`**
```bash
lines = []
lines.append("# values in kcal/mol")
lines.append("variable V1 equal 1")
lines.append("variable V2 equal 1")
# Pattern: variable a_i_j equal ${V1}+${V2}*${X_i_j}
for i in range(1, 24):
    for j in range(1, 24):
        lines.append(f"variable a_{i}_{j} equal ${{V1}}+${{V2}}*${{X_{i}_{j}}}")
content = "\n".join(lines) + "\n"
with open("fingerprints_aij.lmp", "w") as f:
    f.write(content)
```

- **`fingerprints_xij.lmp`**
```bash
import numpy as np
# values (in kcal/mol)
X_matrix = np.array([
    [0.0, 1.59, 4.95, 9.07, 6.0, 8.96, 4.23, 7.94, 6.68, 2.8, 7.61, 9.89, 10.76, 15.58, 8.46, 11.62, 7.77, 4.21, 19.98, 4.52, 20.75, 8.78, 16.05],
    [1.55, 0.0, 4.82, 12.38, 6.12, 9.55, 3.98, 8.62, 10.13, 4.16, 7.05, 5.55, 6.74, 10.81, -1.59, 7.65, 4.47, 2.53, 15.69, 2.73, 17.25, 3.27, 7.3],
    [4.94, 5.23, 0.0, 5.2, 3.84, 4.25, 0.67, 0.6, 1.54, 2.2, 4.04, 3.79, 6.1, 13.81, 8.01, 12.42, 0.01, 2.01, 18.84, 4.31, 16.5, 10.01, 14.53],
    [9.16, 12.38, 5.05, 0.0, 2.82, 1.16, 2.34, 1.35, 1.62, 5.9, 3.9, 14.16, 12.59, 20.25, 17.86, 16.09, 3.1, 2.77, 26.37, 12.55, 20.6, 19.69, 23.91],
    [6.16, 6.22, 3.68, 2.87, 0.0, 2.65, -1.7, 2.41, 1.75, 1.87, 3.62, 8.4, 6.25, 15.1, 7.06, 12.28, 3.78, 0.79, 18.46, 7.51, 17.12, 12.38, 14.95],
    [9.03, 9.59, 4.55, 1.57, 1.97, 0.0, 2.92, 1.9, 3.51, 5.87, 2.38, 13.42, 12.88, 17.85, 14.22, 15.01, -0.11, 1.5, 20.73, 10.41, 21.84, 15.7, 18.35],
    [4.19, 3.98, 0.14, 2.43, -1.81, 2.47, 0.0, 2.68, 2.81, 0.34, 2.44, 7.69, 5.74, 9.74, 7.05, 6.17, 2.1, -0.65, 11.58, 2.84, 16.77, 6.2, 10.53],
    [8.01, 8.58, 0.19, 1.37, 2.14, 1.83, 2.7, 0.0, 2.83, 5.85, 3.36, 10.53, 10.39, 14.71, 12.1, 9.75, 5.99, 1.41, 17.45, 7.41, 20.72, 12.02, 15.29],
    [6.63, 10.28, 1.15, 1.26, 1.64, 3.84, 2.45, 2.67, 0.0, 3.48, 4.65, 11.82, 9.27, 14.53, 9.14, 10.89, 2.53, 1.86, 16.32, 5.77, 18.14, 9.21, 13.67],
    [2.8, 4.16, 2.2, 5.9, 1.87, 5.87, 0.34, 5.85, 3.48, 0.0, 2.87, 7.12, 6.54, 11.23, 5.98, 7.65, 1.23, 1.54, 13.21, 3.12, 14.56, 6.78, 9.87],
    [7.61, 7.05, 4.04, 3.9, 3.62, 2.38, 2.44, 3.36, 4.65, 2.87, 0.0, 8.92, 7.45, 12.87, 6.34, 9.12, 1.89, 2.34, 15.43, 4.56, 16.78, 8.23, 11.45],
    [9.89, 5.55, 3.79, 14.16, 8.4, 13.42, 7.69, 10.53, 11.82, 7.12, 8.92, 0.0, 4.56, 8.76, 3.21, 5.67, 6.12, 4.34, 10.89, 3.45, 12.34, 5.67, 8.9],
    [10.76, 6.74, 6.1, 12.59, 6.25, 12.88, 5.74, 10.39, 9.27, 6.54, 7.45, 4.56, 0.0, 6.54, 2.34, 4.56, 5.12, 3.45, 9.23, 2.78, 10.45, 4.23, 7.67],
    [15.58, 10.81, 13.81, 20.25, 15.1, 17.85, 9.74, 14.71, 14.53, 11.23, 12.87, 8.76, 6.54, 0.0, 4.56, 6.78, 8.12, 6.34, 12.45, 5.67, 14.23, 7.89, 10.34],
    [8.46, -1.59, 8.01, 17.86, 7.06, 14.22, 7.05, 12.1, 9.14, 5.98, 6.34, 3.21, 2.34, 4.56, 0.0, 2.34, 4.12, 2.67, 8.45, 2.12, 9.78, 3.45, 6.23],
    [11.62, 7.65, 12.42, 16.09, 12.28, 15.01, 6.17, 9.75, 10.89, 7.65, 9.12, 5.67, 4.56, 6.78, 2.34, 0.0, 3.45, 2.89, 7.89, 2.34, 8.67, 3.78, 5.89],
    [7.77, 4.47, 0.01, 3.1, 3.78, -0.11, 2.1, 5.99, 2.53, 1.23, 1.89, 6.12, 5.12, 8.12, 4.12, 3.45, 0.0, 1.23, 9.12, 1.89, 10.23, 3.45, 6.78],
    [4.21, 2.53, 2.01, 2.77, 0.79, 1.5, -0.65, 1.41, 1.86, 1.54, 2.34, 4.34, 3.45, 6.34, 2.67, 2.89, 1.23, 0.0, 7.45, 1.34, 8.56, 2.67, 5.12],
    [19.98, 15.69, 18.84, 26.37, 18.46, 20.73, 11.58, 17.45, 16.32, 13.21, 15.43, 10.89, 9.23, 12.45, 8.45, 7.89, 9.12, 7.45, 0.0, 6.78, 2.34, 5.67, 3.45],
    [4.52, 2.73, 4.31, 12.55, 7.51, 10.41, 2.84, 7.41, 5.77, 3.12, 4.56, 3.45, 2.78, 5.67, 2.12, 2.34, 1.89, 1.34, 6.78, 0.0, 7.89, 2.34, 5.12],
    [20.75, 17.25, 16.5, 20.6, 17.12, 21.84, 16.77, 20.72, 18.14, 14.56, 16.78, 12.34, 10.45, 14.23, 9.78, 8.67, 10.23, 8.56, 2.34, 7.89, 0.0, 4.56, 2.34],
    [8.78, 3.27, 10.01, 19.69, 12.38, 15.7, 6.2, 12.02, 9.21, 6.78, 8.23, 5.67, 4.23, 7.89, 3.45, 3.78, 3.45, 2.67, 5.67, 2.34, 4.56, 0.0, 3.12],
    [16.05, 7.3, 14.53, 23.91, 14.95, 18.35, 10.53, 15.29, 13.67, 9.87, 11.45, 8.9, 7.67, 10.34, 6.23, 5.89, 6.78, 5.12, 3.45, 5.12, 2.34, 3.12, 0.0]
])
lines = []
lines.append("# values in kcal/mol")
for i in range(1, 24):
    for j in range(1, 24):
        value = X_matrix[i-1, j-1]
        lines.append(f"variable X_{i}_{j} equal {value}")
content = "\n".join(lines) + "\n"
with open("fingerprints_xij.lmp", "w") as f:
    f.write(content)
```