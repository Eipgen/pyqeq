import numpy as np
from scipy.special import erf

def get_parameters(qeqfile):
    eV = 3.67493245e-2
    Angstrom = 1./0.529177249
    parameters = {}
    with open(qeqfile) as f:
        for i in range(13):
            next(f)
        for line in f:
            data = line.rstrip().split()
            element = data[0]
            elecnegativity = float(data[1])*eV
            hardness = float(data[2])*eV
            sradius = float(data[3])*Angstrom
            basis = 1.0/(sradius*sradius)
            parameters[element] = [elecnegativity, hardness, basis]
    return parameters
    
def read_total_charge(infile):
    with open(infile) as f:
        for line in f:
            if line.startswith("TCHARGE"):
                total_charge = float(line.rstrip().split()[1])
                return total_charge

def get_elements(file):
    atomElements = {}
    F=open(file).readlines()[2:]
    for line in F:
        data = line.rstrip().split()
        atomElements[int(data[4])] = data[0]
    return atomElements

def atom_info(file):
    F=open(file).readlines()[2:]
    atoms = []
    for line in F:
        data = line.rstrip().split()
        atoms.append([float(data[1]),float(data[2]),float(data[3]),int(data[4])])
    return atoms

def calculate_coulomb_intergral(a,b,R):
    """
    a,b are the basis of the two atoms
    R is the distance between the two atoms
    """
    p = np.sqrt(a*b/(a+b))
    return erf(p*R)/R

def fill_J(atoms, J, BasisSet, CoulombMaxDistance):
    Angstrom = 1./0.529177249
    nAtoms = len(atoms)
    for k in range(0, nAtoms):
        for l in range(0,nAtoms):
            if k >l:
                atom1 = atoms[k]
                atom2 = atoms[l]
                xyz_atom1 = np.array(atom1[0:3])
                xyz_atom2 = np.array(atom2[0:3])
                R = np.linalg.norm(xyz_atom1-xyz_atom2)*Angstrom
                if R < CoulombMaxDistance:
                    coulomb = calculate_coulomb_intergral(BasisSet[k],BasisSet[l],R)
                else:
                    coulomb = 1.0/R
                J[k][l] = coulomb
                J[l][k] = coulomb
    for i in range(nAtoms+1):
        J[nAtoms][i] = 1.0
        J[i][nAtoms] = 1.0
    J[nAtoms][nAtoms] = 0.0

def compute_Qeq_charges(atoms,atomElments,total_charge,charge_past):
    CoulombThreshold = 1e-9
    nAtoms = len(atoms)
    ElectroNegativity = np.zeros(nAtoms)
    J = np.zeros((nAtoms+1,nAtoms+1)) # hardness
    Voltage = charge_past
    BasisSet = np.zeros(nAtoms)
    parameters = get_parameters("qeq_reaxff2016.txt")
    #atomElements = get_elements("./atom.xyz")
    for i in range(nAtoms):
        atomType = atoms[i][3]
        atomElement = atomElements[atomType]
        ElectroNegativity[i] = parameters[atomElement][0]
        J[i][i] = parameters[atomElement][1]
        BasisSet[i] = parameters[atomElement][2]
    #total_charge = read_total_charge("./atom.xyz")
    print("Total charge: ", total_charge)
    SmallestGaussianExponent = min(BasisSet)
    CoulombMaxDistance = 2*np.sqrt(-np.log(CoulombThreshold)/SmallestGaussianExponent)
    fill_J(atoms, J, BasisSet, CoulombMaxDistance)
    print("Hardness")
    for j in J:
        j=[str(round(i,6)) for i in j]
        print(" ".join(j))
    Voltage[:-1] = ElectroNegativity
    Voltage[-1] = total_charge
    print("Voltage")
    for i in Voltage:
        print(round(i,6))
    charges = np.linalg.solve(J,Voltage)
    return charges

def Qeq_charge_equilibration(atoms,atomElements,total_charge):
    nAtoms = len(atoms)
    new_charges = np.zeros(nAtoms+1)
    for i in range(1):
        charge_past = new_charges
        new_charges = compute_Qeq_charges(atoms,atomElements,total_charge,charge_past)
    qeq_charges = new_charges
    return qeq_charges

atoms=atom_info("./atom.xyz")
atomElements = get_elements("./atom.xyz")
total_charge = read_total_charge("./atom.xyz")
qeq_charges = Qeq_charge_equilibration(atoms,atomElements,total_charge)
print(qeq_charges) 
