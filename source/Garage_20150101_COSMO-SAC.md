## COSMO-SAC Activity Coefficient Model in MATLAB

This is a MATLAB implementation of the **COSMO-SAC (COSMO Segment Activity Coefficient)** model. The code calculates the thermodynamic activity coefficients of components in chemical mixtures based on their molecular surface charge distributions, known as sigma-profiles.

The model predicts the non-ideal behavior of liquid mixtures by analyzing the interaction energies between molecular surface segments. It accounts for:
* **Electrostatic Misfit Energy**: Interactions between segments with different charge densities.
* **Hydrogen Bonding**: Specific attractions between highly polar surface regions based on a cutoff value.
* **Combinatorial Effects**: Differences in molecular size and shape using the Staverman-Guggenheim term.

The calculation follows a multi-step thermodynamic workflow derived from the source code:

**Sigma Profile Calculation (sigma-profile)**      
For each molecule, the code calculates the surface area distribution as a function of charge density sigma. The local segment charge is averaged over a circular area to account for neighbor effects using the following logic: 

σ<sub>new, i</sub> = 
(&sum;<sub>j</sub> σ<sub>j</sub> · (RAD<sub>j</sub><sup>2</sup> REFF<sup>2</sup> / (RAD<sub>j</sub><sup>2</sup> + REFF<sup>2</sup>)) · exp( - Term1<sup>2</sup> / (RAD<sub>j</sub><sup>2</sup> + REFF<sup>2</sup>) )) /(&sum;<sub>j</sub> (RAD<sub>j</sub><sup>2</sup> REFF<sup>2</sup> / (RAD<sub>j</sub><sup>2</sup> + REFF<sup>2</sup>)) · exp( - Term1<sup>2</sup> / (RAD<sub>j</sub><sup>2</sup> + REFF<sup>2</sup>) ))

Where:
* **Term1** is the Euclidean distance between surface segments i and j.
* **REFF** is the effective averaging radius (0.817642 Å).

**Interaction Energy (Δw)**      
The exchange energy between two segments i and j is calculated as:

Δw<sub>ij</sub> = 
(α'/2) · (σ<sub>i</sub> + σ<sub>j</sub>)<sup>2</sup> + c<sub>hb</sub>· max(0, σ<sub>acc</sub> - σ<sub>hb</sub>) · min(0, σ<sub>don</sub> + σ<sub>hb</sub>)

Where:
* **Misfit term**: Determined by `ALPHAPRIME` and the sum of charge densities.
* **HB term**: Active when charge densities exceed the threshold `SIGMAHB` (0.0084 e/Å²).

**Segment Activity Coefficients (Γs)**     
The activity coefficient of a segment is solved iteratively until the change is less than 10<sup>-6</sup>:

ln Γ<sub>s</sub>(σ<sub>i</sub>) = -ln [ &sum;<sub>j</sub> P(σ<sub>j</sub>) Γ<sub>s</sub>(σ<sub>j</sub>) exp(-Δw<sub>ij</sub> / RT) ]

The code computes this for both **pure species** (`SEGGAMMAPR`) and the **mixture** (`SEGGAMMA`).

**Total Activity Coefficient (γ)**     
The final activity coefficient for component n is the exponential sum of the residual and combinatorial parts:

γ<sub>n</sub> = exp(ln γ<sub>n</sub><sup>res</sup> + ln γ<sub>n</sub><sup>sg</sup>)

Where:
* **Residual**: Calculated by summing the difference between mixture and pure segment activity coefficients weighted by the sigma profile.
* **Combinatorial (SG)**: Uses `COORD` (coordination number), `RNORM` (normalized volume), and `QNORM` (normalized area) parameters.

Source code:      

| File | Description |
| :--- | :--- |
| [`eqCOSMO.m`](Garage_20150101_COSMO-SAC_eqCOSMO.m) | Main script for Two Phase Equilibrium; defines temperature and components. |
| [`Binary.m`](Garage_20150101_COSMO-SAC_Binary.m) | Primary function calculating mole fractions, pure/mixture segment gammas, and final γ. |
| [`SimgaProfileCalculator.m`](Garage_20150101_COSMO-SAC_SimgaProfileCalculator.m) | Manages the averaging of surface charges and calls the sorting logic. |
| [`Library.m`](Garage_20150101_COSMO-SAC_Library.m) | Reads geometry, volume, and charge data from `inputQM.xlsx`. |
| [`paraCOSMO.m`](Garage_20150101_COSMO-SAC_paraCOSMO.m) | Provides universal constants (R, c<sub>hb</sub>, σ<sub>hb</sub>, α, etc.). |
| [`SortSimgaProfile.m`](Garage_20150101_COSMO-SAC_SortSimgaProfile.m) | Bins segment data into a discrete density distribution from -0.025 to 0.025. |
| [`ConvertAU2A.m`](Garage_20150101_COSMO-SAC_ConvertAU2A.m) | Converts coordinates from Atomic Units to Angstroms. |
| [`inputQM.xlsx`](Garage_20150101_COSMO-SAC_inputQM.xlsx) | Input file for the COSMO-SAC model. |


**Usage Instructions**        
- The Excel file (`inputQM.xlsx`) must have sheets named after your components (e.g., '67-63-0-2d' or 'Z1') containing the required QM output data.

**Execution**      
- Open `eqCOSMO.m`.
- Set your desired **SYSTEMP** (Temperature in K).
- Update **ListCOMP** with the sheet names from your Excel file.
- Run the script.

**Outputs**
- **`sProfiles.xlsx`**: Stores the calculated sigma-densities and profiles for each component.
- **`MixGamma.xlsx`**: Stores the final matrix containing mole fractions (x), activity coefficients (γ), and ln γ.
