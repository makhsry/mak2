## COSMO-SAC Sigma Profile Processor

This is a suite of `Shell` scripts designed to automate the extraction and processing of quantum mechanical (QM) data from **DMol3** outputs (specifically **.cosmo** and **.outmol** files) into **sigma-profiles**. 

- **Set the Compound Name:** 

- Edit the scripts to update the `compound` variable (e.g., `compound='75-85-4-2d'`).     
- Make Executable: `chmod +x *.sh`
- Run the Pipeline: `./1_Dmol3COSMO.sh`, then `./2_Dmol3OUTMOL.sh`, then `./3_sProfile.sh`, then `./SortS.sh`. 

The scripts generate several intermediate `.cosmo.xyz` files and a final profile:
- `${compound}.cosmo.SigmaNonSrt`: The smoothed charge densities.
- `${compound}.cosmo.SigmaSrt`: The charge density bin identifiers.
- `${compound}.cosmo.PSigmaSrt`: The final sigma-profile area values.

| File (link) | Type | Purpose |
| :--- | :--- | :--- |
| [`1_Dmol3COSMO.sh`](Garage_20140910_COSMO-SAC-PreSigma_1_Dmol3COSMO.sh) | Bash Script | Extracts segment geometry and raw charges from `.cosmo` files. |
| [`2_Dmol3OUTMOL.sh`](Garage_20140910_COSMO-SAC-PreSigma_2_Dmol3OUTMOL.sh) | Bash Script | Extracts cavity volume and average COSMO data from `.outmol` files. |
| [`3_sProfile.sh`](Garage_20140910_COSMO-SAC-PreSigma_3_sProfile.sh) | Bash Script | Performs the N²-complexity Gaussian averaging of surface charges. |
| [`SortS.sh`](Garage_20140910_COSMO-SAC-PreSigma_SortS.sh) | Bash Script | Generates the $P(\sigma)$ vs $\sigma$ distribution for thermodynamic modeling. |

Coordinates are converted from Atomic Units (au) to Angstroms (Å) using the conversion factor au = 0.529177249 Å.