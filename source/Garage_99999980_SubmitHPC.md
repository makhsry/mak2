### HPC Job Management Tools

This script is a **`Bash`**-based utility designed to automate the configuration and submission of [**`Slurm`**](https://slurm.schedmd.com/)-managed jobs. It handles cluster-specific hardware architectures, resource allocation logic, and job recovery. 

- The **`bash`** script is available [**here**](Garage_99999980_SubmitHPC.sh). 
- An **`.html`** version is available [**here**](Garage_99999980_SubmitHPC.html). 

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