from sys import argv
from yaml import load

class TabTrackingWriter:
    def __init__(self, ispl_file):
        self.ispl_file = ispl_file
        self.tab_depth = 0

    def __del__(self):
        self.ispl_file.close()

    def write(self, string):
        tabs = ("\t" * self.tab_depth)
        self.ispl_file.write(f"{tabs}{string}\n")

    def write_tab(self, string):
        self.write(string)
        self.tab_depth += 1

    def untab_write(self, string):
        self.tab_depth -= 1
        self.write(string)

def deduce_groups_from(formulae):
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

def take_condition(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"{resource}=none and {agent}.Action=req_{resource}"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action=req_{resource})"
    return condition

def others_not_requesting(resource, agent, gdp):
    condition = f"Environment.{resource} = none"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action=req_{resource})"
    return condition

def agents_in_group(g):
    agents = g.split("_")
    agents_explicit = set()
    last_agent = None
    fill_gap = False
    for agent in agents:
        if agent == "":
            fill_gap = True
            continue
        if fill_gap:
            for i in range(AGENTS.index(last_agent)+1, AGENTS.index(agent)): ## list has to be sorted correctly
                agents_explicit.add(AGENTS[i])
            fill_gap = False
        agents_explicit.add(agent)
        last_agent = agent
    return agents_explicit

def all_except(g):
    to_exclude = agents_in_group(g)
    agent_set = set()
    for agent in AGENTS:
        if agent not in to_exclude:
            agent_set.add(agent)
    return agent_set

def explicit_agent_set(g):
    if g == "all":
        return set(AGENTS)
    elif g.startswith("EX"):
        return all_except(g[2:])
    else:
        return agents_in_group(g)

def groups_to_ispl(groups):
    return [(g + " = " + str(explicit_agent_set(g)).replace('\'','') + ";") for g in groups]

def generate_achieve(acting_group):
    achieve = ""
    for a in explicit_agent_set(acting_group):
        achieve += f"(<{acting_group}>F {a}_eat) and "
    return achieve[:-5] + ";"

def generate_live(acting_group):
    live = f"<{acting_group}>G ("
    for a in explicit_agent_set(acting_group):
        live += f"(<{acting_group}>F {a}_eat) and "
    return live[:-5] + ");"

def generate_prevent(acting_group):
    prevent = f"<{acting_group}>G ("
    for a in AGENTS:
        if a not in explicit_agent_set(acting_group):
            prevent += f"!{a}_eat and "
    return prevent[:-5] + ");"

def generate_ispl_formula(formula):
    formula = formula.strip()
    group = formula[formula.find('<')+1:formula.find('>')]
    if formula.endswith("achieve"):
        return generate_achieve(group)
    elif formula.endswith("live"):
        return generate_live(group)
    elif formula.endswith("prevent"):
        return generate_prevent(group)
    else:
        return formula

# ============================================================================


if len(argv) < 2:
    print("No GDP file specified")
    print("You can specify a file when running the script, like this:")
    print("\t$ python3 parsegdp.py 5phil.yaml")
    print("\tor more generally:")
    print("\t$ python3 parsegdp.py <relative_file_path>/<filename>.<yaml/txt>")
    print("\tyou may omit the file extension; making your command of the form:")
    print("\t$ python3 parsegdp.py <relative_file_path>/<filename>")
    filename = input("\nSpecify a file now: ")
else:
    filename = argv[1]
if filename.endswith((".txt",".yaml")):
    try:
        gdp_file = open(filename, "r")
        print(f"Opening file '{filename}'...")
    except IOError:
        print(f"Tried and failed to open '{filename}'")
        print("Are you sure the filename and relative path is correct?")
        exit()
else:
    print(f"Guessing file extension...")
    try:
        gdp_file = open(filename + ".yaml", "r" )
        print(f"Opening file '{filename}.yaml'...")
    except IOError:
        print(f"Tried and failed to open '{filename}.yaml'")
        try: 
            gdpl_file = open(filename + ".txt", "r")
            print(f"Opening file '{filename}.txt'...")
        except IOError:
            print(f"Tried and failed to open '{filename}.txt'")
            print("Are you sure the filename and relative path is correct?")
            exit()        
gdp = load(gdp_file)
print("Parsing model to ISPL...")
AGENTS = sorted(gdp["agents"])
RESOURCES = sorted(gdp["resources"])
NUM_AGENTS = len(AGENTS)
NUM_RESOURCES = len(RESOURCES)
OBSERVABLE = explicit_agent_set(
    gdp["observable"].strip()[1:-1]
)

ispl_file = open("out.ispl", "w")
tw = TabTrackingWriter(ispl_file)

tw.write("Semantics=SingleAssignment;\n")

tw.write_tab("Agent Environment")
tw.write_tab("Vars:")
for r in RESOURCES:
    valid_vars = "{none,"
    for a in AGENTS:
        if r in gdp[a]["access"]:
            valid_vars += f"{a},"
    valid_vars = valid_vars[:-1] + "}"
    tw.write(f"{r}: {valid_vars};")
