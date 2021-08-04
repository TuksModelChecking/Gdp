import math

from yaml import load
from yaml import SafeLoader
from pyeda.inter import *

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


def to_binary_string(number: int, x: int) -> str:
    return format(number, 'b').zfill(m(x))


def m(x) -> int:
    return math.ceil(math.log(x, 2))


# By Definition 12, 13 in Paper
def binary_encode(binary_string: str, name_prefix: str):
    to_conjunct = []
    for index, char in enumerate(reversed(binary_string)):
        new_var = f"{name_prefix}b{index}"
        to_conjunct.append(exprvar(new_var if char == '1' else Not(new_var)))
    return And(to_conjunct)


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, total_num_agents: int) -> And:
    return binary_encode(
        to_binary_string(agent, total_num_agents),
        f"r{resource}a{agent}t{time}"
    )


# By Definition 13 in Paper
def encode_action(action: int, agent: int, time: int, total_num_actions: int) -> And:
    return binary_encode(
        to_binary_string(agent, total_num_actions),
        f"act{action}a{agent}t{time}"
    )

