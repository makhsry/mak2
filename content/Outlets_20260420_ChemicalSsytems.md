### Chemical Reaction Systems Analyzer

A **web-based** tool for analyzing **chemical reaction systems** based atom reducndency principle. The analyzer takes a list of chemical formulas and their phases, constructs an atom-formula matrix, and computes independent chemical reactions from the null-space vectors using reduced row echelon form (RREF).

- **Access** the tool [**here**](Tools_ChemicalSystems.html).

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