#!/usr/bin/env python3.6.3a
import UsrIntel.R1
from tabulate import tabulate
import pandas as pd
import argparse
import os

parser = argparse.ArgumentParser("add_column_to_csv", epilog="""for example:\n
                                 add_column_to_csv.py -dir=/nfs/site/disks/meirlevy_wa/python/ccf-lnl-a0-master-21ww33a-regression/verif/utdb/agents/ccf_flows_csv -column=21 -header=CleanEvict -value=X\n
                                 Or:\n 
                                 add_column_to_csv.py -file=/nfs/site/disks/meirlevy_wa/python/ccf-lnl-a0-master-21ww33a-regression/verif/utdb/agents/ccf_flows_csv/Victim.csv  -column=21 -header=CleanEvict -value=X""")
parser.add_argument("-dir", help="A String with the full path to the CSV file", type=str, default=None)
parser.add_argument("-file", help="A String with the full path to the CSV file", type=str, default=None)
parser.add_argument("-create_new_file", help="A String with the full path to the CSV file", type=bool, default=False)
parser.add_argument("-debug", help="Add debug prints", type=bool, default=False)
parser.add_argument("-column", help="An integer that will tell the script where to add the new column.", type=int)
parser.add_argument("-header", help="A String that will handle the title of the new column.", type=str)
parser.add_argument("-value", help="A String that will populate all the column rows", type=str)
args = parser.parse_args()

csv_dir = args.dir
file_path = args.file
add_column_index = args.column #21
new_column_name = args.header #21 "CleanEvict"
column_value = args.value #"X"
debug_mode = args.debug

def handle_unnamed_cells_in_row(row_l):
    counter = 0
    for index, column in enumerate(row_l):
        if "Unnamed" in column:
            row_l[index] = str(counter)
        if index == add_column_index:
            row_l.insert(add_column_index, str(counter))
        counter = counter + 1

def add_column_to_csv_file(file_path):
    csv_table = pd.read_csv(file_path, header=None)
    if debug_mode:
        debug_df = pd.read_csv(file_path)
        print("Original CSV Table:")
        print(tabulate(debug_df, headers='keys', tablefmt='psql'))
    header_list = list(csv_table.iloc[0])
    handle_unnamed_cells_in_row(header_list)

    secondary_header = list(csv_table.iloc[1])


    if any([True for header_cell in secondary_header if header_cell.lower().strip() == new_column_name.lower().strip()]):
        print("File: {} already has the new column: {}".format(file_path, new_column_name))
    else:
        csv_table = csv_table.drop([0]) #remove main header
        csv_table.columns = secondary_header
        csv_table.insert(add_column_index, column=new_column_name, value=column_value)
        #secondary_header = list(csv_table.columns)
        csv_table.iloc[0, add_column_index] = new_column_name
        csv_table.columns = header_list
        if debug_mode:
            print("Modified CSV Table:")
            print(tabulate(csv_table, headers='keys', tablefmt='psql'))
        csv_table.to_csv(file_path, index=False)


def get_all_csv_files(dir_path):
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.csv'):
                file_list.append(root+'/'+str(file))

    return file_list


def main():
    if csv_dir is not None:
        file_list = get_all_csv_files(csv_dir)
        for file_p in file_list:
            print("Working on file: {}".format(file_p))
            add_column_to_csv_file(file_p)

    elif file_path is not None:
        add_column_to_csv_file(file_path)
    else:
        print("User didn't gave file path or dir path. please check your command.")

if __name__ == "__main__":
    # execute only if run as a script
    main()