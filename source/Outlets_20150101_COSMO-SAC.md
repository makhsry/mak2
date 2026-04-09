### COSMO-SAC Activity Coefficient Model

This is a suite of MATLAB code for the **COSMO-SAC (COSMO Segment Activity Coefficient)** model. 

- An **`.html`** version of the calculator can be found [**here**](Garage_20150101_COSMO-SAC_Calculator.html).

**Usage Instructions**

- The Excel file (**[`inputQM.xlsx`](Garage_20150101_COSMO-SAC_inputQM.xlsx)**) must have sheets named after your **`components`** (e.g., '67-63-0-2d' or 'Z1') containing the required QM output data.
- Set your desired **`SYSTEMP`** (Temperature in **Kelvin**).
- Update **`ListCOMP`** with the sheet names from your **`inputQM.xlsx`** file.
- Run the script **`eqCOSMO.m`**.

**Outputs**

- **`sProfiles.xlsx`**: Stores the calculated **`sigma-densities`** and **`profiles`** for each component.
- **`MixGamma.xlsx`**: Stores the final matrix containing **`mole fractions (x)`**, **`activity coefficients (γ)`**, and **`ln γ`**.

#### **Scripts Details**

##### **1. `eqCOSMO.m`**

```bash
function eqCOSMO() 
% Two Phase Equilibrium Calculations using COSMO model (COSMO-SAC) 
% Manual at this stage 
SYSTEMP=273.15; % temprature of interest 
MIX='Dissolved'; % Mixture 1 - Phase A
ListCOMP={'67-63-0-2d', 'Z1'}; % list of components in mixture 1
% Binary mixtures at this stage 
MATrixA=Binary(SYSTEMP, ListCOMP);
%MATrix(x,:)=[x1(x) GAMMA(1) LNGAMMA(1) x2(x) GAMMA(2) LNGAMMA(2)];
xlswrite('MixGamma.xlsx', MATrixA, MIX);
% 
MIX='Solute'; 
ListCOMP={'Z1', 'Z1'}; 
MATrixB=Binary(SYSTEMP, ListCOMP);
xlswrite('MixGamma.xlsx', MATrixB, MIX);
% Equilibria ::: @SLE
```

##### **2. `Binary.m`**

