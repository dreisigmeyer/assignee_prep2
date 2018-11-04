import sys
from python.launch import process_assignees

NUMBER_OF_PROCESSES = int(sys.argv[1])

process_assignees(NUMBER_OF_PROCESSES)
