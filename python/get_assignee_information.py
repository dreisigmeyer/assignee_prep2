# -*- coding: utf-8 -*-

"""
The patent bulk download data (from Google or USPTO) should be cleaned with
the GBD_data_cleaner before being used here.  That removes HTML entities and
performs other cleaning on the XML files.

This outputs the assignee data from the Google Bulk Download and the USPTO
DVD.  The format is:
xml_pat_num|uspto_pat_num|grant_yr|app_yr|co_name_google|\
assg_num|assg_type|city|st|country|co_raw_name_uspto|co_cleaned_name_uspto|\
zip3|new_state|co_possible_name

new_state is if the raw state information from the GBD XML file is potentially
incorrect.  It is the actual state that corresponds to zip3. It may simply
repeat the st entry. The city is the same.  The zip3 information is inferred
from the assignee City-State information.

assg_num is the position of the assignee in the XML file.  co_raw_name_uspto
and co_cleaned_name_uspto are only present for assg_num = 1.

assg_type is one of the following:
     1    = unassigned
     2    = assigned to a U.S. non-government organization
     3    = assigned to a foreign non-government organization
     4    = assigned to a U.S. individual
     5    = assigned to a foreign individual
     6    = assigned to the U.S. (Federal) Government
     7    = assigned to a foreign government
     8,9  = assigned to a U.S. non-Federal Government agency
              (8 and 9 may not appear)

This requires Python 2.7. It was developed using Anaconda 2.30 (Python 2.7.10).
You should use Anaconda or be prepared to track down and install all of the
necessary Python packages.

To run this make this file executable and do:
    ./get_assignee_information.py num_of_processes
num_of_processes >=1 is the number of individual Python processes to run.

The XML paths are given below for the Google bulk download.  Make
sure they haven't changed if you have problems.

Make sure the USPTO file names haven't changed in below if you have troubles.

All of the date formats are expected to be %Y%m%d

Created by David W. Dreisigmeyer 5 Oct 15
"""

import codecs
import csv
import glob
import json
import os
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher as SeqMatcher

from lxml import etree

cw_dir = os.getcwd()
pat_num_re = re.compile(r'([A-Z]*)0*([0-9]+)')
dateFormat = '%Y%m%d'  # The dates are expected in %Y%m%d format
grant_year_re = re.compile('[a-z]{3,4}([0-9]{8})_wk[0-9]{2}')
xml_validator = etree.XMLParser(
    dtd_validation=False,
    resolve_entities=False,
    encoding='utf8')
path_to_JSON = 'python/json_data/'
LAST_USPTO_DVD_YEAR = 2015
with open(path_to_JSON + 'close_city_spellings.json') as json_data:
    CLOSE_CITY_SPELLINGS = json.load(json_data)


def clean_patnum(patnum):
    """
    Removes extraneous zero padding
    """
    pat_num = patnum.strip().upper()
    hold_pat_num = pat_num_re.match(pat_num).groups()
    pat_num_len = len(hold_pat_num[0] + hold_pat_num[1])
    zero_padding = '0' * (7 - pat_num_len)
    pat_num = hold_pat_num[0] + zero_padding + hold_pat_num[1]
    zero_padding = '0' * (8 - pat_num_len)
    xml_pat_num = hold_pat_num[0] + zero_padding + hold_pat_num[1]
    return xml_pat_num, pat_num


def clean_it(in_str):
    if isinstance(in_str, str):
        return in_str.decode('unicode_escape')
    else:
        return ''


def to_ascii(applicant_text):
    """
    Clean up the string
    """
    applicant_text = clean_it(applicant_text)
    # Replace utf-8 characters with their closest ascii
    applicant_text = unicodedata.normalize('NFKD', applicant_text)
    applicant_text = applicant_text.encode('ascii', 'ignore')
    applicant_text = applicant_text.replace('&', ' AND ')
    applicant_text = ' '.join(applicant_text.split())
    applicant_text = re.sub('[^a-zA-Z0-9 ]+', '', applicant_text).upper()
    return applicant_text.strip()


