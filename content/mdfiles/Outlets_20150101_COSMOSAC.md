### COSMO-SAC Activity Coefficient Model

This is a suite of MATLAB code for the **COSMO-SAC (COSMO Segment Activity Coefficient)** model. 

- An **`.html`** version of the calculator can be found [**here**](tools/COSMOSAC_Calculator.html).
- Source **`MATLAB`** code can be found [**here**](tools/COSMOSAC.m), with a [**required input file**](tools/COSMOSAC_inputQM.xlsx).

**Usage Instructions**

- The Excel file ([**`inputQM.xlsx`**](tools/COSMOSAC_inputQM.xlsx)) must have sheets named after your **`components`** (e.g., '67-63-0-2d' or 'Z1') containing the required QM output data.
- Set your desired **`SYSTEMP`** (Temperature in **Kelvin**).
- Update **`ListCOMP`** with the sheet names from your **`inputQM.xlsx`** file.
- Run the script **`eqCOSMO.m`**.

**Outputs**

- **`sProfiles.xlsx`**: Stores the calculated **`sigma-densities`** and **`profiles`** for each component.
- **`MixGamma.xlsx`**: Stores the final matrix containing **`mole fractions (x)`**, **`activity coefficients (γ)`**, and **`ln γ`**.

![COSMO-SAC Activity Coefficient Model](images/tool_COSMOSAC.png)