import math

from yaml import load
from yaml import SafeLoader
from pyeda.inter import *
from dataclasses import dataclass

# Let "Paper" be used to denote the SMBF2021 submission by Nils Timm and Josua Botha

problem = load(open("input.yml", "r"), Loader=SafeLoader)


@dataclass
class Agent:
    id: int
    acc: list[int]
    d: int


@dataclass
class MRA:
    agt: list[Agent]
    res: list[int]

    def num_agents(self):
        return len(self.agt)

    def num_resources(self):
        return len(self.res)


@dataclass
class AgentAlias:
    id: int
    d_left: int

    def clone(self):
        return AgentAlias(self.id, self.d_left)


@dataclass
class UnCollapsedState:
    resource: int
    agents: list[AgentAlias]

    def clone(self):
        return UnCollapsedState(self.resource, list(map(lambda aa: aa.clone(), self.agents)))


@dataclass
class State:
    a: int
    r: int


def to_binary_string(number: int, x: int) -> str:
    return format(number, 'b').zfill(m(x))


def m(x) -> int:
    return math.ceil(math.log(x, 2))


# By Definition 12, 13, 15 in Paper
def binary_encode(binary_string: str, name_prefix: str):
    to_conjunct = []
    for index, char in enumerate(reversed(binary_string)):
        new_var = f"{name_prefix}b{index}"
        to_conjunct.append(
            exprvar(new_var if char == '1' else Not(new_var))
        )
    return And(to_conjunct)


# By Definition 4 in Paper
def explicate_all_possible_states_of_resource(r: int, agt: list[Agent]) -> UnCollapsedState:
    agents_with_acc = []
    for a in agt:
        if r in a.acc:
            agents_with_acc.append(AgentAlias(a.id, a.d))
    return UnCollapsedState(r, agents_with_acc)


# By Definition 4 in Paper
def map_of_agents_involved(un_collapsed_observation_set) -> dict:
    agents_involved: dict[int, int] = {}
    for uco in un_collapsed_observation_set:
        for a in uco.agents:
            agents_involved[a] = 0
    return agents_involved


# def explicate_state_observation_set(a_i: Agent, mra: MRA) -> list[list[State]]:
#     un_collapsed_observation_set = []
#     for r in a_i.acc:
#         un_collapsed_observation_set.append(explicate_all_possible_states_of_resource(r, mra.agt))
#     agents_involved = map_of_agents_involved(un_collapsed_observation_set)
#     collapsed_observation_set = []
#     for uco in un_collapsed_observation_set:
#         for a in uco.agents:
#             collapsed_observation_set.append([])


def collapse_observation_set(un_collapsed_states: list[UnCollapsedState]):
    return h_collapse_observation_set_rec(un_collapsed_states, [])


def clone(un_collapsed_observation: list[UnCollapsedState]):
    return list(map(lambda ucs: ucs.clone(), un_collapsed_observation))


def h_collapse_observation_set_rec(un_collapsed_states: list[UnCollapsedState], collapsed_observation: list[State]):
    if len(un_collapsed_states) == 0:
        return [collapsed_observation]
    ucs: UnCollapsedState = un_collapsed_states.pop()
    result_group = []
    for a in ucs.agents:
        if a.d_left > 0:
            a.d_left = a.d_left - 1
            collapsed_observation.append(State(a.id, ucs.resource))
            result_group += h_collapse_observation_set_rec(
                clone(un_collapsed_states),
                collapsed_observation,
            )
    return result_group


# By Definition 12 in Paper
def encode_resource_state(resource: int, agent: int, time: int, total_num_agents: int) -> And:
    return binary_encode(
        to_binary_string(agent, total_num_agents),
        f"r{resource}a{agent}t{time}"
    )


# By Definition 13 in Paper
def encode_action(action: int, agent: int, time: int, total_possible_actions: int) -> And:
    return binary_encode(
        to_binary_string(agent, total_possible_actions),
        f"act{action}a{agent}t{time}"
    )


# Must send in state observation (which resources - in acc_list - are held by which agents)
# By Definition 14 in Paper
def encode_state_observation(acc_list: list, agent: int, total_num_agents: int, time: int) -> And:
    to_conjunct = []
    for resource in acc_list:
        to_conjunct.append(
            encode_resource_state(resource, agent, time, total_num_agents)
        )
    return And(to_conjunct)


# By Definition 15 in Paper
def encode_strategic_decision(action: int, agent: Agent, time: int) -> And:
    return binary_encode(
        to_binary_string(action, len(agent.acc)),
        f"s_act{action}a{agent.id}t{time}"
    )


# By definition 16 in Paper
def encode_uniform_action(action: int, agent: int, total_num_agents: int, total_possible_actions: int,
                          time: int) -> And:
    return And(
        encode_action(action, agent, time, total_possible_actions),
        h_encode_uniformity_clause(agent, total_num_agents, action, total_possible_actions, time)
    )


# By definition 16 in Paper (helper function)
def h_encode_uniformity_clause(agent, total_num_agents, action, total_possible_actions, time):
    pass

# By definition 18

# By definition 19

# Evolution

# Initial State
