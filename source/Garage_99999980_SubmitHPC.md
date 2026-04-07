## HPC Job Management Tools

This script is a **`Bash`**-based utility designed to automate the configuration and submission of [**`Slurm`**](https://slurm.schedmd.com/)-managed jobs. It handles cluster-specific hardware architectures, resource allocation logic, and job recovery. 

The **`bash`** script is available [**here**](Garage_99999980_SubmitHPC.sh). 
An **`.html`** version is available [**here**](Garage_99999980_SubmitHPC.html). 

It is specifically tailored for [**COMSOL Multiphysics**](https://www.comsol.com/products/multiphysics/) simulations. The script primaryly manages the entire workflow from environment validation to job submission on various [**Canadian HPC clusters**](https://www.alliancecan.ca/en/about) (_before their migration to new systems_).  

The script builds the final **COMSOL call** as a concatenated string of the following components:      

```bash      
${CALL_COMSOL_AS} batch -mpibootstrap slurm \
    -inputfile ${inputmph} \
    -outputfile ${outputmph} \
    -batchlog ${logfilepath} \
    -tmpdir ${TMPDIR} \
    -recoverydir ${RECDIR} \
    -alivetime 15 \
    ${COMSOL_EXTRA_} \    # Integrated study tags
    ${COMSOL_CONTINUE_} \ # Recovery flags
    ${COMSOL_PARAMS_} \   # Parametric sweep arguments
    ${COMSOL_METHOD_}     # Custom method calls
```

**Interactive Usage Walkthrough (Step-by-Step)**      
- **Prepare Workspace**: Place the `.mph` file in the parent directory. Script creates a subdirectory for the script.
- **Identity Confirmation**: Confirm the detected `username`. If incorrect, enter your Slurm-associated username manually.
- **Account Selection**: Provide the exact Slurm `allocation` name (e.g., `st-amadiseh-1` for UBC or `def-madiseh-ab` for CC). The script will verify this `allocation` against `sacctmgr`.
- **Cluster Discovery**: The script automatically detects the `cluster` (e.g., Narval). Confirm this to load the appropriate hardware menu.
- **Configure Monitoring**:
- - **Option 1**: Manual `wall-time` (e.g., `24-00` for 24 hours).
- - **Option 2 (Watch Mode)**: Manual `wall-time`, but enables automatic resume logic if the job fails due to timeout.
- **Select Hardware Profile**: Pick an `option` from the menu (e.g., Option `3` for high-memory). Ensure you note if the option includes `GPU` support as identified in the `isGPU` column.
- **Finalize & Submit**:
- - Provide the exact input `filename` (must be in the parent directory).
- - Select a `study tag` (e.g., `std1`) or type `no` for a full problem solve.
- - Review the `test-only` submission `feedback`. If successful, the job will be `queued` immediately.

**Cluster Options**    

**- Sockeye (UBC ARC)**   

| Option | RAM/CPU | M<sub>total</sub> | N<sub>cpu</sub> | Arch | isGPU | Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 6 GB | 192G | 32 | Skylake | | |
| 2 | 12 GB | 384G | 32 | Skylake | | |
| 3 | 24 GB | 768G | 32 | Skylake | | |
| 4 | 8 GB | 192G | 24 | Skylake | Yes | Not supported yet |
| 5 | 4.8 GB | 192G | 40 | Cascade | | |
| 6 | 9.6 GB | 384G | 40 | Cascade | | |
| 7 | 19.2 GB | 768G | 40 | Cascade | | |
| 8 | 8 GB | 192G | 24 | Cascade | Yes | Not supported yet |
| Login | 8 GB | 192G | 16 | Skylake | | login node |
| Data | 8 GB | 192G | 16 | Skylake | | data node |

**- Narval (Compute Canada)**       

| Option | RAM/CPU | M<sub>total</sub> | N<sub>cpu</sub> | Arch | isGPU | Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 3.8 GB | 249G | 64 | Rome | | |
| 2 | 31.3 GB | 2009G | 64 | Rome | | |
| 3 | 62.5 GB | 4000G | 64 | Rome | | |
| 4 | 7.7 GB | 498G | 48 | Milan | Yes | Not supported yet |

**- Beluga (Compute Canada)**      

| Option | RAM/CPU | M<sub>total</sub> | N<sub>cpu</sub> | Arch | isGPU | Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 2.3 GB | 92G | 40 | Skylake | | |
| 2 | 4.65 GB | 186G | 40 | Skylake | | |
| 3 | 18.8 GB | 752G | 40 | Skylake | | |
| 4 | 4.65 GB | 186G | 40 | Skylake | Yes | Not supported yet |

**- Cedar (Compute Canada)**      

| Option | RAM/CPU | M<sub>total</sub> | N<sub>cpu</sub> | Arch | isGPU | Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 3.9 GB | 125G | 32 | Broadwell | | |
| 2 | 7.8 GB | 250G | 32 | Broadwell | | |
| 3 | 15.6 GB | 502G | 32 | Broadwell | | |
| 4 | 47.18 GB | 1510G | 32 | Broadwell | | |
| 5 | 125 GB | 4000G | 32 | EPYC | | |
| 6 | 150 GB | 6000G | 40 | Cascade | | |
| 7 | 5.2 GB | 125G | 24 | Broadwell | Yes | Not supported yet |
| 8 | 10.4 GB | 250G | 24 | Broadwell | Yes | Not supported yet |
| 9 | 5.8 GB | 187G | 32 | Cascade | Yes | Not supported yet |
| 10 | 3.8 GB | 187G | 48 | Skylake | | |
| 11 | 3.8 GB | 187G | 48 | Cascade | | |

**- Graham (Compute Canada)**      

| Option | RAM/CPU | M<sub>total</sub> | N<sub>cpu</sub> | Arch | isGPU | Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 3.9 GB | 125G | 32 | Broadwell | | |
| 2 | 15.6 GB | 502G | 32 | Broadwell | | |
| 3 | 7.8 GB | 250G | 32 | Broadwell | | |
| 4 | 47.2 GB | 3022G | 64 | Broadwell | | |
| 5 | 3.8 GB | 124G | 32 | Broadwell | Yes | Not supported yet |
| 6 | 6.6 GB | 187G | 28 | Skylake | Yes | Not supported yet |
| 7 | 9.4 GB | 377G | 40 | Cascade | Yes | Not supported yet |
| 8 | 11.6 GB | 187G | 16 | Skylake | Yes | Not supported yet |
| 9 | 4.25 GB | 187G | 44 | Cascade | Yes | Not supported yet |
| 10 | 4.25 GB | 187G | 44 | Cascade | | |
| 11 | 15.6 GB | 2000G | 128 | EPYC | Yes | Not supported yet |
| 12 | 8 GB | 256G | 32 | Cascade | Yes | Not supported yet |
| 13 | 1.95 GB | 125G | 64 | EPYC | Yes | Not supported yet |

**- Niagara (Compute Canada)**      

*Preset Configuration*: 4.7 GB/CPU (approx 188G/40cores) on Skylake architecture.      

**Environment Variables**

| Flag/Control | Cluster | Action |
| :--- | :--- | :--- |
| `ulimit -s unlimited` | ALL | Removes memory stack limits for MPI safety. |
| `I_MPI_COLL_EXTERNAL=0`| Narval | Disables external MPI collective communication for performance. |
| `CCEnv` / `StdEnv` | CC | Dynamically loads the Compute Canada standard software environments. |
| `openjdk/11.0.20.1_1` | Sockeye| Loads the required Java runtime for the COMSOL backend. |