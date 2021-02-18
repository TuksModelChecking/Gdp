from sys import argv
from yaml import load

class TabTrackingWriter:
    def __init__(self, file):
        self.file = file
        self.tab_depth = 0

    def __del__(self):
        self.file.close()

    def write(self, string):
        tabs = ("\t" * self.tab_depth)
        self.file.write(f"{tabs}{string}\n")

    def write_tab(self, string):
        self.write(string)
        self.tab_depth += 1

    def untab_write(self, string):
        self.tab_depth -= 1
        self.write(string)

def take_condition(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"{resource} = 0 and {agent}.Action = req{r_id}"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def others_not_requesting(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"Environment.{resource} = 0"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def agents_in_group(num_agents, g):
    agents = g.split('A')[1:]
    agents_explicit = []
    last_agent = None
    for agent in agents:
        if agent.endswith(".."):
            last_agent = agent[:-2]
            continue
        if last_agent != None:
            for i in range(int(last_agent), int(agent)):
                agents_explicit.append(i)
            last_agent = None
        if int(agent) > num_agents or int(agent) < 1:
            print(f"\n\terror: agent A{agent} is not defined.\n")
            raise IOError
        agents_explicit.append(agent)
    return agents_explicit

def all_agents(num_agents):
    agent_set = "{"
    for agent in range(1, num_agents):
        agent_set += f"A{agent},"
    agent_set += f"A{num_agents}"
    return "ALL = " + agent_set + "};"

def all_except(num_agents, g):
    to_exclude = agents_in_group(num_agents, g)
    agent_set = "{"
    for agent in range(1, num_agents):
        if agent not in to_exclude:
            agent_set += f"A{agent},"
    return "ex" + g + " = " + agent_set[:-1] + "};"

def specified_group(num_agents, g):
    agents = agents_in_group(num_agents, g)
    group_name = ""
    agent_set = "{"
    for a in agents:
        group_name += f"A{a}"
        agent_set += f"A{a},"
    agent_set = agent_set[:-1] + "};"
    return group_name + " = " + agent_set

def groups_to_ispl(num_agents, groups):
    ispl_groups = []
    for g in groups:
        if g == "ALL":
            ispl_groups.append(all_agents(num_agents))
        elif g.startswith("ex"):
            ispl_groups.append(all_except(num_agents, g[2:]))
        else:
            ispl_groups.append(specified_group(num_agents, g))
    return ispl_groups

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
        file = open(filename, "r")
        print(f"Opening file '{filename}'...")
    except IOError:
        print(f"Tried and failed to open '{filename}'")
        print("Are you sure the filename and relative path is correct?")
        exit()
else:
    print(f"Guessing file extension...")
    try:
        file = open(filename + ".yaml", "r" )
        print(f"Opening file '{filename}.yaml'...")
    except IOError:
        print(f"Tried and failed to open '{filename}.yaml'")
        try: 
            file = open(filename + ".txt", "r")
            print(f"Opening file '{filename}.txt'...")
        except IOError:
            print(f"Tried and failed to open '{filename}.txt'")
            print("Are you sure the filename and relative path is correct?")
            exit()
gdp = load(file)

print("Parsing model to ISPL...")

file = open("out.ispl", "w")
tw = TabTrackingWriter(file)
num_agents = len(gdp["agents"])

tw.write("Semantics=SingleAssignment;\n")

tw.write_tab("Agent Environment")
tw.write_tab("Vars:")
for r in gdp["resources"]:
    #Perhaps optimize here to only allow resources to be held by Agents that actually have access to them?
    tw.write(f"{r}: 0..{num_agents};")
tw.untab_write("end Vars")
tw.write("Actions = {none};\n\tProtocol:\n\t\tOther: {none};\n\tend Protocol")
tw.write_tab("Evolution:")
for r in gdp["resources"]:
    for a in gdp["agents"]:
        if r in gdp[a]["access"]:
            tw.write(f"{r} = {a[1:]} if ({take_condition(r, a, gdp)});")
            tw.write(f"{r} = 0 if ({r} = {a[1:]} and {a}.Action = rel{r[1:]});")
            tw.write(f"{r} = 0 if ({r} = {a[1:]} and {a}.Action = relall);")
tw.untab_write("end Evolution")
tw.untab_write("end Agent\n")

for a in gdp["agents"]:
    tw.write_tab(f"Agent {a}")
    actions = "{"
    lobsvars = "{"
    for r in gdp[a]["access"]:
        actions += f"req{r[1:]},"
        actions += f"rel{r[1:]},"
        lobsvars += r
        lobsvars += ","
    if len(lobsvars) == 1:
        lobsvars = "{none};"
        actions = "{idle};"
    else:
        actions = actions[:-1] + ",relall,idle};"
        lobsvars = lobsvars[:-1] + "};"
    tw.write(f"Lobsvars = {lobsvars}")
    tw.write_tab("Vars:")
    demand = gdp[a]["demand"]
    tw.write(f"rem: 0..{demand};")
    tw.untab_write("end Vars")
    tw.write(f"Actions = {actions}")
    tw.write_tab("Protocol:")
    tw.write("rem = 0 : {relall};")
    tw.write("rem > 0 : {idle};")
    for my_r in gdp[a]["access"]:
        req = "{req" + my_r[1:] + "}"
        rel = "{rel" + my_r[1:] + "}"
        tw.write(f"rem > 0 and Environment.{my_r} = 0 : {req};")
        tw.write(f"rem > 0 and Environment.{my_r} = {a[1:]} : {rel};")
    tw.untab_write("end Protocol")
    tw.write_tab("Evolution:")
    for my_r in gdp[a]["access"]:
        onr = others_not_requesting(my_r, a, gdp)
        tw.write(f"rem = rem-1 if (Action = req{my_r[1:]} and Environment.{my_r} = 0 and {onr});")
        tw.write(f"rem = rem+1 if (Action = rel{my_r[1:]});")
        tw.write(f"rem = {gdp[a]['demand']} if (Action = relall);")
    tw.untab_write("end Evolution")
    tw.untab_write(f"end Agent\n")

tw.write_tab("Evaluation")
for a in gdp["agents"]:
    tw.write(f"eat{a[1:]} if ({a}.rem=0);")
tw.untab_write("end Evaluation\n")

tw.write_tab("InitStates")
for r in gdp["resources"]:
    tw.write(f"Environment.{r}=0 and")
agents = gdp["agents"]
for i in range(0, len(agents)-1):
    tw.write(f"{agents[i]}.rem = {gdp[agents[i]]['demand']} and")
tw.write(f"{agents[len(agents)-1]}.rem = {gdp[agents[len(agents)-1]]['demand']};")
tw.untab_write("end InitStates\n")

tw.write_tab("Groups")
for g in groups_to_ispl(len(gdp["agents"]), gdp["groups"]):
    tw.write(g)
tw.untab_write("end Groups\n")

tw.write_tab("Formulae")
for f in gdp["formulae"]:
    tw.write(f)
tw.untab_write("end Formulae\n")

tw.__del__()
print("done, 'out.ispl' created")