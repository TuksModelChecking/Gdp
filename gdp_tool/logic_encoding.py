from yaml import load
from yaml import SafeLoader
from pysat.formula import CNF
from pysat.solvers import Lingeling

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)

# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int) -> CNF:
    encoding = CNF()
    return encoding
