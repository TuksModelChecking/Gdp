import math
import re as r

import sympy
from yaml import load
from yaml import SafeLoader
from sympy import *
from pysat.formula import CNF
from sympy.abc import A, B, D
from pysat.solvers import Minisat22

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


class IDStore:
    next_id_source = 0
    variable_list = {}

    def __generate_id(self):
        self.next_id_source += 1
        return self.next_id_source

    def get_or_generate_var_id(self, variable):
        if variable not in self.variable_list:
            self.variable_list[variable] = self.__generate_id()
        return self.variable_list[variable]


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, num_agents: int, store: IDStore) -> And:
    m: int = math.ceil(math.log(num_agents, 2))
    symbol_assembly_line = []
    for b in reversed(range(0, m)):
        symbol_assembly_line.append(f"r{resource}a{agent}t{time}b{b}")
    return to_cnf(And(*symbols(symbol_assembly_line)))


STORE = IDStore()
s = encode_resource_state(1, 1, 1, 12, STORE).args
print(s)
print(type(s))
for t in s:
    print(t)
    print(t.args)

