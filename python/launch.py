# -*- coding: utf-8 -*-

import csv
import glob
import json
import os
import random
import sys
import get_assignee_information
from multiprocessing import Process

number_of_processes = int(sys.argv[1])
cw_dir = sys.argv[2]


def split_seq(seq, num_processes):
    """
    Slices a list into number_of_processes pieces
    of roughly the same size
    """
    num_files = len(seq)
    if num_files < num_processes:
        num_processes = num_files
    size = num_processes
    newseq = []
    splitsize = 1.0 / size * num_files
    for i in range(size):
        newseq.append(
            seq[int(round(i * splitsize)):int(round((i + 1) * splitsize))])
    return newseq


def get_assignee_info(directory):
    uspto_files = glob.glob(directory + "/*.TXT")
    uspto_files.sort()
    asg_names = {}
    pat_asg_info = {}
    with open(uspto_files[0]) as asg_names_file:
        for line in asg_names_file:
            asg_num = line[:7].strip()
            asg_name = line[8:].strip()
            asg_names[asg_num] = asg_name
    with open(uspto_files[1]) as pat_names_file:
        for line in pat_names_file:
            pat_num = line[:7]
            trash, pat_num = get_assignee_information.clean_patnum(pat_num)
            asg_num_1 = line[8:15].strip()
            asg_num_2 = line[16:].strip()
            pat_asg_info[pat_num] = [
                asg_names[asg_num_1], asg_names[asg_num_2]]
    return pat_asg_info


def get_standard_names(directory):
    standard_names_file = "standard_names.csv"
    standard_names = {}
    with open(standard_names_file, newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        for line in csv_reader:
            try:
                xml_name = line[0]
                grant_yr = line[1]
                standardized_name = line[2]
                standard_names[xml_name][grant_yr] = standardized_name
            except Exception as e:
                pass
    return standard_names


# Start processing
uspto_dir = 'uspto_data/'
path_to_data = 'in_data/'
path_to_JSON = 'python/json_data/'
files = glob.glob(os.path.join(path_to_data, "*.bz2"))
random.shuffle(files)  # Newer years have more granted patents
files_list = split_seq(files, number_of_processes)
if __name__ == '__main__':
    pat_assg_info = get_assignee_info(uspto_dir)
    standard_names = get_standard_names(uspto_dir)
    with open(path_to_JSON + 'city_state_to_zip3.json') as json_data:
        zips_dict = json.load(json_data)
    with open(path_to_JSON + 'city_misspellings.json') as json_data:
        cities_dict = json.load(json_data)
    procs = []
    for chunk in files_list:
        p = Process(
            target=get_assignee_information.get_info,
            args=(chunk, zips_dict, cities_dict, pat_assg_info, standard_names)
        )
        procs.append(p)
        p.start()
