from sys import argv
from random import random

def generate_philosophers(num_p, demand_range):
    num_resources = random(demand_range[0], demand_range[1])
    gdp = {}
    gdp["agents"] = [f"A{i}" for i in range(1, num_p)]
    gdp["resources"] = [f"r{i}" for i in range(1, num_p)]
    for a in gdp["agents"]:
        gdp[a]["demamd"] = random(demand_range[0], num_resources)
        access = []
    return gdp

def random_generation():
    minimum = random(0, 50)
    maximum = random(minimum, 100)
    return generate_philosophers(random(1, 100), (minimum, maximum))

if len(argv) < 2:
    print("No arguments provided")
    print("To generate a totally random GDP run this script with only the -r flag")
    print("\texample: $ python3 generategdp.py -r")
    print("To set the number of philosophers and the demand range, run the script like this:")
    print("\tgenerally: $ python3 generategdp.py <num_philosophers> <min demand>..<max_demand>")
    print("\texample: $ python3 generategdp.py 5 1..4\n")
    decision = input("Generate a fully randomized GDP now? (Y/N) ")
    if "Y" in decision.capitalize():
        gdp = random_generation()
    decision = input("Generate a bounded random GDP now? (Y/N) ")
    if "Y" in decision.capitalize():
        gdp = random_generation(input("Number of Philosophers? (int) "), input("Demand range? (x..y) "))
elif argv[1] == "-r":
    gdp = random_generation()
else:
    flag = False
    if not isinstance(argv[1], int):
        print("error: the number of philosophers must be an integer")
        flag = True
    if not isinstance(argv[2], str):
        print("The demand range must be a string of the form <lower-bound-as-int>..<upper-bound-as-int>")
        flag = True
    if flag:
        exit()  
    print(type(1))
    gdp = random_generation(argv[1], argv[2])
