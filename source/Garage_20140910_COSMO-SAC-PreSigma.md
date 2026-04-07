## COSMO-SAC Sigma Profile Processor

This is a suite of `Shell` scripts designed to automate the extraction and processing of quantum mechanical (QM) data from **DMol3** output files (specifically **.cosmo** and **.outmol**) into **sigma-profiles** for **COSMO-SAC thermodynamic modeling**. 

**How to Use**    
- Set the **Compound Name** by editing the scripts to update the **`compound`** variable (e.g., `compound='75-85-4-2d'`).     
- Make **Executable**: `chmod +x *.sh`
- Run the **Pipeline** 
    - first [**`1_Dmol3COSMO.sh`**](Garage_20140910_COSMO-SAC-PreSigma_1_Dmol3COSMO.sh): Extracts segment geometry and raw charges from `.cosmo` files. 
    - then [**`2_Dmol3OUTMOL.sh`**](Garage_20140910_COSMO-SAC-PreSigma_2_Dmol3OUTMOL.sh): Extracts cavity volume and average COSMO data from `.outmol` files. 
    - then [**`3_sProfile.sh`**](Garage_20140910_COSMO-SAC-PreSigma_3_sProfile.sh): Performs the N<sup>2</sup>-complexity Gaussian averaging of surface charges. 
    - and finally [**`SortS.sh`**](Garage_20140910_COSMO-SAC-PreSigma_SortS.sh): Generates the P(σ) vs σ distribution for thermodynamic modeling. 

The scripts generate several intermediate such as `.cosmo.xyz` files and a final sigma-profile:
- `${compound}.cosmo.SigmaNonSrt`: The smoothed charge densities.
- `${compound}.cosmo.SigmaSrt`: The charge density bin identifiers.
- `${compound}.cosmo.PSigmaSrt`: The final sigma-profile area values.

Coordinates are converted from Atomic Units (au) to Angstroms (Å) by `au = 0.529177249 Å`.