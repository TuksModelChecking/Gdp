import yaml

class TabbedWriter:
    def __init__(self, file):
        self.file = file
        self.tab_depth = 0

    def __del__(self):
        self.file.close()

    def write(self, str):
        tabs = ("\t" * self.tab_depth)
        self.file.write(f"{tabs}{str}\n")

    def write_tab(self, string):
        self.write(string)
        self.tab_depth += 1

    def untab_write(self, string):
        self.tab_depth -= 1
        self.write(string)


with open("gdp.yaml", "r") as gdp_yaml:
    gdp = yaml.load(open("gdp.yaml", "r"))

file = open("out.ispl", "w")
tw = TabbedWriter(file)
num_agents = len(gdp["agents"])

tw.write("Semantics=SingleAssignment;\n")

tw.write_tab("Agent Environment")
tw.write_tab("Vars:")
for v in gdp["resources"]:
    tw.write(f"{v}: 0..{num_agents};")
tw.untab_write("end Vars")
tw.write("Actions = {none};\n\tProtocol:\n\t\tOther: {none};\n\tend Protocol")
tw.untab_write("end Agent\n")

for a in gdp["agents"]:
    tw.write_tab(f"Agent {a}")
    lobsvars = "{"
    for v in gdp[a]["access"]:
        lobsvars += v
        lobsvars += ","
    lobsvars = lobsvars[:-1] + "};"
    tw.write(f"Lobsvars = {lobsvars}")
    tw.write_tab("Vars:")
    demand = gdp[a]["demand"]
    tw.write(f"rem: 0..{demand};")
    tw.untab_write("end Vars")
    tw.untab_write(f"end Agent\n")

tw.write_tab("Evaluation")
tw.untab_write("end Evaluation\n")

tw.write_tab("InitStates")
tw.untab_write("end InitStates\n")

tw.write_tab("Groups")
for g in gdp["groups"]:
    tw.write(g)
tw.untab_write("end Groups\n")

tw.write_tab("Formulae")
for f in gdp["formulae"]:
    tw.write(f)
tw.untab_write("end Formulae\n")