from sys import argv
from random import randint
from yaml import safe_dump

def generate_philosophers(num_p, num_r, demand_range):
    max_demand = randint(int(demand_range[0]), int(demand_range[1]))
    gdp = {}
    gdp["agents"] = [f"A{i}" for i in range(1, num_p+1)]
    gdp["resources"] = [f"r{i}" for i in range(1, num_r+1)]
    for a in gdp["agents"]:
        gdp[a] = {}
        gdp[a]["demand"] = randint(int(demand_range[0]), max_demand)
        gdp[a]["access"] = []
        for i in range(0, randint(gdp[a]["demand"], max_demand)):
            start_point = randint(0, num_r)
            for c in range(0, num_r):
                print((start_point + c) % num_r)
                choice = gdp["resources"][(start_point + c) % num_r]
                if choice not in gdp[a]["access"]:
                    gdp[a]["access"].append(choice)
                    break
                else: 
                    start_point += 1
        gdp[a]["access"].sort()
    gdp["groups"] = [
        u'A1A2',
        u'ALL',
        u'exA1A2'
    ]
    gdp["formulae"] = [
        u'<ALL>G ((<ALL>F eat1) and (<ALL>F eat2) and (<ALL>F eat3));',
        u'<A1A2>G ((<A1A2>F eat1) and (<exA1A2>F eat2));'
    ]
    return gdp

def random_generation():
    minimum = randint(0, 50)
    maximum = randint(minimum, 100)
    return generate_philosophers(randint(1, 100), randint(1, maximum), (minimum, maximum))

if len(argv) < 2:
    print("No arguments provided")
    print("To generate a totally random GDP run this script with only the -r flag")
    print("\texample: $ python3 generategdp.py -r")
    print("To set the number of philosophers and the demand range, run the script like this:")
    print("\tgenerally: $ python3 generategdp.py <num_philosophers> <num_resources> <min demand>..<max_demand>")
    print("\texample: $ python3 generategdp.py 5 4 1..4\n")
    decision = input("Generate a fully randomized GDP now? (Y/N) ")
    if "Y" in decision.capitalize():
        gdp = random_generation()
    decision = input("Generate a bounded random GDP now? (Y/N) ")
    if "Y" in decision.capitalize():
        gdp = random_generation(
            input("Number of Philosophers? (int) "),
            input("Number of Resources? (int)"),
            input("Demand range? (x..y) [with y ≤ num_resources]: ")
        )
elif argv[1] == "-r":
    gdp = random_generation()
else:
    flag = False
    if not argv[1].isdigit():
        print("error: number of philosophers must be an integer")
        flag = True
    if not argv[2].isdigit():
        print("error: number of resources must be an integer")
    if not len(argv[3]) > 3 and argv[3].contains(".."):
        print("error: demand range must be a string of the form <lower-bound-as-int>..<upper-bound-as-int>")
        flag = True
    if flag:
        exit()
    gdp = generate_philosophers(int(argv[1]), int(argv[2]), argv[3].split(".."))
with open("generated_gdp.yaml", "w") as outfile:
    safe_dump(gdp, outfile, default_flow_style=False)