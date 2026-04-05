## Falling Film Mass Transfer & Penetration Theory

In the paper [**Revisiting ‘penetration depth’ in falling film mass transfer**](https://www.sciencedirect.com/science/article/pii/S0263876219305994), we calculated mass transfer characteristics in falling liquid films. We compared the **Infinite Penetration** (Higbie's theory) and **Finite Penetration** models to determine how deep a solute penetrates a moving film under various physical conditions.        

![Falling Film Mass Transfer & Penetration Theory](Publications_20200101_jChERD.png)
 
Two python scripts are provided to calculate the mass transfer characteristics in falling liquid films. The scripts are written in Python 3.x and use the NumPy library for numerical calculations. The scripts solve the governing equations for convective mass transfer in a laminar falling film.

**Python Scripts**    

**1. Impact of Diffusivity**    
Analyzes how different diffusion coefficients impact the penetration depth and flux.

```python 
# (in)finite penetration depth : varying D
import numpy as np
import math
# test data 
L=1 # wall lenght 
gamma=0.05 # film flow rate kg/m.s 
#um=0.21 # maximum flow velocity 
#u=um*2/3 # average flow velocity 
cA0=0 # initial concentration 
cAi=0.0366 # interfacial concentration
#D=1.96/1000000000 # diffusivity 
var=[1.0, 2.0, 2.5, 5.0, 7.0, 8.0, 9.0]
varD=[vard/1000000000 for vard in var] 
Rho=998 # kg/m3
Mue=0.000894 # kg/m.s at STP
g=9.807 # m/s2
#Z=[0.01, 0.05, 0.1, 0.2, 0.5, 1, 1.5, 2, 2.4]
#Z=[z/10000 for z in Z] 
# y-coordinate 
YY=[0.00000000001, 0.0000000001, 0.000000001, 
    0.00000001, 0.0000001, 0.000001, 0.00001, 
    0.0001, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1]
Y=[L*y for y in YY] 
# film thickness 
delta=((3*Mue*gamma)/((Rho**2)*g))**(1/3)
u=gamma/(Rho*delta)
# z-coordinate 
Z=np.linspace(0, delta, num=50)
# mass transfer properties 
#delta=((3*Mue*u)/(Rho*g))**0.5
for D in varD:
	b=(2*D)/(3*u)
	infinity=100
	for y in Y:
		# finding kisi from BC2 
		guesslist=np.logspace(0, 10, num=10000)
		guesslist=delta/guesslist
		guesslist=np.fliplr([guesslist])[0]
		KICI=[delta]
		for kisi in guesslist:
			sigma=0
			for n in range(infinity):
				Sin=((-1)**n)/(2*n+1)
				lmbda=((2*n+1)*math.pi)/(2*kisi)
				lmbda2=lmbda**2
				Expot=(-1)*lmbda2*b
				Expt=y*Expot
				Exp=np.exp(Expt)
				An=Sin*Exp
				sigma += An
			Err=sigma - (math.pi/4)
			if abs(Err)==0:
				KICI.append(kisi)	
		kisi=min(KICI)
		# calculating kc and NA  
		Sum=0
		for n in range(infinity):
			lmbda=((2*n+1)*math.pi)/(2*kisi)
			lmbda2=lmbda**2
			Expot=(-1)*lmbda2*b
			Expt=y*Expot
			Exp=np.exp(Expt)
			An=Exp
			Sum += An
		kc_infY=(2*D/kisi)*Sum
		NA_infY=kc_infY*(cAi - cA0)
		kc_infN=((3*u*D)/(2*math.pi*y))**0.5
		NA_infN=(cAi-cA0)*kc_infN
		# kcbar calculation 
		Sum=0
		for n in range(infinity):
			lmbda=((2*n+1)*math.pi)/(2*kisi)
			lmbda2=lmbda**2
			Expot=(-1)*lmbda2*b
			Expt=L*Expot
			Exp=np.exp(Expt)
			An=Exp/((2*n+1)**2)
			Sum += An
		kcbar_infY=(12*u*kisi/(L*(math.pi**2)))*((math.pi**2)/8 - Sum)	
		kcbar_infN=((6*u*D)/(math.pi*L))**0.5
		# calculating cA 
		for z in Z:
			Sum=0
			for n in range(infinity):
				lmbda=((2*n+1)*math.pi)/(2*kisi)
				lmbda2=lmbda**2
				Expot=(-1)*lmbda2*b
				Expt=y*Expot
				Exp=np.exp(Expt)
				Sin=math.sin(z*lmbda)
				An=Sin*Exp/(2*n+1)
				Sum += An 
			cA_infY=cA0+(cAi-cA0)*(1-(4/math.pi)*Sum)
			Exp_infN=0.5*(((3*u*(z**2))/(2*D*y))**0.5)
			cA_infN=cA0+(cAi-cA0)*(1-math.erf(Exp_infN))
			print (D, y, z, delta, kisi, cA_infY, cA_infN, NA_infY, NA_infN, kc_infY, kc_infN, kcbar_infY, kcbar_infN, gamma, u)
```

**2. Impact of Flow Rate**    
Analyzes the effect of film velocity and thickness on mass transfer efficiency.

```python 
# (in)finite penetration depth : varying Gamma  
import numpy as np
import math
# test data
L=1 # wall lenght
#um=0.21 # maximum flow velocity
#u=um*2/3 # average flow velocity
varG=[0.01, 0.02, 0.05, 0.08, 0.10, 0.20]
cA0=0 # initial concentration
cAi=0.0366 # interfacial concentration
D=1.96/1000000000 # diffusivity
Rho=998 # kg/m3
Mue=0.000894 # kg/m.s at STP
g=9.807 # m/s2
# y-coordinate 
YY=[0.00000000001, 0.0000000001, 0.000000001, 
    0.00000001, 0.0000001, 0.000001, 0.00001, 
    0.0001, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1]
Y=[L*y for y in YY] 
for gamma in varG:
	# mass transfer properties
	delta=((3*Mue*gamma)/((Rho**2)*g))**(1/3)
	u=gamma/(Rho*delta)
	# z-coordinate 
	Z=np.linspace(0, delta, num=50)
	b=(2*D)/(3*u)
	infinity=100
	for y in Y:
		# finding kisi from BC2
		guesslist=np.logspace(0, 10, num=10000)
		guesslist=delta/guesslist
		guesslist=np.fliplr([guesslist])[0]
		KICI=[delta]
		for kisi in guesslist:
			sigma=0
			for n in range(infinity):
				Sin=((-1)**n)/(2*n+1)
				lmbda=((2*n+1)*math.pi)/(2*kisi)
				lmbda2=lmbda**2
				Expot=(-1)*lmbda2*b
				Expt=y*Expot
				Exp=np.exp(Expt)
				An=Sin*Exp
				sigma += An
			Err=sigma - (math.pi/4)
			if abs(Err)==0:
				KICI.append(kisi)
		kisi=min(KICI)
		# calculating kc and NA
		Sum=0
		for n in range(infinity):
			lmbda=((2*n+1)*math.pi)/(2*kisi)
			lmbda2=lmbda**2
			Expot=(-1)*lmbda2*b
			Expt=y*Expot
			Exp=np.exp(Expt)
			An=Exp
			Sum += An
		kc_infY=(2*D/kisi)*Sum
		NA_infY=kc_infY*(cAi - cA0)
		kc_infN=((3*u*D)/(2*math.pi*y))**0.5
		NA_infN=(cAi-cA0)*kc_infN
		# kcbar calculation 
		Sum=0
		for n in range(infinity):
			lmbda=((2*n+1)*math.pi)/(2*kisi)
			lmbda2=lmbda**2
			Expot=(-1)*lmbda2*b
			Expt=L*Expot
			Exp=np.exp(Expt)
			An=Exp/((2*n+1)**2)
			Sum += An
		kcbar_infY=(12*u*kisi/(L*(math.pi**2)))*((math.pi**2)/8 - Sum)	
		kcbar_infN=((6*u*D)/(math.pi*L))**0.5
		# calculating cA 
		for z in Z:
			Sum=0
			for n in range(infinity):
				lmbda=((2*n+1)*math.pi)/(2*kisi)
				lmbda2=lmbda**2
				Expot=(-1)*lmbda2*b
				Expt=y*Expot
				Exp=np.exp(Expt)
				Sin=math.sin(z*lmbda)
				An=Sin*Exp/(2*n+1)
				Sum += An 
			cA_infY=cA0+(cAi-cA0)*(1-(4/math.pi)*Sum)
			Exp_infN=0.5*(((3*u*(z**2))/(2*D*y))**0.5)
			cA_infN=cA0+(cAi-cA0)*(1-math.erf(Exp_infN))
			print (gamma, u, y, z, delta, kisi, cA_infY, cA_infN, NA_infY, NA_infN, kc_infY, kc_infN, kcbar_infY, kcbar_infN, D)
```  

**Usage Instructions**    
1. Open the desired script.
2. Adjust the **Test Data** section to match your physical system:

```python
L = 1         # Wall length (m)
gamma = 0.05  # Film flow rate (kg/m.s)
cAi = 0.0366  # Interfacial concentration
``` 












---

## Mathematical Logic

The scripts solve the governing equations for convective mass transfer in a laminar falling film.

### 1. Film Hydrodynamics
The film thickness (δ) and average velocity (u) are calculated based on the film flow rate (Γ) and fluid properties (density ρ, viscosity μ):

<p>δ = (3μΓ / ρ²g)<sup>1/3</sup></p>
<p>u = Γ / (ρδ)</p>

### 2. Infinite Penetration Model
For short contact times or thick films, the solute is assumed not to reach the wall. The local mass transfer coefficient (k<sub>c</sub>) is:

<p>k<sub>c</sub>(y) = (3uD / 2πy)<sup>1/2</sup></p>

### 3. Finite Penetration Model
When the solute reaches the wall (finite depth), the concentration profile is solved using a Fourier series expansion. The code determines a characteristic parameter (ξ) by solving for the root of the error function:

<p>Error = ( Σ<sub>n=0</sub><sup>∞</sup> <sup>(-1)<sup>n</sup></sup>&frasl;<sub>2n+1</sub> exp( - [ <sup>(2n+1)π</sup>&frasl;<sub>2ξ</sub> ]<sup>2</sup> &middot; <sup>Dy</sup>&frasl;<sub>u</sub> ) ) - π&frasl;4</p>

### 4. Mass Flux Calculation (N<sub>A</sub>)
The local mass flux at the interface is determined by:

<p>N<sub>A</sub> = k<sub>c</sub> &middot; (c<sub>Ai</sub> - c<sub>A0</sub>)</p>

Where c<sub>Ai</sub> is the interfacial concentration and c<sub>A0</sub> is the bulk concentration.

---