## Falling Film Mass Transfer & Penetration Theory

In the paper [**Revisiting ‘penetration depth’ in falling film mass transfer**](https://www.sciencedirect.com/science/article/pii/S0263876219305994), we calculated mass transfer characteristics in falling liquid films. We compared the **Infinite Penetration** (Higbie's theory) and **Finite Penetration** models to determine how deep a solute penetrates a moving film under various physical conditions.        

![Falling Film Mass Transfer & Penetration Theory](Publications_20200101_jChERD.png)
 
Two python scripts are provided to calculate the mass transfer characteristics in falling liquid films. The scripts are written in Python 3.x and use the NumPy library for numerical calculations. The scripts solve the governing equations for convective mass transfer in a laminar falling film. One analyzes how different diffusion coefficients impact the penetration depth and flux [click here (save as .py)](Publications_20200101_jChERD_varD.py). The other analyzes the effect of film flow rate on mass transfer efficiency [click here (save as .py)](Publications_20200101_jChERD_varG.py).

**Film Hydrodynamics**
The film thickness (δ) and average velocity (u) are calculated based on the film flow rate (Γ) and fluid properties (density ρ, viscosity μ):

<p>δ = (3μΓ / ρ²g)<sup>1/3</sup></p>
<p>u = Γ / (ρδ)</p>

**Infinite Penetration Model**
For short contact times or thick films, the solute is assumed not to reach the wall. The local mass transfer coefficient (k<sub>c</sub>) is:

<p>k<sub>c</sub>(y) = (3uD / 2πy)<sup>1/2</sup></p>

**Finite Penetration Model**
When the solute reaches the wall (finite depth), the concentration profile is solved using a Fourier series expansion. The code determines a characteristic parameter (ξ) by solving for the root of the error function:

<p>Error = ( Σ<sub>n=0</sub><sup>∞</sup> <sup>(-1)<sup>n</sup></sup>&frasl;<sub>2n+1</sub> exp( - [ <sup>(2n+1)π</sup>&frasl;<sub>2ξ</sub> ]<sup>2</sup> &middot; <sup>Dy</sup>&frasl;<sub>u</sub> ) ) - π&frasl;4</p>

**Mass Flux Calculation (N<sub>A</sub>)**
The local mass flux at the interface is determined by:

<p>N<sub>A</sub> = k<sub>c</sub> &middot; (c<sub>Ai</sub> - c<sub>A0</sub>)</p>

where c<sub>Ai</sub> is the interfacial concentration and c<sub>A0</sub> is the bulk concentration.     

**Usage Instructions**    
1. Open the desired script.
2. Adjust the **Test Data** section to match your physical system:

```python
L = 1         # Wall length (m)
gamma = 0.05  # Film flow rate (kg/m.s)
cAi = 0.0366  # Interfacial concentration
``` 