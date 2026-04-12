### COSMO-SAC Sigma Profile Generator

This is a suite of MATLAB code designed to process raw quantum mechanical (QM) surface data into **sigma-profiles**.

- An **`html`** version of this document is available [**here**](Outlets_20141010_COSMO-SAC-Simga.html).

**How to Use**

- Replace `CompoundName` with the specific `sheet name` in the Excel file **`inputQM.xlsx`** ([**Click here to see sample input file**](Outlets_20141010_COSMO-SAC-Simga_inputQM.xlsx)):
	- **Columns C, D, E:** are X, Y, Z coordinates (Atomic Units).
	- **Column G:** is Segment Area.
	- **Column H:** is Charge per Area (Surface Charge Density).

- Call the calculator function from the MATLAB command window as `[Density, Profile, Vol] = SimgaProfileCalculator('CompoundName');`.

#### **Scripts Details**

##### **1. `SimgaProfileCalculator.m`**

```bash
function SimgaProfileCalculator()
    % [SigmaDensity SigmaProfile]=SimgaProfileCalculator()
    REFF = 0.81764200000000;
    Char=input('Enter sheet name contains data and press enter = ','s');
    [NUMSEGMENT VolCavity AreaCavity ...
        Charge Area Sigma Potential ...
        POSXAU POSYAU POSZAU]=IOinDataBase(Char);
    [POSXA POSYA POSZA RAD]=ConvertAU2A(POSXAU,POSYAU,POSZAU,Area);
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
    xlswrite('IOinDataBase.xlsx', SigmaDensity', Char, ['N3' ':' ['N' num2str(length(SigmaDensity)+3)]]); 
    xlswrite('IOinDataBase.xlsx', SigmaProfile', Char, ['O3' ':' ['O' num2str(length(SigmaDensity)+3)]]); 
end 
```

##### **2. **`IOinDataBase.m`** 

```bash
function [NUMSEGMENT VolCavity AreaCavity ...
    Charge Area ChargePerArea Potential ...
    POSXAU POSYAU POSZAU]=IOinDataBase(Char)
    % Reads data from IOinDataBase.xlsx for Compound in sheet "Char"
    NUMSEGMENT=xlsread('IOinDataBase.xlsx',Char,'L2');
    VolCavity=xlsread('IOinDataBase.xlsx',Char,'L3');
    AreaCavity=xlsread('IOinDataBase.xlsx',Char,'L4');
    EndPOSXAU=['C' num2str(NUMSEGMENT+4)];
    EndPOSYAU=['D' num2str(NUMSEGMENT+4)];
    EndPOSZAU=['E' num2str(NUMSEGMENT+4)];
    EndCharge=['F' num2str(NUMSEGMENT+4)];
    EndArea=['G' num2str(NUMSEGMENT+4)];
    EndChargePerArea=['H' num2str(NUMSEGMENT+4)];
    EndPotential=['I' num2str(NUMSEGMENT+4)];
    POSXAU=xlsread('IOinDataBase.xlsx',Char,['C4' ':' EndPOSXAU]);
    POSYAU=xlsread('IOinDataBase.xlsx',Char,['D4' ':' EndPOSYAU]);
    POSZAU=xlsread('IOinDataBase.xlsx',Char,['E4' ':' EndPOSZAU]);
    Charge=xlsread('IOinDataBase.xlsx',Char,['F4' ':' EndCharge]);
    Area=xlsread('IOinDataBase.xlsx',Char,['G4' ':' EndArea]);
    ChargePerArea=xlsread('IOinDataBase.xlsx',Char,['H4' ':' EndChargePerArea]);
    Potential=xlsread('IOinDataBase.xlsx',Char,['I4' ':' EndPotential]);
end
```

##### **3. `SortSimgaProfile.m`**

```bash
function [SigmaDensity SigmaProfile]=SortSimgaProfile(SigmaNEW,Area)
    % Sorts the Sigma Profile
    SigmaDensity = -0.025:1e-3:0.025;
    SigmaProfile = zeros(length(SigmaDensity),1)';
    for idPart=1:length(SigmaDensity)-1
        [dummy idParSigmaNEW]=find(SigmaNEW>SigmaDensity(idPart) & SigmaNEW<SigmaDensity(idPart+1));
        TempData=abs(SigmaNEW(idParSigmaNEW)-SigmaNEW(idParSigmaNEW+1)).*...
            Area(idParSigmaNEW);
        SigmaProfile(idPart)=sum(TempData);
    end
end
```

##### **4. `ConvertAU2A.m`**

```bash 
function [POSXA POSYA POSZA RAD]=ConvertAU2A(POSXAU,POSYAU,POSZAU,Area)
    % From atomic unit [au] to ANGSTROMS [A*]
    PI = 3.14159265358979;
    POSXA=POSXAU*0.529177249;
    POSYA=POSYAU*0.529177249;
    POSZA=POSZAU*0.529177249;
    RAD=sqrt(Area/PI);
end
```