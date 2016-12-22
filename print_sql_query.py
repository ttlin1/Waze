import csv
import os


def print_query(csv_file_number):
    sql_query = "SELECT * FROM waze.t_jams WHERE waze.t_jams.uuid IN ('"
    base_dir = r"U:\Projects\Tasks_For_Bonnie\Waze_State_Signals_090716\sqloutput\jamuuid"
    csv_file = os.path.join(base_dir, str(csv_file_number) + ".csv")
    uuid = []
    with open(csv_file, "rb") as text_file:
        reader = csv.reader(text_file, delimiter="\t")
        for r in reader:
            uuid.append(r[0])
    del text_file
    sql_query += "', '".join(u for u in uuid)
    sql_query += "');"
    return sql_query

base_dir = r"\\mhd-fsp-bos-v01\urd$\lint\Desktop\temp"
for i in range(48, 76, 1):
    out_file = os.path.join(base_dir, str(i) + ".txt")
    with open(out_file, "wb") as text_file:
        writer = csv.writer(text_file, delimiter=",")
        row = [str(print_query(i)).replace('"', '')]
        writer.writerow(row)
    del text_file
