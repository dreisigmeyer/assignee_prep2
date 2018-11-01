#!/bin/bash

NUMBER_OF_THREADS=$1

python -m python $NUMBER_OF_THREADS
./get_iops.sh