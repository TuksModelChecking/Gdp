from sys import argv
from yaml import load
from yaml import dump
import click
from random import randrange

class GDPParser:
    def __init__(self, gdp, ispl_file, fair, obs):
        self.tab_depth = 0
        self.gdp = gdp
        self.ispl_file = ispl_file
        if fair == None:
            self.fairness = False if gdp["fairness"] == None else gdp["fairness"]
        else:
            self.fairness = fair
        self.agent_index = []
        self.resources = []
        malformed = False
        for item in gdp:
            if item in ["fairness", "formulae","observable"]:
                continue
            if gdp[item]["demand"] == None:
                print(f"error: agent {item} requires a demand integer.")
                malformed = True
            if not isinstance(gdp[item]["access"], list) or len(gdp[item]["access"]) == 0:
                print(f"error: agent {item} requires a demand list")
                malformed = True
            self.agent_index.append(item)

            for r in gdp[item]["access"]:
                if not isinstance(r, str):
                    print(f"error: resource {r}, in agent {item} is not a string")
                if r not in self.resources:
                    self.resources.append(r)
        if malformed:
            print("ABORTING: Your GDP file is malformed. Please ensure you are conforming to the standard.")
            exit()
        self.agent_index.sort()
        self.resources.sort()
        self.n_a = len(self.agent_index)
        self.n_r = len(self.resources)
        if obs == None:
            self.observable = self.__explicit_agent_set(
                "" if self.gdp["observable"] == None else self.gdp["observable"].strip()[1:-1]
            )
        else:
            self.observable = self.__explicit_agent_set(
                "all" if obs else ""
            )

    def __del__(self):
        self.ispl_file.close()

    def __deduce_groups_from(self, formulae):
        groups = set()
        reading = False
        group_name = ""
        for f in formulae:
            for char in f:
                if not reading and char == '<':
                    reading = True
                    group_name = ""
                elif reading:
                    if char == '>':
                        reading = False
                        groups.add(group_name)
                    else:
                        group_name += char
            if reading:
                print("Formulae input should always have closing '>' for each agent group used")
                raise ValueError
        return groups

    def __take_condition(self, resource, agent):
        a_id = agent[1:]
        r_id = resource[1:]
        condition = f"{resource}=none and {agent}.Action=req_{resource}"
        for a in self.agent_index:
            if a != agent and resource in self.gdp[a]["access"]:
                condition += f" and !({a}.Action=req_{resource})"
        return condition

    def __others_not_requesting(self, resource, agent):
        condition = f"Environment.{resource} = none"
        for a in self.agent_index:
            if a != agent and resource in self.gdp[a]["access"]:
                condition += f" and !({a}.Action=req_{resource})"
        return condition

    def __agents_in_group(self, g):
        agents = g.split("_")
        agents_explicit = set()
        last_agent = None
        fill_gap = False
        for agent in agents:
            if agent == "":
                fill_gap = True
                continue
            if fill_gap:
                for i in range(self.agent_index.index(last_agent)+1, self.agent_index.index(agent)): ## list has to be sorted correctly
                    agents_explicit.add(self.agent_index[i])
                fill_gap = False
            agents_explicit.add(agent)
            last_agent = agent
        return agents_explicit

    def __all_except(self, g):
        to_exclude = self.__agents_in_group(g)
        agent_set = set()
        for agent in self.agent_index:
            if agent not in to_exclude:
                agent_set.add(agent)
        return agent_set

    def __explicit_agent_set(self, g):
        if g == "none":
            return set()
        if g == "all":
            return set(self.agent_index)
        elif g.startswith("EX"):
            return self.__all_except(g[2:])
        else:
            return self.__agents_in_group(g)

    def __groups_to_ispl(self, groups):
        return [(g + " = " + str(self.__explicit_agent_set(g)).replace('\'','') + ";") for g in groups]

    def __generate_achieve(self, acting_group):
        achieve = ""
        for a in self.__explicit_agent_set(acting_group):
            achieve += f"(<{acting_group}>F {a}_eat) and "
        return achieve[:-5] + ";"

    def __generate_live(self, acting_group):
        live = f"<{acting_group}>G ("
        for a in self.__explicit_agent_set(acting_group):
            live += f"(<{acting_group}>F {a}_eat) and "
        return live[:-5] + ");"

    def __generate_prevent(self, acting_group):
        prevent = f"<{acting_group}>G ("
        for a in self.agent_index:
            if a not in self.__explicit_agent_set(acting_group):
                prevent += f"!{a}_eat and "
        return prevent[:-5] + ");"

    def __generate_ispl_formula(self, formula):
        formula = formula.strip()
        group = formula[formula.find('<')+1:formula.find('>')]
        if formula.endswith("achieve"):
            return self.__generate_achieve(group)
        elif formula.endswith("live"):
            return self.__generate_live(group)
        elif formula.endswith("prevent"):
            return self.__generate_prevent(group)
        else:
            return formula

    # ==== Functions that write to file ==================================
    # ====================================================================
    def write(self, string):
        tabs = ("\t" * self.tab_depth)
        self.ispl_file.write(f"{tabs}{string}\n")

    def write_tab(self, string):
        self.write(string)
        self.tab_depth += 1

    def untab_write(self, string):
        self.tab_depth -= 1
        self.write(string)

    def write_ispl_single_assignment(self):
        self.write("Semantics = SingleAssignment;\n")

    def write_ispl_environment(self):
        self.write_tab("Agent Environment")
        self.write_tab("Vars:")
        for r in self.resources:
            valid_vars = "{none,"
            for a in self.agent_index:
                if r in self.gdp[a]["access"]:
                    valid_vars += f"{a},"
            valid_vars = valid_vars[:-1] + "}"
            self.write(f"{r}: {valid_vars};")
        for a in self.observable:
            demand = self.gdp[a]["demand"]
            self.write(f"rem_{a} : 0..{demand};")
        self.untab_write("end Vars")
        self.write("Actions = {none};\n\tProtocol:\n\t\tOther: {none};\n\tend Protocol")
        self.write_tab("Evolution:")
        for r in self.resources:
            for a in self.agent_index:
                if r in self.gdp[a]["access"]:
                    self.write(f"{r} = {a} if ({self.__take_condition(r, a)});")
                    self.write(f"{r} = none if ({r} = {a} and {a}.Action = rel_{r});")
                    self.write(f"{r} = none if ({r} = {a} and {a}.Action = relall);\n")
                    if a in self.observable:
                        self.write(f"rem_{a} = rem_{a} - 1 if ({self.__take_condition(r, a)});")
                        self.write(f"rem_{a} = rem_{a} + 1 if ({r} = {a} and {a}.Action = rel_{r});")
                        self.write(f"rem_{a} = {self.gdp[a]['demand']} if ({r} = {a} and {a}.Action = relall);\n")      
        self.untab_write("end Evolution")
        self.untab_write("end Agent\n")
    
    def write_ispl_agents(self):
        for agent in self.agent_index:
            agent
            self.write_tab(f"Agent {agent}")
            actions = "{"
            lobsvars = "{"
            for r in self.gdp[agent]["access"]:
                actions += f"req_{r},"
                actions += f"rel_{r},"
                lobsvars += r
                lobsvars += ","
            for a in self.observable:
                lobsvars += f"rem_{a},"
            if len(lobsvars) == 1:
                lobsvars = "{none};"
                actions = "{idle};"
            else:
                actions = actions[:-1] + ",relall,idle};"
                lobsvars = lobsvars[:-1] + "};"
            self.write(f"Lobsvars = {lobsvars}")
            self.write_tab("Vars:")
            demand = self.gdp[agent]["demand"]
            self.write(f"rem : 0..{demand};")
            if self.fairness:
                self.write(f"idl : boolean;")
            self.untab_write("end Vars")
            self.write(f"Actions = {actions}")
            self.write_tab("Protocol:")
            self.write("rem = 0 : {relall};")
            self.write("rem > 0 : {idle};")
            for my_r in self.gdp[agent]["access"]:
                req = "{req_" + my_r + "}"
                rel = "{rel_" + my_r + "}"
                self.write(f"rem > 0 and Environment.{my_r} = none : {req};")
                self.write(f"rem > 0 and Environment.{my_r} = {agent} : {rel};")
            self.untab_write("end Protocol")
            self.write_tab("Evolution:")
            for my_r in self.gdp[agent]["access"]:
                onr = self.__others_not_requesting(my_r, agent)
                self.write(f"rem = rem - 1 if (Action = req_{my_r} and Environment.{my_r} = none and {onr});")
                self.write(f"rem = rem + 1 if (Action = rel_{my_r});")
                self.write(f"rem = {self.gdp[agent]['demand']} if (Action = relall);\n")
                if self.fairness:
                    self.write(f"idl = false if (Action = req_{my_r} and Environment.{my_r} = none and {onr});")
                    self.write(f"idl = false if (Action = rel_{my_r});")
                    self.write(f"idl = false if (Action = relall);")
                    self.write(f"idl = true if (Action = idle);\n")
            self.untab_write("end Evolution")
            self.untab_write(f"end Agent\n")

    def write_ispl_evaluation(self):
        self.write_tab("Evaluation")
        for a in self.agent_index:
            self.write(f"{a}_eat if ({a}.rem = 0);")
        if self.fairness:
            for a in self.agent_index:
                self.write(f"not_idle_{a} if ({a}.idl = false);")
        self.untab_write("end Evaluation\n")

    def write_ispl_init_states(self):
        self.write_tab("InitStates")
        for r in self.resources:
            self.write(f"Environment.{r} = none and")
        for a in self.observable:
            self.write(f"Environment.rem_{a} = {self.gdp[a]['demand']} and")
        for i in range(1, self.n_a-1):
            self.write(f"{self.agent_index[i]}.rem = {self.gdp[self.agent_index[i]]['demand']} and")
        self.write(f"{self.agent_index[self.n_a-1]}.rem = {self.gdp[self.agent_index[self.n_a-1]]['demand']};")
        self.untab_write("end InitStates\n")

    def write_ispl_groups(self):
        self.write_tab("Groups")
        for g in self.__groups_to_ispl(self.__deduce_groups_from(self.gdp["formulae"])):
            self.write(g)
        self.untab_write("end Groups\n")

    def write_ispl_fairness(self):
        if self.fairness:
            self.write_tab("Fairness")
            for a in self.agent_index:
                self.write(f"not_idle_{a};")
            self.untab_write("end Fairness\n")

    def write_ispl_formulae(self):
        self.write_tab("Formulae")
        for f in self.gdp["formulae"]:
            self.write(self.__generate_ispl_formula(f))
        self.untab_write("end Formulae\n")

