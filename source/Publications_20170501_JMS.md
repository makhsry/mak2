## Thermokinetic Model of Phase Inversion

In the paper [**On the search of rigorous thermo-kinetic model for wet phase inversion technique**](https://www.sciencedirect.com/science/article/pii/S0376738817306889), we developed a rigorous thermo-kinetic model for the wet phase inversion process, with special emphasis on the role of the diffusion-thermo effect at the interface. The model provides a comprehensive mathematical derivation and mapping of the logic implemented in this phase inversion simulation project.   

![Thermokinetic Model of Phase Inversion](Publications_20170501_JMS.png)

**System Constants & Parameters**
The physical constants are defined in `CONSTANTS.m`. For the default Water (1) / Acetone (2) / Polymer (3) system:

| Constant | Description | Value |
| :--- | :--- | :--- |
| ρ<sub>01</sub> | Density of Water | 1.0 g/cm³ |
| ρ<sub>02</sub> | Density of Acetone | 0.7857 g/cm³ |
| ρ<sub>03</sub> | Density of Polymer | 1.31 g/cm³ |
| M<sub>w1</sub> | Molecular weight (nonsolvent) | 18.0 g/mol |
| M<sub>w2</sub> | Molecular weight (solvent) | 58.08 g/mol |
| M<sub>w3</sub> | Molecular weight (polymer) | 40,000 g/mol |
| v<sub>i</sub> | Specific volume of component $i$ | $1/\rho_{0i}$ |
| V<sub>i</sub> | Molar volume of component $i$ | $v_i \cdot M_{wi}$ |

**Solution Properties** ([`DENSTY.m`](Publications_20170501_JMS_DENSTY.m) & [`PHIs.m`](Publications_20170501_JMS_PHIs.m))

**- Mixture Density**
The density ρ is calculated using a mole-fraction based mixing rule from the equation of state:      

rρ = ω<sub>1</sub> · ((ρ<sub>03</sub> − ρ<sub>01</sub>) / (ρ<sub>01</sub>ρ<sub>03</sub>)) + ω<sub>2</sub> · ((ρ<sub>03</sub> − ρ<sub>02</sub>) / (ρ<sub>02</sub>ρ<sub>03</sub>)) + 1 / ρ<sub>03</sub>            

ρ = 1 / (rρ)         

**- Volume Fraction Conversion**
The volume fractions φ are converted from mass fractions ω using the following logic:

D = α ω<sub>1</sub> + β ω<sub>2</sub> + γ           

Where:
- α = V<sub>1</sub>/M<sub>w1</sub> - V<sub>3</sub>/M<sub>w3</sub>       
- β = V<sub>2</sub>/M<sub>w2</sub> - V<sub>3</sub>/M<sub>w3</sub>         
- γ = V<sub>3</sub>/M<sub>w3</sub>        

Then:

φ<sub>1</sub> = (V<sub>1</sub>/M<sub>w1</sub>) ω<sub>1</sub> / D            
φ<sub>2</sub> = (V<sub>2</sub>/M<sub>w2</sub>) ω<sub>2</sub> / D                
φ<sub>3</sub> = (V<sub>3</sub>/M<sub>w3</sub>) (1 − ω<sub>1</sub> − ω<sub>2</sub>) / D           

**Thermodynamic Logic** ([`FLORYHOGGINSCOEFF.m`](Publications_20170501_JMS_FLORYHOGGINSCOEFF.m) & [`FGcomponents.m`](Publications_20170501_JMS_FGcomponents.m))      

**- Flory-Huggins Interaction Parameters**
Parameters G<sub>ij</sub> are concentration-dependent. Let u<sub>2</sub> be the solvent volume fraction on a polymer-free basis: u<sub>2</sub> = \frac{\phi_2}{\phi_1 + \phi_2}.

**- Interaction G<sub>12</sub> (Nonsolvent-Solvent):**           
G<sub>12</sub> = 0.661 + (0.417 / (1 − 0.755 u<sub>2</sub>))              
∂G<sub>12</sub>/∂u<sub>2</sub> = (0.417 · 0.755) / (1 − 0.755 u<sub>2</sub>)<sup>2</sup>
  
**- Interaction G<sub>23</sub> (Solvent-Polymer):**           
G<sub>23</sub> = 0.535 + 0.11 \phi_3      
∂G<sub>23</sub>/∂\phi<sub>3</sub> = 0.11
  
**- Interaction G<sub>13</sub> (Nonsolvent-Polymer):**           
G<sub>13</sub> = 1.4

**- Thermodynamic Gains (Q<sub>1</sub>, Q<sub>2</sub>, S<sub>1</sub>, S<sub>2</sub>)**
These terms represent the derivatives of chemical potentials ∂μ<sub>i</sub>/∂φ<sub>j</sub> (excluding the RT factor):  

Q<sub>1</sub> =
1/φ<sub>1</sub> − 1 + V<sub>13</sub> + φ<sub>2</sub>(V<sub>12</sub>G<sub>23</sub> − G<sub>12</sub>) − (φ<sub>2</sub> + 2φ<sub>3</sub>)G<sub>13</sub> + (φ<sub>1</sub> − 2u<sub>2</sub>)u<sub>2</sub><sup>2</sup> (∂G<sub>12</sub>/∂u<sub>2</sub>) + 3V<sub>12</sub>φ<sub>2</sub>φ<sub>3</sub> (∂G<sub>23</sub>/∂φ<sub>3</sub>) + u<sub>1</sub>u<sub>2</sub><sup>3</sup> (∂<sup>2</sup>G<sub>12</sub>/∂u<sub>2</sub><sup>2</sup>) + V<sub>12</sub>φ<sub>2</sub>φ<sub>3</sub><sup>2</sup> (∂<sup>2</sup>G<sub>23</sub>/∂φ<sub>3</sub><sup>2</sup>)             

Q<sub>2</sub> =
−V<sub>12</sub> + V<sub>13</sub> + (φ<sub>2</sub> + φ<sub>3</sub>)(G<sub>12</sub> − G<sub>13</sub>) + V<sub>12</sub>(φ<sub>2</sub> − φ<sub>3</sub>)G<sub>23</sub> + u<sub>1</sub>u<sub>2</sub>(u<sub>2</sub> − u<sub>1</sub> − φ<sub>1</sub>) (∂G<sub>12</sub>/∂u<sub>2</sub>) + V<sub>12</sub>φ<sub>3</sub>(3φ<sub>2</sub> − φ<sub>3</sub>) (∂G<sub>23</sub>/∂φ<sub>3</sub>) − (u<sub>1</sub>u<sub>2</sub>)<sup>2</sup> (∂<sup>2</sup>G<sub>12</sub>/∂u<sub>2</sub><sup>2</sup>) + V<sub>12</sub>φ<sub>2</sub>φ<sub>3</sub><sup>2</sup> (∂<sup>2</sup>G<sub>23</sub>/∂φ<sub>3</sub><sup>2</sup>)               

S<sub>1</sub> =
−V<sub>21</sub> + V<sub>23</sub> + (φ<sub>1</sub> + φ<sub>3</sub>)(V<sub>21</sub>G<sub>12</sub> − G<sub>23</sub>) + V<sub>21</sub>(φ<sub>1</sub> − φ<sub>3</sub>)G<sub>13</sub> + V<sub>21</sub>u<sub>1</sub>u<sub>2</sub>(φ<sub>2</sub> + u<sub>2</sub> − u<sub>1</sub>) (∂G<sub>12</sub>/∂u<sub>2</sub>) + φ<sub>3</sub>(3φ<sub>2</sub> − 1) (∂G<sub>23</sub>/∂φ<sub>3</sub>) − V<sub>21</sub>(u<sub>1</sub>u<sub>2</sub>)<sup>2</sup> (∂<sup>2</sup>G<sub>12</sub>/∂u<sub>2</sub><sup>2</sup>) + φ<sub>2</sub>φ<sub>3</sub><sup>2</sup> (∂<sup>2</sup>G<sub>23</sub>/∂φ<sub>3</sub><sup>2</sup>)            

S<sub>2</sub> =
1/φ<sub>2</sub> − 1 + V<sub>23</sub> + V<sub>21</sub>φ<sub>1</sub>(G<sub>13</sub> − G<sub>12</sub>) − (φ<sub>1</sub> + 2φ<sub>3</sub>)G<sub>13</sub> + V<sub>21</sub>u<sub>1</sub><sup>2</sup>(2u<sub>1</sub> − φ<sub>2</sub>) (∂G<sub>12</sub>/∂u<sub>2</sub>) + φ<sub>3</sub>(4φ<sub>2</sub> + φ<sub>1</sub> − 2) (∂G<sub>23</sub>/∂φ<sub>3</sub>) + V<sub>21</sub>u<sub>1</sub><sup>3</sup>u<sub>2</sub> (∂<sup>2</sup>G<sub>12</sub>/∂u<sub>2</sub><sup>2</sup>) + φ<sub>2</sub>φ<sub>3</sub><sup>2</sup> (∂<sup>2</sup>G<sub>23</sub>/∂φ<sub>3</sub><sup>2</sup>)                  

**Continuity & Flux Logic ([`COEFFICIENTS.m`](Publications_20170501_JMS_COEFFICIENTS.m), [`ABCD.m`](Publications_20170501_JMS_ABCD.m), [`BDCA.m`](Publications_20170501_JMS_BDCA.m))**            
**- Kinetic Mobility** 
Friction coefficients ξ<sub>ij</sub> are calculated from self-diffusion coefficients D<sub>i</sub><sup>*</sup>, where D<sub>2</sub><sup>*</sup> is given by the solvent self-diffusion in `FRICTIONCOEF.m`.                                
ξ<sub>23</sub> = (ρ<sub>03</sub> M<sub>w3</sub>) / D<sub>2</sub><sup>*</sup>         

**- Mobility Matrix Elements ([`ABCD.m`](Publications_20170501_JMS_ABCD.m))**     
The elements A, B, C, D facilitate the inversion of the friction matrix:      
A = (ω<sub>2</sub>ξ<sub>12</sub>)/(M<sub>w2</sub>ω<sub>1</sub>) + (ξ<sub>13</sub>(1 − ω<sub>2</sub>))/(M<sub>w3</sub>ω<sub>1</sub>)            
B = ξ<sub>12</sub>/M<sub>w2</sub> − ξ<sub>13</sub>/M<sub>w3</sub>          
C = (ω<sub>1</sub>ξ<sub>12</sub>)/(M<sub>w1</sub>ω<sub>2</sub>) + (ξ<sub>23</sub>(1 − ω<sub>1</sub>))/(M<sub>w3</sub>ω<sub>2</sub>)           
D = ξ<sub>12</sub>/M<sub>w1</sub> − ξ<sub>23</sub>/M<sub>w3</sub>           

**- Reciprocal Scaling Term ([`BDCA.m`](Publications_20170501_JMS_BDCA.m))**            
CF<sub>12</sub>G<sub>12</sub> = (ω<sub>1</sub>ω<sub>2</sub>M<sub>w1</sub>M<sub>w2</sub>M<sub>w3</sub><sup>3</sup>)/(M<sub>w1</sub>M<sub>w3</sub>ξ<sub>12</sub>ξ<sub>23</sub>ω<sub>2</sub> + M<sub>w2</sub>M<sub>w3</sub>ξ<sub>13</sub>ξ<sub>12</sub>ω<sub>1</sub> + M<sub>w1</sub>M<sub>w2</sub>ξ<sub>13</sub>ξ<sub>23</sub>ω<sub>3</sub>)

**- Final Transport Coefficients ([`COEFFICIENTS.m`](Publications_20170501_JMS_COEFFICIENTS.m))**           
The final Fickian-like coefficients F<sub>1</sub>, F<sub>2</sub>, G<sub>1</sub>, G<sub>2</sub> are, where σ<sub>ij</sub> = (∂μ<sub>i</sub>)/(∂ω<sub>j</sub>) (computed in `DMiOi.m`):               
F<sub>1</sub> = CF<sub>12</sub>G<sub>12</sub> &middot; (C σ<sub>11</sub> + B σ<sub>21</sub>)         
F<sub>2</sub> = CF<sub>12</sub>G<sub>12</sub> &middot; (D σ<sub>11</sub> + A σ<sub>21</sub>)                    
G<sub>1</sub> = CF<sub>12</sub>G<sub>12</sub> &middot; (C σ<sub>12</sub> + B σ<sub>22</sub>)           
G<sub>2</sub> = CF<sub>12</sub>G<sub>12</sub> &middot; (D σ<sub>12</sub> + A σ<sub>22</sub>)         

**PDE & Velocity Execution ([`MainGUFDM.m`](Publications_20170501_JMS_MainGUFDM.m) & [`VELOCITY.m`](Publications_20170501_JMS_VELOCITY.m))**           

**- Reference Velocity**        
The center-of-mass velocity $v$ ensures volumetric consistency, where J<sub>i</sub><sup>'</sup> is the bracketed part of the flux J<sub>i</sub> = -ρ J<sub>i</sub><sup>'</sup>.             
v = ((ρ<sub>01</sub> − ρ<sub>03</sub>) / (ρ<sub>01</sub>ρ<sub>03</sub>)) J<sub>1</sub><sup>'</sup> + ((ρ<sub>02</sub> − ρ<sub>03</sub>) / (ρ<sub>02</sub>ρ<sub>03</sub>)) J<sub>2</sub><sup>'</sup>

**- Time Evolution**      
Components 1 and 2 evolve according to:         
ω<sub>i</sub><sup>t+Δt</sup> = ω<sub>i</sub><sup>t</sup> − ( (1/ρ)(∂J<sub>i</sub>/∂z) + v(∂ω<sub>i</sub>/∂z) ) Δt      

**- Spatial Discretization ([`MESHS.m`](Publications_20170501_JMS_MESHS.m))**      
The spatial derivatives are discretized using the GUFDM non-uniform grid.