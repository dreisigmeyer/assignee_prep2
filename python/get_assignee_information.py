import codecs
import csv
import glob
# import json
import os
import re
from datetime import datetime
# from difflib import SequenceMatcher as SeqMatcher
from shared_python_code.process_text import clean_patnum
from shared_python_code.process_text import dateFormat
from shared_python_code.process_text import get_assignee_info
from shared_python_code.process_text import grant_year_re
from shared_python_code.xml_paths import magic_validator
from shared_python_code.utility_functons import initialize_close_city_spelling
from lxml import etree

THIS_DIR = os.path.dirname(__file__)
path_to_JSON = 'python/json_data/'
LAST_USPTO_DVD_YEAR = 2015


def get_info(files, zip3_json, cleaned_cities_json, pat_assg_info, standard_names):
    get_zip3 = initialize_close_city_spelling(path_to_JSON)
    for infile in files:
        folder_name = os.path.splitext(os.path.basename(infile))[0]
        # Get data in and ready
        folder_path = THIS_DIR + "/python/holdData/" + folder_name + "/"
        os.system("mkdir " + folder_path)
        os.system("unzip -qq -o " + infile + " -d " + folder_path)
        xml_split = glob.glob(folder_path + "/*.xml")
        out_file_name = os.path.splitext(os.path.basename(infile))[0]
        csv_file = codecs.open("outData/" + out_file_name + ".csv", 'w', 'ascii')
        csv_writer = csv.writer(csv_file, delimiter='|')
        grant_year_gbd = int(grant_year_re.match(folder_name).group(1))
        """
        These are the XML paths we use to extract the data.
        Note: if the path is rel_path_something_XXX then this is a path that is
        relative to the path given by path_something
        """
        if grant_year_gbd > 2004:
            # Theses paths are for 2005 - present
            path_patent_number = "us-bibliographic-data-grant/publication-reference/document-id/doc-number"
            path_grant_date = "us-bibliographic-data-grant/publication-reference/document-id/date"
            path_app_date = "us-bibliographic-data-grant/application-reference/document-id/date"
            path_assignees = "us-bibliographic-data-grant/assignees/"
            rel_path_assignees_orgname = "addressbook/orgname"
            rel_path_assignees_city = "addressbook/address/city"
            rel_path_assignees_state = "addressbook/address/state"
            rel_path_assignees_country = "addressbook/address/country"
            rel_path_assignees_type = "addressbook/role"
        elif 2001 < grant_year_gbd < 2005:
            # Theses paths are for 2002 - 2004
            path_patent_number = "SDOBI/B100/B110/DNUM/PDAT"
            path_grant_date = "SDOBI/B100/B140/DATE/PDAT"
            path_app_date = "SDOBI/B200/B220/DATE/PDAT"
            path_assignees = "SDOBI/B700/B730"
            rel_path_assignees_orgname = "./B731/PARTY-US/NAM/ONM/STEXT/PDAT"
            rel_path_assignees_city = "./B731/PARTY-US/ADR/CITY/PDAT"
            rel_path_assignees_state = "./B731/PARTY-US/ADR/STATE/PDAT"
            rel_path_assignees_country = "./B731/PARTY-US/ADR/CTRY/PDAT"
            rel_path_assignees_type = "./B732US/PDAT"
        elif grant_year_gbd < 2002:
            # Theses paths are for pre-2002
            path_patent_number = "WKU"
            path_grant_date = ""  # just use grant_year_GBD
            path_app_date = "APD"
            path_assignees = "ASSGS/"
            rel_path_assignees_orgname = "NAM"
            rel_path_assignees_city = "CTY"
            rel_path_assignees_state = "STA"
            rel_path_assignees_country = "CNT"
            rel_path_assignees_type = "COD"
        else:
            raise UserWarning("Incorrect grant year: " + str(grant_year_gbd))

        # Run the queries
        for xmlDoc in xml_split:
            root = etree.parse(xmlDoc, magic_validator)

            try:  # to get patent number
                xml_patent_number = root.find(path_patent_number).text
                xml_patent_number, patent_number = clean_patnum(xml_patent_number)
            except Exception:  # no point in going on
                continue

            # I hand fixed some files and want the grant year from the XML
            # for these, otherwise take the grant year from the folder name
            grant_year = grant_year_gbd
            hand_fixed = re.match(r'fix', folder_name)
            if hand_fixed and hand_fixed.group(0) == 'fix':
                try:  # to get the application date
                    grant_date = root.find(path_grant_date).text.upper()
                    grant_year = str(datetime.strptime(grant_date, dateFormat).year)
                except Exception:
                    grant_year = grant_year_gbd
                    pass

            try:  # to get the application date
                app_date = root.find(path_app_date).text
                app_year = str(datetime.strptime(app_date, dateFormat).year)
            except Exception:
                app_year = ''
                pass

            assignees = root.findall(path_assignees)
            if not assignees:  # Self-assigned
                continue

            number_assignees_to_process = len(assignees)
            assignees_counter = 0
            for assignee in assignees:
                assignees_counter += 1
                assignee_information = [
                    xml_patent_number,
                    patent_number,
                    grant_year,
                    app_year]
                a_orgname = ''
                try:
                    a_orgname = get_assignee_info(assignee, rel_path_assignees_orgname)
                    assignee_information.append(a_orgname)
                except Exception:
                    assignee_information.append('')
                assignee_information.append(assignees_counter)
                try:
                    a_type = get_assignee_info(assignee, rel_path_assignees_type)
                    assignee_information.append(a_type)
                except Exception:
                    assignee_information.append('')
                try:
                    a_city = get_assignee_info(assignee, rel_path_assignees_city)
                    assignee_information.append(a_city)
                except Exception:
                    a_city = ''
                    assignee_information.append('')
                try:
                    a_state = get_assignee_info(assignee, rel_path_assignees_state)
                    assignee_information.append(a_state)
                except Exception:
                    a_state = ''
                    assignee_information.append('')
                try:
                    a_country = get_assignee_info(assignee, rel_path_assignees_country)
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
                if a_state != '' and a_city != '':
                    try:
                        possible_zip3s = get_zip3(a_state, a_city, zip3_json, cleaned_cities_json)
                    except Exception:
                        pass
                if not possible_zip3s:
                    possible_zip3s[''] = ''

                for zip3, state in possible_zip3s.iteritems():
                    hold_csv_line = list(assignee_information)
                    hold_csv_line.extend([zip3, state])
                    if grant_year_gbd > LAST_USPTO_DVD_YEAR and a_orgname:
                        try:
                            hold_names = standard_names[a_orgname][LAST_USPTO_DVD_YEAR]
                            for name in hold_names:
                                csv_writer.writerow(hold_csv_line + [name])
                        except Exception:
                            csv_writer.writerow(hold_csv_line + [''])
                    elif assignees_counter != 1 and a_orgname:
                        try:
                            hold_names = standard_names[a_orgname][grant_year_gbd]
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
        csv_file.close()
        os.system("rm -rf " + folder_path)
