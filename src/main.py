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

    def write_tab(self, str):
        self.write(str)
        self.tab_depth += 1

    def untab_write(self, str):
        self.tab_depth -= 1
        self.write(str)

    def tab(self):
        self.tab_depth += 1

    def untab(self):
        self.tab_depth -= 1



with open("gdp.yaml", "r") as gdp_yaml:
    gdp = yaml.load(open("gdp.yaml", "r"))

file = open("out.ispl", "w")
tw = TabbedWriter(file)


tw.write("Semantics=SingleAssignment;")

tw.write_tab("Agent Environment")
tw.write_tab("Vars")
tw.untab_write("end Vars")
tw.untab_write("end Agent")

for a in gdp["agents"]:
    tw.write_tab(f"Agent {a}")
    tw.write("...")
    tw.untab_write(f"end {a}")

tw.write_tab("Evaluation")
tw.untab_write("end Evaluation")

tw.write_tab("InitStates")
tw.untab_write("end InitStates")

tw.write_tab("Groups")
tw.untab_write("end Groups")

tw.write_tab("Formulae")
tw.untab_write("end Formulae")