# -*- coding: utf-8 -*-

import os

NUMBER_OF_PROCESSES = 6
base_dir = "python"
cw_dir = os.getcwd()
fp_dir = cw_dir + "/" + base_dir
launch_it = "python -u -m {BD}.launch {NP} {FP}".format(
    BD=base_dir, NP=NUMBER_OF_PROCESSES, FP=fp_dir)
os.system(launch_it)