def generate_access(num_resources, demand):
    if num_resources == 0:
        return []
    access = set()
    access_size = max(randrange(demand, num_resources+1), demand)
    while len(access) < access_size:
        access.add(f"r{randrange(1, num_resources+1)}")
    return list(access)


def generate_template_file(filename, bounds):
    b = extract_bounds(bounds)
    num_agents = randrange(b[0][0], b[0][1])
    gdp = {'fairness': False, 'formulae': ['<all> live'], 'observable': '<none>'}
    num_resources = 0
    if len(b) > 1:
        num_resources = randrange(b[1][0], b[1][1])
    demand_range = (1, max(num_resources, 2))
    if len(b) > 2:
        demand_range = b[2]
    for i in range(1, num_agents+1):
        demand = randrange(demand_range[0], demand_range[1])
        gdp[f'a{i}'] = {'access': [generate_access(num_resources, demand)], 'demand': demand}
    with open(f"gdp_files/{filename}", 'w') as f:
        dump(gdp, f)
    with open(f"gdp_files/{filename}", "a") as f:
        f.write("\n# USAGE GUIDE ===============\n# ===========================\n")


def extract_bounds(bnds):
    bnds = bnds.split(',')
    bounds = []
    for b in bnds:
        b = b.split("..")
        if len(b) > 1:
            bounds.append((int(b[0]), int(b[1])))
        else:
            bounds.append((int(b[0]), int(b[0])+1))
    return bounds

