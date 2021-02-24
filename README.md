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
get the parsegdp.py file (located in src in this project) 
in the directory where you saved it run the following commands
$ python3 parsegdp.py -txt
this will generate a template file explaining how you can define the GDP
$ python3 parsegdp.py template.txt
this will output out.ispl
simply run MCMAS with this out.ispl as our input