```bash
function MATrix=Binary(SYSTEMP, ListCOMP) 
% 
COMP=length(ListCOMP); % COMP=2;
% mole fractions 
x1=5e-3:1e-3:(1-5e-3); % mole fraction of component 1
x2=1-x1; % mole fraction of component 2
%
% COSMO settings 
[EO, AEFFPRIME, RGAS, VNORM, ANORM, COMPSEG, ...
	EPS, COORD, SIGMAHB, CHB, FPOL, ALPHA, ALPHAPRIME]=paraCOSMO(); 
%
for n=1:COMP
	[SigmaDensity SigmaProfile VolCavity]=SimgaProfileCalculator(ListCOMP{n});
	xlswrite('sProfiles.xlsx', SigmaDensity', ListCOMP{n}, ...
	['A3' ':' ['A' num2str(length(SigmaDensity)+3)]]); 
	xlswrite('sProfiles.xlsx', SigmaProfile', ListCOMP{n}, ...
	['B3' ':' ['B' num2str(length(SigmaDensity)+3)]]);
	SigmaProfiles(:,n)=SigmaProfile'; 
	ACOSMO(n)=sum(SigmaProfile); % MOLECULAR SURFACE AREA FROM COSMO OUTPUT (A**2) 
								% --THE SUM OF THE INDIVIDUAL PROFILE
	VCOSMO(n)=VolCavity; % CAVITY VOLUME FROM COSMO OUTPUT (A**3)
end
RNORM = VCOSMO./VNORM; 
QNORM = ACOSMO./ANORM;
for x=1:length(x1)
	NUMER = x1(x)*SigmaProfiles(:,1) + x2(x)*SigmaProfiles(:,2);
	DENOM = x1(x)*ACOSMO(1) + x2(x)*ACOSMO(2);
	MixSigmaProfile=NUMER./DENOM;
	for i=1:length(SigmaDensity)
		for j=1:length(SigmaDensity)
			if SigmaDensity(i)>=SigmaDensity(j)
				SIGMAACC = SigmaDensity(i);
				SIGMADON = SigmaDensity(j);
			else 
				SIGMADON = SigmaDensity(i);
				SIGMAACC = SigmaDensity(j);
			end 
			DELTAW(i,j)=(ALPHAPRIME/2.0)*(SigmaDensity(i)+SigmaDensity(j))^2.0 + ...
				CHB*max(0.0,(SIGMAACC - SIGMAHB))*min(0.0,(SIGMADON + SIGMAHB));
		end 
	end
	% SEGMENT ACITIVITY COEF (PURE SPECIES)
	for n=1:COMP
		CONPR=1e3;
		SEGGAMMAPR(1:length(SigmaDensity),n) = 1.0;
		while (max(CONPR) > 1e-6)
			SEGGAMMAOLDPR(:,n)=SEGGAMMAPR(:,n);
			for i=1:length(SigmaDensity)
				SUMMATION = 0.0;
				for j=1:length(SigmaDensity)
					SUMMATION = SUMMATION + ...
						(SigmaProfiles(j,n)/ACOSMO(n))*SEGGAMMAOLDPR(j,n)*...
						exp(-DELTAW(i,j)/(RGAS*SYSTEMP));
				end
				SEGGAMMAPR(i,n)=exp(-log(SUMMATION));
				SEGGAMMAPR(i,n)=(SEGGAMMAPR(i,n)+SEGGAMMAOLDPR(i,n))/2.0; 
			end 
			CONPR=abs((SEGGAMMAPR(:,n)-SEGGAMMAOLDPR(:,n))/SEGGAMMAOLDPR(:,n));
		end 
	end 
	% SEGMENT ACTIVITY COEF. (MIXTURE)
	CON=1e3;
	SEGGAMMA(1:length(SigmaDensity)) = 1.0;
	while (max(CON) > 1e-6)
		SEGGAMMAOLD=SEGGAMMA;
		for i=1:length(SigmaDensity)
			SUMMATION = 0.0;
			for j=1:length(SigmaDensity)
				SUMMATION = SUMMATION + MixSigmaProfile(j)...
				*SEGGAMMAOLD(j)*exp(-DELTAW(i,j)/(RGAS*SYSTEMP));
			end
			SEGGAMMA(i)=exp(-log(SUMMATION));
			SEGGAMMA(i)=(SEGGAMMA(i)+SEGGAMMAOLD(i))/2.0; 
		end 
		CON=abs((SEGGAMMA-SEGGAMMAOLD)/SEGGAMMAOLD);
	end 
	BOTTHETA = x1(x)*QNORM(1) + x2(x)*QNORM(2);
	BOTPHI = x1(x)*RNORM(1) + x2(x)*RNORM(2);
	THETA(1) = (x1(x)*QNORM(1))/BOTTHETA;
	THETA(2) = (x2(x)*QNORM(2))/BOTTHETA;
	PHI(1) = (x1(x)*RNORM(1))/BOTPHI;
	PHI(2) = (x2(x)*RNORM(2))/BOTPHI;
	L = (COORD/2.0)*(RNORM-QNORM)-(RNORM-1.0);
	% CALCULATION OF GAMMAS
	GAMMASG(1) = log(PHI(1)/x1(x))+(COORD/2)*QNORM(1)*log(THETA(1)/PHI(1))...
		+L(1)-(PHI(1)/x1(x))* (x1(x)*L(1) + x2(x)*L(2));
	GAMMASG(2) = log(PHI(2)/x2(x))+(COORD/2)*QNORM(2)*log(THETA(2)/PHI(2))...
		+L(2)-(PHI(2)/x2(x))* (x1(x)*L(1) + x2(x)*L(2)); 
	for n=1:COMP 
		SUMGAMMA(n)=sum((SigmaProfiles(:,n)/AEFFPRIME).*(log(SEGGAMMA'./(SEGGAMMAPR(:,n)))));
	end 
	GAMMA=exp(SUMGAMMA + GAMMASG);
	LNGAMMA = log(GAMMA);
	MATrix(x,:)=[x1(x) GAMMA(1) LNGAMMA(1) x2(x) GAMMA(2) LNGAMMA(2)];
end
% 
end
```

##### **3. `SimgaProfileCalculator.m`**

```bash
function [SigmaDensity SigmaProfile VolCavity]=SimgaProfileCalculator(Char)
% [SigmaDensity SigmaProfile]=SimgaProfileCalculator()
REFF = 0.81764200000000;
%Char=input('Enter sheet name contains data and press enter = ','s');
[NUMSEGMENT VolCavity AreaCavity ...
    Charge Area ChargePerArea Potential ...
    POSXAU POSYAU POSZAU]=Library(Char);
[POSXA POSYA POSZA RAD]=ConvertAU2A(POSXAU,POSYAU,POSZAU,Area);
Sigma=ChargePerArea;
SigmaNEW=zeros(NUMSEGMENT,1);
NormSum=zeros(NUMSEGMENT,1);
for i=1:NUMSEGMENT
    SigmaNEW(i)=0;
    NormSum(i)=0;
    for j=1:NUMSEGMENT
        diffPOSXA=POSXA(j)-POSXA(i);
        diffPOSYA=POSYA(j)-POSYA(i);
        diffPOSZA=POSZA(j)-POSZA(i);
        Term1=sqrt(diffPOSXA^2+diffPOSYA^2+diffPOSZA^2);
        Term2=Sigma(j)*((RAD(j)^2*REFF^2)/(RAD(j)^2+REFF^2)).*...
            exp(-Term1^2/((RAD(j)^2+REFF^2)));
        Term3=(RAD(j)^2*REFF^2*(RAD(j)^2+REFF^2))*...
            exp(-Term1^2/(RAD(j)^2+REFF^2));
        SigmaNEW(i)=SigmaNEW(i)+Term2;
        NormSum(i)= NormSum(i)+Term3;
    end
    SigmaNEW(i)=SigmaNEW(i)/NormSum(i);
end
[SigmaDensity SigmaProfile]=SortSimgaProfile(SigmaNEW,Area);
end
```