def get_assignee_info(assignee, xml_path):
    """
    """
    try:
        assignee_info = assignee.find(xml_path).text
        assignee_info = to_ascii(assignee_info)
    except Exception:  # may have assignee name from USPTO DVD
        assignee_info = ''
    return assignee_info


def get_zip3(assignee_state, assignee_city, zip3_json, cleaned_cities_json):
    """
    Attempts to find a zip3 from an assignee's city and state information.
    """
    possible_zip3s = dict()
    possible_cities = [assignee_city]
    cleaned_cities = cleaned_cities_json.get(assignee_state)
    if cleaned_cities:
        for hold_city, spellings in cleaned_cities.iteritems():
            if hold_city not in possible_cities:
                if assignee_city[:20] in spellings:
                    possible_cities.append(hold_city)
    city_names = zip3_json.get(assignee_state)
    close_city_names = CLOSE_CITY_SPELLINGS.get(assignee_state)
    if close_city_names:
        close_city_names_keys = close_city_names.keys()
    else:
        close_city_names_keys = []
    for alias in possible_cities:
        if alias in close_city_names_keys:  # is the name ok?
            for zip3 in close_city_names[alias]:
                possible_zip3s[zip3] = assignee_state
            continue
        # is this a real state?
        if assignee_state not in CLOSE_CITY_SPELLINGS.keys():
            continue
        CLOSE_CITY_SPELLINGS[assignee_state][alias] = set()  # this isn't there
        # this may be a new misspelling, which we're going to check for now
        if city_names:
            for city, zips in city_names.iteritems():
                str_match = SeqMatcher(None, alias, city)
                if str_match.ratio() >= 0.9:  # good enough match
                    CLOSE_CITY_SPELLINGS[assignee_state][alias].update(zips)
                    for zip3 in zips:
                        possible_zip3s[zip3] = assignee_state
    # Maybe the state is wrong so look for a matching city name
    if len(possible_zip3s) == 0:
        states = zip3_json.keys()
        for state in states:
            zips = zip3_json[state].get(assignee_city)
            if zips:
                for zip3 in zips:
                    possible_zip3s[zip3] = state
    if not possible_zip3s:  # in case wee didn't find a zip3
        possible_zip3s[''] = ''
    return possible_zip3s


def get_info(files, zip3_json, cleaned_cities_json, pat_assg_info, standard_names):
    for infile in files:
        folder_name = os.path.splitext(os.path.basename(infile))[0]
        # Get data in and ready
        folder_path = cw_dir + "/python/holdData/" + folder_name + "/"
        os.system("mkdir " + folder_path)
        os.system("unzip -qq -o " + infile + " -d " + folder_path)
        xml_split = glob.glob(folder_path + "/*.xml")
        out_file_name = os.path.splitext(os.path.basename(infile))[0]
        csv_file = codecs.open("outData/" + out_file_name + ".csv", 'w', 'ascii')
        csv_writer = csv.writer(csv_file, delimiter='|')
        grant_year_gbd = int(grant_year_re.match(folder_name).group(1)[:4])
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
            root = etree.parse(xmlDoc, xml_validator)

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
                        assignee_information.append(pat_assg_info[patent_number][0])
                    except Exception:
                        assignee_information.append('')
                    try:
                        assignee_information.append(pat_assg_info[patent_number][1])
                    except Exception:
                        assignee_information.append('')
                else:
                    assignee_information.append('')
                    assignee_information.append('')

                possible_zip3s = dict()
                possible_zip3s[''] = ''
                if a_state != '' and a_city != '':
                    try:
                        possible_zip3s = get_zip3(a_state, a_city, zip3_json, cleaned_cities_json)
                    except Exception:
                        pass

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
                print("WARNING: Didn't process every assignee on patent " + patent_number)
        # Clean things up
        csv_file.close()
        os.system("rm -rf " + folder_path)
