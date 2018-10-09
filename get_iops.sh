#!/bin/bash

rm -f trash.csv
rm -f iops.csv

grep -h "INDIVIDUALLY OWNED PATENT" ./outData/*.csv | awk -F'|' -v OFS='|' '{print $1,$5,$3,$6,$4,$10,$11}' | sort -t'|' -u >> trash.csv
awk -F'|' -v OFS='|' '{ if ($6 == "04" || $6 =="05") {print $1,$5,$3,$6,$4,$10,$11}}' ./outData/*.csv | sort -t'|' -u >> trash.csv
sort -t'|' -u trash.csv > iops.csv

rm trash.csv