for a in OBSERVABLE:
    demand = gdp[a]["demand"]
    tw.write(f"rem_{a} : 0..{demand};")
tw.untab_write("end Vars")
tw.write("Actions = {none};\n\tProtocol:\n\t\tOther: {none};\n\tend Protocol")
tw.write_tab("Evolution:")
for r in RESOURCES:
    for a in AGENTS:
        if r in gdp[a]["access"]:
            tw.write(f"{r}={a} if ({take_condition(r, a, gdp)});")
            tw.write(f"{r}=none if ({r}={a} and {a}.Action=rel_{r});")
            tw.write(f"{r}=none if ({r}={a} and {a}.Action=relall);")
            if a in OBSERVABLE:
                tw.write(f"rem_{a}=rem_{a}-1 if ({take_condition(r, a, gdp)});")
                tw.write(f"rem_{a}=rem_{a}+1 if ({r}={a} and {a}.Action=rel_{r});")
                tw.write(f"rem_{a}={gdp[a]['demand']} if ({r}={a} and {a}.Action=relall);")
        
tw.untab_write("end Evolution")
tw.untab_write("end Agent\n")

for agent in AGENTS:
    agent
    tw.write_tab(f"Agent {agent}")
    actions = "{"
    lobsvars = "{"
    for r in gdp[agent]["access"]:
        actions += f"req_{r},"
        actions += f"rel_{r},"
        lobsvars += r
        lobsvars += ","
    for a in OBSERVABLE:
        lobsvars += f"rem_{a},"
    if len(lobsvars) == 1:
        lobsvars = "{none};"
        actions = "{idle};"
    else:
        actions = actions[:-1] + ",relall,idle};"
        lobsvars = lobsvars[:-1] + "};"
    tw.write(f"Lobsvars = {lobsvars}")
    tw.write_tab("Vars:")
    demand = gdp[agent]["demand"]
    tw.write(f"rem : 0..{demand};")
    if gdp["fairness"] != None and gdp["fairness"] == "-on":
        tw.write(f"idl : boolean;")
    tw.untab_write("end Vars")
    tw.write(f"Actions = {actions}")
    tw.write_tab("Protocol:")
    tw.write("rem = 0 : {relall};")
    tw.write("rem > 0 : {idle};")
    for my_r in gdp[agent]["access"]:
        req = "{req_" + my_r + "}"
        rel = "{rel_" + my_r + "}"
        tw.write(f"rem > 0 and Environment.{my_r}=none : {req};")
        tw.write(f"rem > 0 and Environment.{my_r}={agent} : {rel};")
    tw.untab_write("end Protocol")
    tw.write_tab("Evolution:")
    for my_r in gdp[agent]["access"]:
        onr = others_not_requesting(my_r, agent, gdp)
        tw.write(f"rem=rem-1 if (Action=req_{my_r} and Environment.{my_r}=none and {onr});")
        tw.write(f"rem=rem+1 if (Action=rel_{my_r});")
        tw.write(f"rem={gdp[agent]['demand']} if (Action=relall);")
        if gdp["fairness"] != None and gdp["fairness"] == "-on":
            tw.write(f"idl=false if (Action=req_{my_r} and Environment.{my_r}=none and {onr});")
            tw.write(f"idl=false if (Action=rel_{my_r});")
            tw.write(f"idl=false if (Action=relall);")
            tw.write(f"idl=true if (Action=idle);")
    tw.untab_write("end Evolution")
    tw.untab_write(f"end Agent\n")

tw.write_tab("Evaluation")
for a in AGENTS:
    tw.write(f"{a}_eat if ({a}.rem=0);")
if gdp["fairness"] != None and gdp["fairness"] == "-on":
    for a in AGENTS:
        tw.write(f"not_idle_{a} if ({a}.idl=false);")
tw.untab_write("end Evaluation\n")

tw.write_tab("InitStates")
for r in RESOURCES:
    tw.write(f"Environment.{r}=none and")
for a in OBSERVABLE:
    tw.write(f"Environment.rem_{a}={gdp[a]['demand']} and")
for i in range(1, NUM_AGENTS-1):
    tw.write(f"{AGENTS[i]}.rem={gdp[AGENTS[i]]['demand']} and")
tw.write(f"{AGENTS[NUM_AGENTS-1]}.rem={gdp[AGENTS[NUM_AGENTS-1]]['demand']};")
tw.untab_write("end InitStates\n")

tw.write_tab("Groups")
for g in groups_to_ispl(deduce_groups_from(gdp["formulae"])):
    tw.write(g)
tw.untab_write("end Groups\n")

tw.write_tab("Fairness")
if gdp["fairness"] != None and gdp["fairness"] == "-on":
    for a in AGENTS:
        tw.write(f"not_idle_{a};")
tw.untab_write("end Fairness\n")

tw.write_tab("Formulae")
for f in gdp["formulae"]:
    tw.write(generate_ispl_formula(f))
tw.untab_write("end Formulae\n")

tw.__del__()
print("done, 'out.ispl' created")