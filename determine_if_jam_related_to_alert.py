import arcpy
import math


def euclidean_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between two sets of coordinates"""
    return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))


def find_alerts_related_to_jams(jam_feature_class, alert_feature_class, time_delta, search_distance):
    """Finds alerts that are within the search distance and within the time delta from a jam.  Adds the alert type and
    subtype to the jams in the field 'Jam_Reason'.  """
    jam_dict = {}
    for row in arcpy.da.SearchCursor(jam_feature_class, ["uuid", "date", "SHAPE@"]):
        jam_dict[row[0]] = [row[1], row[2]]

    alert_dict = {}
    for row in arcpy.da.SearchCursor(alert_feature_class, ["uuid", "date", "location_x", "location_y", "type", "subtype"]):
        alert_dict[row[0]] = [row[1], (row[2], row[3]), row[4], row[5]]

    jam_to_alert = {}
    for j in jam_dict:
        for a in alert_dict:
            if abs((jam_dict[j][0] - alert_dict[a][0]).total_seconds() / 60) <= time_delta:  # minutes
                jam_to_alert[j] = []
                for pt in jam_dict[j][1]:
                    if euclidean_distance(pt.X, pt.Y, alert_dict[a][1][0], alert_dict[a][1][1]) <= search_distance:
                        jam_to_alert[j].append(a)

    arcpy.AddField_management(jam_feature_class, "Jam_Reason", "TEXT", 255)
    with arcpy.da.UpdateCursor(jam_feature_class, ["uuid", "Jam_Reason"]) as cursor:
        for row in cursor:
            if row[0] in jam_to_alert:
                if len(jam_to_alert[row[0]]) > 0:
                    subtype_list = []
                    for a in jam_to_alert[row[0]]:
                        subtype_list.append(alert_dict[a][2] + " - " + alert_dict[a][3])
                    row[1] = ", ".join(s for s in subtype_list)
                    cursor.updateRow(row)
    del cursor
    return

jam_fc = r"U:\Projects\Tasks_For_Bonnie\Jams_At_City_Level_082416\Swansea\data.gdb\JAMS"
alert_fc = r"U:\Projects\Tasks_For_Bonnie\Jams_At_City_Level_082416\Swansea\data.gdb\ALERTS"
find_alerts_related_to_jams(jam_fc, alert_fc, 15, 0.0005)
