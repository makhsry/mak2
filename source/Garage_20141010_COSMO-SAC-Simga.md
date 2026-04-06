## COSMO-SAC Sigma Profile Generator

This is a MATLAB code designed to process raw quantum mechanical (QM) surface data into **sigma-profiles**. These profiles represent the probability distribution of segment surface areas as a function of their local charge density, a critical input for calculating activity coefficients in chemical mixtures. 

An **`html`** version of this document is available [**here**](Garage_20141010_COSMO-SAC-Simga.html).

The generator transforms discrete surface segment data (positions and charges) into a smoothed, continuous distribution. It accounts for neighbor-averaging effects to ensure the resulting profile accurately reflects the molecular surface environment.  

To account for the influence of adjacent segments, the "raw" segment charge density (sigma<sub>i</sub>) is converted into a smoothed "effective" charge density (sigma<sub>new,i</sub>). The code uses a distance-weighted Gaussian averaging function:  

σ<sub>new,i</sub> = (∑<sub>j</sub> σ<sub>j</sub>
( (r<sub>j</sub><sup>2</sup> R<sub>eff</sub><sup>2</sup>) / (r<sub>j</sub><sup>2</sup> + R<sub>eff</sub><sup>2</sup>) )
exp( − d<sub>ij</sub><sup>2</sup> / (r<sub>j</sub><sup>2</sup> + R<sub>eff</sub><sup>2</sup>) )
)/(∑<sub>j</sub>( (r<sub>j</sub><sup>2</sup> R<sub>eff</sub><sup>2</sup>(r<sub>j</sub><sup>2</sup> + R<sub>eff</sub><sup>2</sup>) ) / (r<sub>j</sub><sup>2</sup> + R<sub>eff</sub><sup>2</sup>) )
exp( − d<sub>ij</sub><sup>2</sup> / (r<sub>j</sub><sup>2</sup> + R<sub>eff</sub><sup>2</sup>)))

where:    
- d<sub>ij</sub> is the Euclidean distance between segments calculated from Cartesian coordinates (x, y, z).
- r<sub>j</sub> is the radius of the segment, derived from its surface area (RAD = sqrt(Area/π)).
- R<sub>eff</sub> is the fixed effective averaging radius (0.8176 Å).

The smoothed charge densities (sigma<sub>new</sub>) are categorized into discrete bins to form the sigma-profile P(sigma).
- **Range:** The code defines a density spectrum from -0.025 to 0.025 e/Å<sup>2</sup>.
- **Binning Logic:** For every segment falling within a specific charge density interval, its area is weighted and summed:
  
A(sigma<sub>bin</sub>) = sum<sub>i in bin</sub> | sigma<sub>new, i</sub> - sigma<sub>new, i+1</sub> | * Area<sub>i</sub>

| File | Function | Description |
| :--- | :--- | :--- |
| [`SimgaProfileCalculator.m`](Garage_20141010_COSMO-SAC-Simga_SimgaProfileCalculator.m) | **Core Engine** | The main routine that calculates distances, performs Gaussian averaging, and yields the final profile. |
| [`IOinDataBase.m`](Garage_20141010_COSMO-SAC-Simga_IOinDataBase.m) | **Data Handler** | Manages input/output by reading QM data from `inputQM.xlsx` and writing processed profiles. |
| [`SortSimgaProfile.m`](Garage_20141010_COSMO-SAC-Simga_SortSimgaProfile.m) | **Binning Logic** | Discretizes the continuous surface data into the specific $\sigma$-density intervals used by COSMO-SAC. |
| [`ConvertAU2A.m`](Garage_20141010_COSMO-SAC-Simga_ConvertAU2A.m) | **Unit Converter**| Converts spatial coordinates from Atomic Units (au) to Angstroms (Å) and calculates radii. |
|[`inputQM.xlsx`](Garage_20141010_COSMO-SAC-Simga_inputQM.xlsx) | **Input Data** | The input file containing the QM data. |

The Excel file named `inputQM.xlsx`, each sheet should correspond to a unique compound and contain:
- **Columns C, D, E:** X, Y, Z coordinates (Atomic Units).    
- **Column G:** Segment Area.    
- **Column H:** Charge per Area (Surface Charge Density).     

Call the calculator function from the MATLAB command window:
```matlab
% Replace 'CompoundName' with the specific sheet name in your Excel file
[Density, Profile, Vol] = SimgaProfileCalculator('CompoundName');
```
