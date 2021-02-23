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
    condition = f"{resource} = 0 and {agent}.Action = req{r_id}"
    for i in range(1, NUM_AGENTS+1):
        a = f"A{i}"
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def others_not_requesting(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"Environment.{resource} = 0"
    for i in range(1, NUM_AGENTS+1):
        a = f"A{i}"
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def agents_in_group(g):
    agents = g.split('A')[1:]
    agents_explicit = []
    last_agent = None
    for agent in agents:
        if agent.endswith("_"):
            last_agent = agent[:-1]
            continue
        if last_agent != None:
            for i in range(int(last_agent), int(agent)):
                agents_explicit.append(i)
            last_agent = None
        if int(agent) > NUM_AGENTS or int(agent) < 1:
            print(f"\n\terror: agent A{agent} is not defined.\n")
            raise IOError
        agents_explicit.append(agent)
    return agents_explicit

def all_agents():
    agent_set = set()
    for agent in range(1, NUM_AGENTS + 1):
        agent_set.add(f"A{agent}")
    return agent_set

def all_except(g):
    to_exclude = agents_in_group(g)
    agent_set = set()
    for agent in range(1, NUM_AGENTS + 1):
        if agent not in to_exclude:
            agent_set.add(f"A{agent}")
    return agent_set

def specified_group(g):
    agents = agents_in_group(g)
    agent_set = set()
    for a in agents:
        agent_set.add(f"A{a}")
    return agent_set

def explicit_agent_set(g):
    if g == "all":
        return all_agents()
    elif g.startswith("ex"):
        return all_except(g[2:])
    else:
        return specified_group(g)

def groups_to_ispl(groups):
    return [(g + " = " + str(explicit_agent_set(g)).replace('\'','') + ";") for g in groups]

def generate_achieve(acting_group):
    achieve = ""
    for a in explicit_agent_set(acting_group):
        achieve += f"(<{acting_group}>F eat{a[1:]}) and "
    return achieve[:-5] + ";"

def generate_live(acting_group):
    live = f"<{acting_group}>G ("
    for a in explicit_agent_set(acting_group):
        live += f"(<{acting_group}>F eat{a[1:]}) and "
    return live[:-5] + ");"

def generate_prevent(acting_group):
    prevent = f"<{acting_group}>G ("
    for i in range(1, NUM_AGENTS+1):
        if f"A{i}" not in explicit_agent_set(acting_group):
            prevent += f"!eat{i} and "
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
NUM_AGENTS = gdp["num_agents"]
OBSERVABLE = explicit_agent_set(
    gdp["observable"].strip()[1:-1]
)

ispl_file = open("out.ispl", "w")
tw = TabTrackingWriter(ispl_file)

tw.write("Semantics=SingleAssignment;\n")

tw.write_tab("Agent Environment")
tw.write_tab("Vars:")
for i in range(1, gdp["num_resources"]+1):
    #Perhaps optimize here to only allow resources to be held by Agents that actually have access to them?
    tw.write(f"r{i}: 0..{NUM_AGENTS};")
for a in OBSERVABLE:
    demand = gdp[a]["demand"]
    tw.write(f"rem{a[1:]} : 0..{demand};")
tw.untab_write("end Vars")
tw.write("Actions = {none};\n\tProtocol:\n\t\tOther: {none};\n\tend Protocol")
tw.write_tab("Evolution:")
for i in range(1, gdp["num_resources"]+1):
    r = f"r{i}"
    for i in range(1, NUM_AGENTS+1):
        a = f"A{i}"
        if r in gdp[a]["access"]:
            tw.write(f"{r} = {i} if ({take_condition(r, a, gdp)});")
            tw.write(f"{r} = 0 if ({r} = {i} and A{i}.Action = rel{r[1:]});")
            tw.write(f"{r} = 0 if ({r} = {i} and A{i}.Action = relall);")
            if a in OBSERVABLE:
                tw.write(f"rem{i} = rem{i}-1 if ({take_condition(r, a, gdp)});")
                tw.write(f"rem{i} = rem{i}+1 if ({r} = {i} and A{i}.Action = rel{r[1:]});")
                tw.write(f"rem{i} = {gdp[a]['demand']} if ({r} = {i} and A{i}.Action = relall);")
        
tw.untab_write("end Evolution")
tw.untab_write("end Agent\n")

for i in range(1, NUM_AGENTS+1):
    agent = f"A{i}"
    tw.write_tab(f"Agent A{i}")
    actions = "{"
    lobsvars = "{"
    for r in gdp[agent]["access"]:
        actions += f"req{r[1:]},"
        actions += f"rel{r[1:]},"
        lobsvars += r
        lobsvars += ","
    for a in OBSERVABLE:
        lobsvars += f"rem{a[1:]},"
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
        req = "{req" + my_r[1:] + "}"
        rel = "{rel" + my_r[1:] + "}"
        tw.write(f"rem > 0 and Environment.{my_r} = 0 : {req};")
        tw.write(f"rem > 0 and Environment.{my_r} = {i} : {rel};")
    tw.untab_write("end Protocol")
    tw.write_tab("Evolution:")
    for my_r in gdp[agent]["access"]:
        onr = others_not_requesting(my_r, agent, gdp)
        tw.write(f"rem = rem-1 if (Action = req{my_r[1:]} and Environment.{my_r} = 0 and {onr});")
        tw.write(f"rem = rem+1 if (Action = rel{my_r[1:]});")
        tw.write(f"rem = {gdp[agent]['demand']} if (Action = relall);")
        if gdp["fairness"] != None and gdp["fairness"] == "-on":
            tw.write(f"idl = false if (Action = req{my_r[1:]} and Environment.{my_r} = 0 and {onr});")
            tw.write(f"idl = false if (Action = rel{my_r[1:]});")
            tw.write(f"idl = false if (Action = relall);")
            tw.write(f"idl = true if (Action = idle);")
    tw.untab_write("end Evolution")
    tw.untab_write(f"end Agent\n")

tw.write_tab("Evaluation")
for i in range(1, NUM_AGENTS+1):
    tw.write(f"eat{i} if (A{i}.rem=0);")
if gdp["fairness"] != None and gdp["fairness"] == "-on":
    for i in range(1, NUM_AGENTS+1):
        tw.write(f"not_idle{i} if (A{i}.idl=false);")
tw.untab_write("end Evaluation\n")

tw.write_tab("InitStates")
for i in range(1, gdp["num_resources"]+1):
    r = f"r{i}"
    tw.write(f"Environment.{r}=0 and")
agents = [f"A{i}" for i in range(1, NUM_AGENTS+1)]
for a in OBSERVABLE:
    tw.write(f"Environment.rem{a[1:]}={gdp[a]['demand']} and")
for i in range(0, NUM_AGENTS-1):
    tw.write(f"{agents[i]}.rem={gdp[agents[i]]['demand']} and")
tw.write(f"{agents[NUM_AGENTS-1]}.rem={gdp[agents[NUM_AGENTS-1]]['demand']};")
tw.untab_write("end InitStates\n")

tw.write_tab("Groups")
for g in groups_to_ispl(deduce_groups_from(gdp["formulae"])):
    tw.write(g)
tw.untab_write("end Groups\n")

tw.write_tab("Fairness")
if gdp["fairness"] != None and gdp["fairness"] == "-on":
    for i in range(1, NUM_AGENTS+1):
        tw.write(f"not_idle{i};")
tw.untab_write("end Fairness\n")

tw.write_tab("Formulae")
for f in gdp["formulae"]:
    tw.write(generate_ispl_formula(f))
tw.untab_write("end Formulae\n")

tw.__del__()
print("done, 'out.ispl' created")