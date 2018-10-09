## Getting the data
1.	If you don't have git-lfs you'll need to get the _ASG\_NAMES\_UPRD\_YY\_YY.TXT_ and _PN\_ASG\_UPRD\_YY\_YY.TXT_ files from the USPTO's patent data DVD.
	These files are placed in _usptoData/_.

2.	If you do have git-lfs and pulled this for the first time from this directory you'll need to 
    run  
    `bzip2 -d uspto_data/ASG_NAMES_UPRD_69_15.TXT.bz2`  
    `bzip2 -d uspto_data/PN_ASG_UPRD_69_15.TXT.bz2`  
	If the bzip files change you'll need to rerun this.

## Setting up the Python environment
Included is an _environment.yml_ file that you can use with Anaconda to set up a Python virtual 
environment using  
`conda env create -f environment.yml`  
More information is available at https://conda.io/docs/user-guide/tasks/manage-environments.html.
The environment is the same as for **carra_prep** so you don't need to do this step if you've set up that environment.

## Running the code
1.  From the **carra_prep** repository:
	* _create\_GBD\_metadata_ is run to generate JSON files
	for attaching zip3s, correcting city-state information, etc.
	Copy the files (in the **carra_prep** top directory)
	_close\_city\_spellings.json_,
	_zip3\_cities.json_ and
	_cityMispellings.json_
	into _python/json\_data_.
    * _python\_validation_ creates valid XML documents from the original XML files (2002-present).
    Copy the files from _python\_validation/outData/_ to _inData/_.
2.  From this directory issue the command  
    `nohup ./runit &`  
    This will create an _iops.csv_ file as well as one output file in _outData/_ per USPTO weekly release.
    The output format is  
    `xml_pat_num|uspto_pat_num|grant_yr|app_yr|co_name_google|assg_num|assg_type|city|st|country|co_raw_name_uspto|co_cleaned_name_uspto|zip3|new_state`  
    _new\_state_ is if the raw state information from the GBD XML file is potentially incorrect.
    It is the actual state that corresponds to zip3.
    It may simply repeat the st entry.
    The city is the same.
    The zip3 information is inferred from the assignee City-State information.  
    _assg\_num_ is the position of the assignee in the XML file.  
    _co\_raw\_name\_uspto_ and _co\_cleaned\_name\_uspto_ are only present for _assg\_num_ = 1.  
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
