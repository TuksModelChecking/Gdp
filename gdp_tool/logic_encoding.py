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


def extract_negation_and_variable(symbol):
    symbol_string = str(symbol)
    if symbol_string[0] == '~':
        negation_sign = -1
        symbol_string = symbol_string[1:]
    else:
        negation_sign = 1
    return negation_sign, symbol_string


def symbol_cnf_to_int_cnf(symbol_cnf: Tuple, store: IDStore):
    int_cnf = []
    for clause in symbol_cnf:
        if type(clause) is Tuple:
            new_clause = []
            for symbol in clause:
                negation_sign, variable = extract_negation_and_variable(symbol)
                new_clause.append(negation_sign * store.get_or_generate_var_id(variable))
            int_cnf.append(new_clause)
        else:
            negation_sign, variable = extract_negation_and_variable(clause)
            int_cnf.append(negation_sign * store.get_or_generate_var_id(variable))
    return int_cnf


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, num_agents: int) -> And:
    m: int = math.ceil(math.log(num_agents, 2))
    symbol_assembly_line = []
    for b in reversed(range(0, m)):
        symbol_assembly_line.append(f"r{resource}a{agent}t{time}b{b}")
    return to_cnf(And(*symbols(symbol_assembly_line)))


STORE = IDStore()
print(encode_resource_state(1, 1, 1, 12))
s = encode_resource_state(1, 1, 1, 12).args
print(s)
print(type(s))
for t in s:
    print(t)
    print(t.args)

print(symbol_cnf_to_int_cnf(s, STORE))