# === CLI ===========================================================
# ===================================================================
@click.command()
@click.option('--gdp_file', '-gdp', default=None, type=click.Path(exists=True), help="The GDP file to convert to ISPL.")
@click.option('--ispl_file', '-ispl', default='ispl_files/out.ispl', type=click.Path(), help="Location and name to give generated file.")
@click.option('--fair/--nfair', '-f/-nf', default=None, help='Add fairness constraint. Default: -nf')
@click.option('--obs/--nobs', '-o/-no', default=None, help="Make demand vars observable. Default: -no")
@click.option('--generate', '-g', nargs=2, type=str, help="Generate a GDP model based on the specified num_agents,num_resources,agent_demand. Each paramater can be an int or an int range. EXAMPLE: -g gdp.txt 3,2..4,1..4\nNote, you may run with only num_agents. EXAMPLE: -g gdp.txt 3")

# === main ==========================================================
# ===================================================================
def main(fair, obs, generate, ispl_file, gdp_file):
    """
        A tool that converts a shorthand description of a GDP model to an ISPL file that can be checked using MCMAS.\n
        USAGE EXAMPLE\n  
        GDP definition:\n
            $ python3 parsegdp.py -t model_name.txt 3   (Then manually define rest of GDP in model_name.txt)\n
            or\n
            $ python3 parsegdp.py -g model_name.txt 3..5,7,2..7    (Generate GDP model with 3 to 5 agents, 7 resources, and (for each agent) a demand within the range [2,7]. Open file to set formulae to check)\n
        then\n
        ISPL generation:\n
            $ python3 parsegdp.py -gdp model_name.txt -o -f -ispl m13.ispl    (Parse model; turn on observability and fairness; output as m13.ispl)\n
    """ 
    if len(generate) == 2:
        generate_template_file(generate[0], generate[1])
    elif gdp_file != None:
        gdpp = GDPParser(
            load(open(gdp_file,"r")),
            open(ispl_file, "w"),
            fair,
            obs
        )
        gdpp.write_ispl_single_assignment()
        gdpp.write_ispl_environment()
        gdpp.write_ispl_agents()
        gdpp.write_ispl_evaluation()
        gdpp.write_ispl_init_states()
        gdpp.write_ispl_groups()
        gdpp.write_ispl_fairness()
        gdpp.write_ispl_formulae()
        gdpp.__del__()
        print(f"done, '{ispl_file}' created")
    else:
        print("run with --help for usage guide, ex:\npython3 parsegdp.py --help")

if __name__ == '__main__':
    main()