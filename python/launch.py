import csv
import glob
import json
import os
import random
from multiprocessing import Process
from python.get_assignee_information import get_info
from shared_python_code.process_text import clean_patnum
from shared_python_code.process_text import standardize_name
from shared_python_code.utility_functons import split_seq


def get_uspto_assignee_info(directory):
    '''Retrieves the assignee names on the USPTO DVD.

    directory -- directory where the DVD files are located.
    '''
    asg_names_file = glob.glob(directory + "ASG_NAMES_*.TXT")[0]
    pat_names_file = glob.glob(directory + "PN_ASG_*.TXT")[0]
    asg_names = {}
    pat_asg_info = {}
    with open(asg_names_file) as file:
        for line in file:
            asg_num = line[:7].strip()
            asg_name = line[8:].strip()
            asg_names[asg_num] = asg_name
    with open(pat_names_file) as file:
        for line in file:
            pat_num = line[:7]
            xml_pat_num, _ = clean_patnum(pat_num)
            asg_num_1 = line[8:15].strip()
            asg_num_2 = line[16:].strip()
            pat_asg_info[xml_pat_num] = [asg_names[asg_num_1], asg_names[asg_num_2]]
    return pat_asg_info


def get_standard_names(directory, pat_assg_info):
    '''Creates a xml_name to USPTO standardized name mapping by grant year.

    directory -- location of the prdn_metadata.csv file created by carra_prep.
    pat_assg_info -- output of get_uspto_assignee_info.
    '''
    standard_names_file = directory + "prdn_metadata.csv"
    standard_names = {}
    with open(standard_names_file, newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        for line in csv_reader:
            try:
                xml_pat_num, _ = clean_patnum(line[0])
                grant_yr = line[1]
                xml_name = standardize_name(line[-1])
                standardized_name = pat_assg_info[xml_pat_num][1]
                if xml_name not in standard_names:
                    standard_names[xml_name] = {}
                if grant_yr not in standard_names[xml_name]:
                    standard_names[xml_name][grant_yr] = []
                if standardized_name not in standard_names[xml_name][grant_yr]:
                    standard_names[xml_name][grant_yr].append(standardized_name)
            except Exception as e:
                pass
    return standard_names


# Start processing
def process_assignees(number_of_processes):
    '''Driver function that collects the XML data into CSV files.

    number_of_processes -- number of Python threads to use
    '''
    uspto_dir = 'uspto_data/'
    csv_dir = 'csv_data/'
    xml_data = 'xml_data/'
    path_to_JSON = 'json_data/'
    files = glob.glob(os.path.join(xml_data, "*.bz2"))
    random.shuffle(files)  # Newer years have more granted patents
    files_list = split_seq(files, number_of_processes)
    pat_assg_info = get_uspto_assignee_info(uspto_dir)
    standard_names = get_standard_names(csv_dir, pat_assg_info)
    with open(path_to_JSON + 'city_state_to_zip3.json') as json_data:
        zips_dict = json.load(json_data)
    with open(path_to_JSON + 'city_misspellings.json') as json_data:
        cities_dict = json.load(json_data)
    procs = []
    for chunk in files_list:
        p = Process(
            target=get_info,
            args=(chunk, zips_dict, cities_dict, pat_assg_info, standard_names)
        )
        procs.append(p)
        p.start()
