import csv
import arcpy
from datetime import datetime
from pytz import timezone


def join_jamspoints_to_jams(jam_text_file, jampoints_text_file, in_gdb):
    """
    Inputs: jams and jampoints as text files, geodatabase for output
    Joins the jampoints to the jams and outputs the result to a geodatabase
    """
    uuid = []
    jam_dict = {}
    jampoints_dict = {}
    wgs1984 = arcpy.SpatialReference(u'Geographic Coordinate Systems/World/WGS 1984')
    field_type_dict = {'runid': "LONG",
                       'pubmillis': "DOUBLE",
                       'location_x': "DOUBLE",
                       'location_y': "DOUBLE",
                       'uuid': "TEXT",
                       'magvar': "SHORT",
                       'type': "TEXT",
                       'subtype': "TEXT",
                       'reportdescription': "TEXT",
                       'street': "TEXT",
                       'city': "TEXT",
                       'country': "TEXT",
                       'roadtype': "SHORT",
                       'reportrating': "SHORT",
                       'jamuuid': "TEXT",
                       'reliability': "SHORT",
                       'imageurl': "TEXT",
                       'confidence': "SHORT",
                       'date': "DATE",
                       'speed': "DOUBLE",
                       'length': "LONG",
                       'delay': "LONG",
                       'startnode': "TEXT",
                       'endnode': "TEXT",
                       'level': "LONG",
                       'turntype': "TEXT",
                       'blockingalertuuid': "TEXT",
                       'type': "TEXT",
                       'jamuuid': "TEXT",
                       'location_x': "DOUBLE",
                       'location_y': "DOUBLE"}

    def convert_to_ordinal(milliseconds):
        eastern = timezone('US/Eastern')
        return datetime.fromtimestamp(milliseconds / 1000.0, eastern)

    with open(jam_text_file, "rb") as txt_file:
        reader = csv.reader(txt_file, delimiter=",")
        for r in reader:
            if r[0] == "uuid":
                jam_legend = r
            else:
                if r[0] not in uuid:
                    uuid.append(r[0])
                    jam_dict[r[0]] = r[1:]
    del txt_file

    with open(jampoints_text_file, "rb") as txt_file:
        reader = csv.reader(txt_file, delimiter=",")
        for r in reader:
            if r[0] != "runid":
                if r[1] not in jampoints_dict:
                    jampoints_dict[r[1]] = []
                jampoints_dict[r[1]].append((float(r[2]), float(r[3])))
    del txt_file

    output_fc = arcpy.CreateFeatureclass_management(in_gdb, "JAMS", "MULTIPOINT", "", "", "", wgs1984)
    for j in jam_legend:
        arcpy.AddField_management(output_fc, j, field_type_dict[j])
    arcpy.AddField_management(output_fc, "date", "DATE")
    arcpy.AddField_management(output_fc, "speed_mph", "DOUBLE")

    insert_fields = jam_legend + ["date", "speed_mph", "SHAPE@"]
    cursor = arcpy.da.InsertCursor(output_fc, insert_fields)
    for jam_id in jam_dict:
        if jam_id in jampoints_dict:
            row = [jam_id]
            for field in jam_legend:
                if field != "uuid":
                    row.append(jam_dict[jam_id][jam_legend.index(field) - 1])
            row.append(convert_to_ordinal(float(jam_dict[jam_id][jam_legend.index('pubmillis') - 1])))
            row.append((float(jam_dict[jam_id][jam_legend.index('speed') - 1]) * 0.000621371 * 60 * 60))
            row.append(arcpy.Multipoint(arcpy.Array([arcpy.Point(*coordinates) for coordinates in jampoints_dict[jam_id]])))
            cursor.insertRow(row)
    return

jam_text = r"U:\Projects\Tasks_For_Bonnie\Waze_Springfield_I_91_110416\sqloutput\T_JAMS.csv"
jampoints_text = r"U:\Projects\Tasks_For_Bonnie\Waze_Springfield_I_91_110416\sqloutput\T_JAMPOINTS.csv"
gdb = r"U:\Projects\Tasks_For_Bonnie\Waze_Springfield_I_91_110416\waze_springfield.gdb"

join_jamspoints_to_jams(jam_text, jampoints_text, gdb)
