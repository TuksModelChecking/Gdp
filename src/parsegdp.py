import sys
import yaml

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

def takeCondition(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"{resource} = 0 and {agent}.Action = req{r_id}"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def othersNotRequesting(resource, agent, gdp):
    a_id = agent[1:]
    r_id = resource[1:]
    condition = f"Environment.{resource} = 0"
    for a in gdp["agents"]:
        if a != agent and resource in gdp[a]["access"]:
            condition += f" and !({a}.Action = req{r_id})"
    return condition

def generate_philosophers(num_p, demand_range):
    gdp = []
    return gdp

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

if len(sys.argv) > 2:
    print(f"Generating a GDP model of {sys.argv[1]} Philosophers - each with random demand within {sys.argv[2]}...")
    gdp = generate_philosophers(sys.argv[1], sys.argv[2])
elif len(sys.argv) == 2:
    filename = sys.argv[1]
    print(f"Reading model from file '{filename}'...")
    if filename.endswith((".txt",".yaml")):
        file = open(filename, "r")
    else:
        try:
            file = open(filename + ".yaml", "r" )
        except IOError:
            try: 
                file = open(filename + ".txt", "r")
            except IOError:
                pass
    gdp = yaml.load(file)
else:
    print("Generating a completely random GDP model...")
    gdp = generate_philosophers()

print("Parsing to ISPL...")

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
            tw.write(f"{r} = {a[1:]} if ({takeCondition(r, a, gdp)});")
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
        onr = othersNotRequesting(my_r, a, gdp)
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

