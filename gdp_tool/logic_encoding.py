import math
import re as r

from yaml import load
from yaml import SafeLoader
from sympy import *
from pysat.formula import CNF
from pysat.solvers import Minisat22

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


# A helper function that can convert unique a named variable into a unique integer, created so that pysat can be used
# alongside variables given non-integer names, as in the Paper, to make this program easier to map to the paper
def ascii_encode(s: Symbol) -> int:
    name = s.__str__()
    ascii_encoding = ""
    for char in name:
        ascii_encoding += str(ord(char)).zfill(3)
    return int(ascii_encoding)


# Acts as the "antidote" to ascii_encode: given a number it spits out the original Symbol
def ascii_decode(number: int) -> Symbol:
    name = ""
    for encoded_char in r.findall('...', str(number)):
        name += chr(int(encoded_char))
    return Symbol(name)


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, num_agents: int) -> CNF:
    m: int = math.ceil(math.log(num_agents, 2))
    symbol_assembly_line = []
    for b in reversed(range(0, m)):
        symbol_assembly_line.append(f"r{resource}a{agent}t{time}b{b}")
    boolean_symbols = symbols(symbol_assembly_line)
    for sym in boolean_symbols:
        print(ascii_decode(ascii_encode(sym)))
    return to_cnf(And(*boolean_symbols))


encode_resource_state(1, 1, 1, 8)

# with Minisat22(bootstrap_with=encode_resource_state(1, 1, 1, 8)) as mini:
#     print(mini.solve())
