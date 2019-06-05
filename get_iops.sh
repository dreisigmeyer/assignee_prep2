#!/bin/bash

# This collects together all of the needed information for 
# Individually Owned Patents

rm -f trash.csv
rm -f iops.csv

grep -h "INDIVIDUALLY OWNED PATENT" ./out_data/*.csv | awk -F'|' -v OFS='|' '{print $1,$5,$3,$6,$4,$10,$11}' | sort -t'|' -u >> trash.csv
awk -F'|' -v OFS='|' '{ if ($7 == "04" || $7 =="05") {print $1,$5,$3,$6,$4,$10,$11}}' ./out_data/*.csv | sort -t'|' -u >> trash.csv
sort -t'|' -u trash.csv > iops.csv

rm trash.csv