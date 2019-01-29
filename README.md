See also the README for **shared_python_code**.


## Getting the data
1.	If you don't have git-lfs you'll need to get the _ASG\_NAMES\_UPRD\_YY\_YY.TXT_ and _PN\_ASG\_UPRD\_YY\_YY.TXT_ files from the USPTO's patent data DVD.
	These files are placed in _usptoData/_.

2.	If you do have git-lfs and pulled this for the first time from this directory you'll need to 
    run  
    `bzip2 -dk uspto_data/ASG_NAMES_UPRD_69_15.TXT.bz2`  
    `bzip2 -dk uspto_data/PN_ASG_UPRD_69_15.TXT.bz2`  
	If the bzip files change you'll need to rerun this.


## Setting up the Python environment
The code was run with a standard Anaconda Python 3 environment (https://www.anaconda.com).


## Running the code
1.  From the **carra_prep2** repository:
	* _create\_GBD\_metadata_ is run to generate JSON files
	for attaching zip3s, correcting city-state information, etc.
	Copy the files in the **carra_prep2/outputs/json_output** directory
	_close\_city\_spellings.json_,
	_city\_state\_to\_zip3.json_ and
	_city\_mispellings.json_
	into **json_data**.
    * Copy the valid XML files from **carra_prep2/outputs/xml_output/xml_with_inventors** to **xml_data**.
2.  From this directory issue the command  
    `nohup ./run_it number_of_threads_to_use &`  
    This will create an _iops.csv_ file as well as one output file in **out_data** per USPTO weekly release.
    The output format for the files in **out_data** is  
    `xml_pat_num|uspto_pat_num|grant_yr|app_yr|co_name_google|assg_num|assg_type|city|st|country|co_raw_name_uspto|co_cleaned_name_uspto|zip3|new_state|inferred_cleaned_name_uspto`  
    _new\_state_ is if the raw state information from the GBD XML file is potentially incorrect.
    It is the actual state that corresponds to zip3.
    It may simply repeat the st entry.
    The city is the same.
    The zip3 information is inferred from the assignee City-State information.  
    _assg\_num_ is the position of the assignee in the XML file.  
    _co\_raw\_name\_uspto_ and _co\_cleaned\_name\_uspto_ are only present for _assg\_num_ = 1 prior to 2016.
    _inferred\_cleaned\_name\_uspto_ is present for all other assignees.  
    _assg\_type_ is one of the following:
    *   1    = unassigned
    *   2    = assigned to a U.S. non-government organization
    *   3    = assigned to a foreign non-government organization
    *   4    = assigned to a U.S. individual
    *   5    = assigned to a foreign individual
    *   6    = assigned to the U.S. (Federal) Government
    *   7    = assigned to a foreign government
    *   8,9  = assigned to a U.S. non-Federal Government agency
                  (8 and 9 may not appear)


## The individual pieces of the code
1.  The **python** module collects together the basic information about assignees.
The functions provided in **launch.py** are:
```
get_uspto_assignee_info(directory):
    Retrieves the assignee names on the USPTO DVD.

    directory -- directory where the DVD files are located.
```
```
get_standard_names(directory, pat_assg_info):
    Creates a xml_name to USPTO standardized name mapping by grant year.

    directory -- location of the prdn_metadata.csv file created by carra_prep.
    pat_assg_info -- output of get_uspto_assignee_info.
```
```
process_assignees(number_of_processes):
    Driver function that collects the XML data into CSV files.

    number_of_processes -- number of Python threads to use
```

The functions provided in **get_assignee_information.py** are:
```
get_info(files, zip3_json, cleaned_cities_json, pat_assg_info, standard_names):
    Collects all of the assignee information.

    files -- list of compressed XML files to process.
    zip3_json -- dictionary created from the carra prep city_state_to_zip3.json file.
    cleaned_cities_json -- dictionary created from the carra prep city_misspellings.json file.
    pat_assg_info -- basic information extracted from the USPTO DVD.
    standard_names -- standardized assignee names.
```