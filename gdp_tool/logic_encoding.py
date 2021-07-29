import math

from yaml import load
from yaml import SafeLoader
from sympy import *
from pysat.formula import CNF
from pysat.solvers import Minisat22

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, num_agents: int) -> CNF:
    m: int = math.ceil(math.log(num_agents, 2))
    symbol_assembly_line = []
    for b in reversed(range(0, m)):
        symbol_assembly_line.append(f"r{resource}a{agent}t{time}b{b}")
    boolean_symbols = symbols(symbol_assembly_line)
    return to_cnf(And(*boolean_symbols))


print(encode_resource_state(1, 1, 1, 8))
