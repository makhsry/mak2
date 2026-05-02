### HPC Job Management Tools

This script is a **`Bash`**-based utility designed to automate the configuration and submission of [**`Slurm`**](https://slurm.schedmd.com/)-managed jobs. It handles cluster-specific hardware architectures, resource allocation logic, and job recovery.

- **Access** an **`.html`** version [**here**](tools/SubmitHPC.html) to run it in the browser.
- **Source** `bash` code can be found [**here**](tools/SubmitHPC.sh).

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
    ${COMSOL_EXTRA_} \
    ${COMSOL_CONTINUE_} \
    ${COMSOL_PARAMS_} \
    ${COMSOL_METHOD_}
```

![HPC Job Management Tools](images/tool_SubmitHPC.png)