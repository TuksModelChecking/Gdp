import math

from yaml import load
from yaml import SafeLoader
from pyeda.inter import *

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


def to_binary_string(number: int) -> str:
    return format(number, 'b')


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, num_agents: int) -> And:
    b: int = math.ceil(math.log(num_agents, 2))
    to_conjunct = []
    for char in to_binary_string(agent):
        b = b - 1
        new_var = f"r{resource}a{agent}t{time}b{b}"
        to_conjunct.append(exprvar(new_var if char == '1' else Not(new_var)))
    return And(to_conjunct)
