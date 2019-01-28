#!/bin/bash

# The commandline argument gives the number of threads to run.
NUMBER_OF_THREADS=$1

python -m python $NUMBER_OF_THREADS
./get_iops.sh