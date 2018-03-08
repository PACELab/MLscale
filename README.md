# MLscale
[MLscale:](http://www3.cs.stonybrook.edu/~anshul/suscom17.pdf) Application agnostic autoscaling using blackbox machine learning

## What is MLscale?
MLscale is an approach to drive autoscaling engine of a multi-tiered cloud application using machine learning to learn the relationship 
between performance and several system and application level metrics.
MLscale collects these metrics and the performance target such as response time during the training phase and then builds models using 
neural network and linear regression which are then used for predictions in the autoscaling engine.

## Scripts included:
Most of the codebase is python scripts which interact with the system using subprocess module.

`tensecscale.py` implements prototype of MLscale by using a prebuilt neural network model as well as linear regression coefficients stored in `bvalues.py`

`cputhreshscale.py` and `naivescale.py` implement CPU threshold based scaling and naive reactive scaling respectively.

### Setup
Experimental setup included a load-generator (httperf), load-balancer (apache) and a tier of webservers.
Some detail on configuration is given in `setup.txt` and libraries required in `workersetup.sh`

### Misc scripts
Scripts for neural networking learning and experiment trace generation are also included. Linear regression code not included,
it is a one liner in MATLAB.
