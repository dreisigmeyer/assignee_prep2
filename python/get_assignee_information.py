import codecs
import csv
import glob
import os
import tarfile
from datetime import datetime
from shared_python_code.process_text import clean_patnum
from shared_python_code.process_text import dateFormat
from shared_python_code.process_text import get_assignee_info
from shared_python_code.process_text import grant_year_re
from shared_python_code.xml_paths import assg_xml_paths
from shared_python_code.xml_paths import magic_validator
from shared_python_code.utility_functons import initialize_close_city_spelling
from lxml import etree

THIS_DIR = os.path.dirname(__file__)
hold_folder_path = THIS_DIR + '/hold_data/'
close_city_spellings = 'json_data/close_city_spellings.json'
LAST_USPTO_DVD_YEAR = 2015


def get_info(files, zip3_json, cleaned_cities_json, pat_assg_info, standard_names):
    '''Collects all of the assignee information.

    files -- list of compressed XML files to process.
    zip3_json -- dictionary created from the carra prep city_state_to_zip3.json file.
    cleaned_cities_json -- dictionary created from the carra prep city_misspellings.json file.
    pat_assg_info -- basic information extracted from the USPTO DVD.
    standard_names -- standardized assignee names.
    '''
    get_zip3 = initialize_close_city_spelling(close_city_spellings)
    for in_file in files:
        folder_name = os.path.splitext(os.path.basename(in_file))[0] + "/"
        # Get data in and ready
        folder_path = hold_folder_path + folder_name
        with tarfile.open(name=in_file, mode='r:bz2') as tar_file:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar_file, path=folder_path)
            out_file_name = os.path.basename(in_file)
            out_file_name = out_file_name.rsplit('.')[0]
            xml_split = glob.glob(folder_path + out_file_name + "/*.xml")
            out_csv_file = "out_data/" + out_file_name + ".csv"
            csv_file = codecs.open(out_csv_file, 'w')
            csv_writer = csv.writer(csv_file, delimiter='|')
            grant_year_gbd = int(grant_year_re.match(folder_name).group(1))
            xml_paths = assg_xml_paths(grant_year_gbd)
            path_prdn = xml_paths[0]
            path_app_date = xml_paths[2]
            path_assgs = xml_paths[3]
            assg_orgname, assg_type = xml_paths[4], xml_paths[8]
            assg_city, assg_state, assg_country = xml_paths[5], xml_paths[6], xml_paths[7]
            # Run the queries
            for xmlDoc in xml_split:
                root = etree.parse(xmlDoc, magic_validator)
                try:  # to get patent number
                    xml_patent_number = root.find(path_prdn).text
                    xml_patent_number, patent_number = clean_patnum(xml_patent_number)
                except Exception:  # no point in going on
                    continue
                try:  # to get the application date
                    app_date = root.find(path_app_date).text
                    app_year = str(datetime.strptime(app_date, dateFormat).year)
                except Exception:
                    app_year = ''
                    pass
                assignees = root.findall(path_assgs)
                if not assignees:  # Self-assigned
                    continue
                number_assignees_to_process = len(assignees)
                assignees_counter = 0
                for assignee in assignees:
                    assignees_counter += 1
                    assignee_information = [xml_patent_number, patent_number, grant_year_gbd, app_year]
                    try:
                        a_orgname = get_assignee_info(assignee, assg_orgname)
                        assignee_information.append(a_orgname)
                    except Exception:
                        a_orgname = ''
                        assignee_information.append(a_orgname)
                    assignee_information.append(assignees_counter)
                    try:
                        a_type = get_assignee_info(assignee, assg_type)
                        assignee_information.append(a_type)
                    except Exception:
                        assignee_information.append('')
                    try:
                        a_city = get_assignee_info(assignee, assg_city)
                        assignee_information.append(a_city)
                    except Exception:
                        a_city = ''
                        assignee_information.append('')
                    try:
                        a_state = get_assignee_info(assignee, assg_state)
                        assignee_information.append(a_state)
                    except Exception:
                        a_state = ''
                        assignee_information.append('')
                    try:
                        a_country = get_assignee_info(assignee, assg_country)
                        assignee_information.append(a_country)
                    except Exception:
                        assignee_information.append('')
                    if assignees_counter == 1 and grant_year_gbd <= LAST_USPTO_DVD_YEAR:
                        try:
                            assignee_information.append(pat_assg_info[xml_patent_number][0])
                        except Exception:
                            assignee_information.append('')
                        try:
                            assignee_information.append(pat_assg_info[xml_patent_number][1])
                        except Exception:
                            assignee_information.append('')
                    else:
                        assignee_information.append('')
                        assignee_information.append('')
                    possible_zip3s = {}
                    possible_zip3s[''] = ''
                    if a_state and a_city:
                        try:
                            possible_zip3s = get_zip3(a_state, a_city, zip3_json, cleaned_cities_json)
                        except Exception:
                            pass
                    for zip3, state in possible_zip3s.items():
                        hold_csv_line = list(assignee_information)
                        hold_csv_line.extend([zip3, state])
                        if grant_year_gbd > LAST_USPTO_DVD_YEAR and a_orgname:
                            try:
                                grant_year = str(LAST_USPTO_DVD_YEAR)
                                hold_names = standard_names[a_orgname][grant_year]
                                for name in hold_names:
                                    csv_writer.writerow(hold_csv_line + [name])
                            except Exception:
                                csv_writer.writerow(hold_csv_line + [''])
                        elif assignees_counter != 1 and a_orgname:
                            try:
                                grant_year = str(grant_year_gbd)
                                hold_names = standard_names[a_orgname][grant_year]
                                for name in hold_names:
                                    csv_writer.writerow(hold_csv_line + [name])
                            except Exception:
                                csv_writer.writerow(hold_csv_line + [''])
                        else:
                            csv_writer.writerow(hold_csv_line + [''])
                # make sure we at least tried to get every applicant
                if number_assignees_to_process != assignees_counter:
                    print("WARNING: Didn't process every assignee on patent " + xml_patent_number)
        # Clean things up
        os.system("rm -rf " + folder_path)
