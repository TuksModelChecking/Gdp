# gdp
Generalized Dining Philosophers

### Summary
A tool that converts shorthand GDP input into an explicilty defined input file for the MCMAS model checker.

### Required
* MCAMS
  * place link here
* python3
  * windows/mac (https://www.python.org/downloads/release/python-381/)
  * linux $ sudo apt-get install python3.6 (https://docs.python-guide.org/starting/install3/linux/)

### Usage Guide
1) Get the gifg.py file (located in gdp_tool in this project) <br>
2) Navigate to the directory where you saved gigf.py and run the following commands: <br>
$ python3 gifg.py --help <br>(get info on how the tool should be used at any time)<br>
$ python3 gifg.py -g model_name.txt 3 <br>
(Generates a template file with 3 agents. User must manually define rest of GDP in model_name.txt) <br>
$ python3 gifg.py -gdp model_name.txt -o -f -ispl m13.ispl <br>
(Parse model; turn on observability and fairness; output as m13.ispl) <br>
3) Run MCMAS with out.ispl as our input