##### **4. `Library.m`**

```bash
function [NUMSEGMENT VolCavity AreaCavity ...
    Charge Area ChargePerArea Potential ...
    POSXAU POSYAU POSZAU]=Library(Char)
% Reads data from inputQM.xlsx for Compound in sheet "Char"
NUMSEGMENT=xlsread('inputQM.xlsx',Char,'L2');
VolCavity=xlsread('inputQM.xlsx',Char,'L3');
AreaCavity=xlsread('inputQM.xlsx',Char,'L4');
EndPOSXAU=['C' num2str(NUMSEGMENT+4)];
EndPOSYAU=['D' num2str(NUMSEGMENT+4)];
EndPOSZAU=['E' num2str(NUMSEGMENT+4)];
EndCharge=['F' num2str(NUMSEGMENT+4)];
EndArea=['G' num2str(NUMSEGMENT+4)];
EndChargePerArea=['H' num2str(NUMSEGMENT+4)];
EndPotential=['I' num2str(NUMSEGMENT+4)];
% 
POSXAU=xlsread('inputQM.xlsx',Char,['C4' ':' EndPOSXAU]);
POSYAU=xlsread('inputQM.xlsx',Char,['D4' ':' EndPOSYAU]);
POSZAU=xlsread('inputQM.xlsx',Char,['E4' ':' EndPOSZAU]);
% 
Charge=xlsread('inputQM.xlsx',Char,['F4' ':' EndCharge]);
Area=xlsread('inputQM.xlsx',Char,['G4' ':' EndArea]);
ChargePerArea=xlsread('inputQM.xlsx',Char,['H4' ':' EndChargePerArea]);
Potential=xlsread('inputQM.xlsx',Char,['I4' ':' EndPotential]);
end
```

##### **5. `paraCOSMO.m`**

```bash
function [EO, AEFFPRIME, RGAS, VNORM, ANORM, COMPSEG, ...
	EPS, COORD, SIGMAHB, CHB, FPOL, ALPHA, ALPHAPRIME]=paraCOSMO()
EO = 2.395e-4; % PERMITTIVITY IN A VACUUM (e**2*mol/Kcal*Angstrom)
AEFFPRIME = 7.5; % EFFECTIVE SURFACE AREA (ANGSTROMS**2) --FROM LIN
RGAS = 0.001987; % IDEAL GAS CONSTANT (Kcal/mol*K)
VNORM = 66.69;  % VOLUME NORMALIZATION CONSTANT (A**3) --FROM LIN
ANORM = 79.53; % AREA NORMALIZATION CONSTANT (A**2) --FROM LIN
COMPSEG = 51; % NUMBER OF INTERVALS FOR THE SIGMA PROFILE
EPS = 3.667; % RELATIVE PERMITTIVITY 
			% --FROM LIN (LIN AND SANDLER USE A CONSTANT FPOL WHICH YEILDS EPS=3.68)
COORD = 10.0; % THE COORIDINATION NUMBER --FROM LIN (KLAMT USED 7.2)  
SIGMAHB = 0.0084; % CUTOFF VALUE FOR HYDROGEN BONDING (e/Angstrom**2)
CHB = 85580.0; % HYDROGEN BONDING COEFFICIENT (Kcal/mole*Angstroms**4/e**2)
FPOL = (EPS-1.0)/(EPS+0.5);
ALPHA = (0.3*AEFFPRIME^(1.5))/(EO);
ALPHAPRIME = FPOL*ALPHA; % ALPHAPRIME = A CONSTANT USED IN THE MISFIT ENERGY CALCULATION
end 
```

##### **6. `SortSimgaProfile.m`**

```bash
function [SigmaDensity SigmaProfile]=SortSimgaProfile(SigmaNEW,Area)
% Sorts the Sigma Profile
SigmaDensity = -0.025:1e-3:0.025;
SigmaProfile = zeros(length(SigmaDensity),1)';
%
for idPart=1:length(SigmaDensity)-1
    [dummy idParSigmaNEW]=find(SigmaNEW>SigmaDensity(idPart) & SigmaNEW<SigmaDensity(idPart+1));
    TempData=abs(SigmaNEW(idParSigmaNEW)-SigmaNEW(idParSigmaNEW+1)).*...
        Area(idParSigmaNEW);
    SigmaProfile(idPart)=sum(TempData);
end
end

```

##### **7. `ConvertAU2A.m`**

```bash
function [POSXA POSYA POSZA RAD]=ConvertAU2A(POSXAU,POSYAU,POSZAU,Area)
% From atomic unit [au] to ANGSTROMS [A*]
PI = 3.14159265358979;
% 
POSXA=POSXAU*0.529177249;
POSYA=POSYAU*0.529177249;
POSZA=POSZAU*0.529177249;
RAD=sqrt(Area/PI);
end
```