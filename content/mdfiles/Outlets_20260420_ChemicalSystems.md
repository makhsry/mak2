### Chemical Reaction Systems Analyzer

A **web-based** tool for analyzing **chemical reaction systems** and **Gibbs free energy minimization**. 

This is a **demo** of the **Gibbs Reactor Module** in **CADSIM Plus (Aurel Systems Inc.)**. For the simplicity of this demo, all chemicals are treated as **ideal gases**, and their thermodynamic properties are pulled from the **Shomate** thermodynamic database provided by the **NIST**.

- **Access** the tool [**here**](_ChemicalSystems.html). (with new style [**here**](_ChemicalSystems2.html))

**Standard Chemical Input**
- Enter chemical formulas with phases (gas, liquid, solid, aqueous)
- Formulas are parsed using a periodic table (valid elements only)
- Drag-to-reorder entries

**Decomposition Pathways**
- Mark chemicals that decompose into fragments
- Add multiple fragment formulas to create different decomposition sequences
- Each pathway subtracts its fragment until any atom reaches zero
- Automatically generates intermediate compounds

**Special Chemicals**
- Add non-standard species using the pattern: `Formula^Flag(phase)`
- Example: OH radical: `OH^.(aq)` or hydrated electron: `e^-(aq)`
- Gets a unique row in the matrix for tracking

**Element Support**   
All 118 periodic table elements are supported (H through Og).

**References**    
- Gibbs Reactor Module, Aurel Systems Inc. (CADSIM Plus).
- Chemical Reaction Equilibrium Analysis: Theory and Algorithms by William R. Smith and Ronald W. Missen (1982)

![Chemical Reaction Systems Analyzer](images/Images_Outlets_20260420_ChemicalSystems.png)