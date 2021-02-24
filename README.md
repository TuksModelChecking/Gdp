# gdp
Generalized Dining Philosophers

### Summary
A tool that converts shorthand GDP input into an explicilty defined input file for the MCMAS model checker.

### Required
* MCAMS
  *
* python3
  * windows/mac (https://www.python.org/downloads/release/python-381/)
  * linux $ sudo apt-get install python3.6 (https://docs.python-guide.org/starting/install3/linux/)

### Usage Guide
1) Get the parsegdp.py file (located in src in this project) <br>
2) Navigate to the directory where you saved parsegdp.py and run the following commands: <br>
$ python3 parsegdp.py -txt <br>
_this will generate a template file explaining how you can define the GDP_ <br>
$ python3 parsegdp.py template.txt <br>
_this will output out.ispl_<br>
2) Run MCMAS with out.ispl as our input
