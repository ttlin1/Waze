import arcpy
import math
import os
import pickle


def euclidean_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between two sets of coordinates"""
    return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))


def text_compare(string1, string2):
    """Cleans up and compares street names"""
    list1 = string1.upper().split(" ")
    list2 = string2.upper().split(" ")
    cleaned_list1 = [l for l in list1 if l not in ("HIGHWAY", "HWY", "ROAD", "RD", "STREET", "ST", "")]
    cleaned_list2 = [l for l in list2 if l not in ("HIGHWAY", "HWY", "ROAD", "RD", "STREET", "ST", "")]
    if len(cleaned_list1) > len(cleaned_list2):
        larger = cleaned_list1
        smaller = cleaned_list2
    else:
        larger = cleaned_list2
        smaller = cleaned_list1
    intersect = [l for l in larger if l in smaller]
    union = set(cleaned_list1 + cleaned_list2)
    return len(intersect) / float(len(union))


def calculate_nearest_segment_to_jam(gdb, jam_fc, muni_fc, road_fc, pickle_output):
    """Determines the nearest road segment to each point in the jam and saves the results in a dictionary"""
    projected_jam_fc = os.path.join(gdb, "projected")
    mass_state_plane = arcpy.SpatialReference('Projected Coordinate Systems/State Plane/NAD 1983 (2011) (Meters)/NAD 1983 (2011) StatePlane Massachusetts FIPS 2001 (Meters)')
    arcpy.Project_management(jam_fc, projected_jam_fc, mass_state_plane)

    jam_dictionary = {}
    for row in arcpy.da.SearchCursor(projected_jam_fc, ["uuid", "SHAPE@", "street", "city", "speed_mph", "length",
                                                        "delay", "level", "Jam_Reason"]):
        jam_dictionary[row[0]] = [row[1], row[2], row[3][:row[3].find(",")].upper(), row[4], row[5], row[6], row[7], row[8]]

    municipal_dict = {}
    for row in arcpy.da.SearchCursor(muni_fc, ["TOWN_ID", "TOWN"]):
        municipal_dict[row[1]] = row[0]

    road_dict = {}
    for row in arcpy.da.SearchCursor(road_fc, ["City", "RoadInventory_ID", "SHAPE@", "StreetName"]):
        if row[0] not in road_dict:
            road_dict[row[0]] = {}
        road_dict[row[0]][row[1]] = [row[2], row[3]]

    segment_data_dictionary = {}  # [[speed_mph1, length1, delay1, level1], [speed_mph2, length2, delay2, level2] ... ]
    for j in jam_dictionary:
        for pt in jam_dictionary[j][0]:
            current_distance = 0
            lowest_distance = 999999999
            closest_segment_id = -1
            for segment_id in road_dict[municipal_dict[jam_dictionary[j][2]]]:
                if text_compare(road_dict[municipal_dict[jam_dictionary[j][2]]][segment_id][1], jam_dictionary[j][1]) > 0:
                    for arr in road_dict[municipal_dict[jam_dictionary[j][2]]][segment_id][0]:
                        for seg_pt in arr:
                            current_distance = euclidean_distance(pt.X, pt.Y, seg_pt.X, seg_pt.Y)
                            if current_distance < 25:
                                if current_distance < lowest_distance:
                                    closest_segment_id = segment_id
                                    lowest_distance = current_distance
            if closest_segment_id not in segment_data_dictionary:
                segment_data_dictionary[closest_segment_id] = [j]
            if j not in segment_data_dictionary[closest_segment_id]:
                segment_data_dictionary[closest_segment_id].append(j)

    pickle.dump(segment_data_dictionary, open(pickle_output, "wb"))
    arcpy.Delete_management(projected_jam_fc)
    return segment_data_dictionary, jam_dictionary


def output_data(gdb, segment_data_dictionary, jam_dictionary, road_fc, output_fc):
    """Creates an output feature class with the jam data"""
    temp_fc = os.path.join(gdb, "temp")
    sql_expression = '"RoadInventory_ID" IN (' + ", ".join(str(i) for i in segment_data_dictionary) + ")"
    arcpy.MakeFeatureLayer_management(road_fc, temp_fc, sql_expression)
    if arcpy.Exists(output_fc):
        arcpy.Delete_management(output_fc)
    arcpy.CopyFeatures_management(temp_fc, output_fc)
    arcpy.AddField_management(output_fc, "Jams", "TEXT", 500)
    arcpy.AddField_management(output_fc, "Number_of_Jams", "LONG")
    arcpy.AddField_management(output_fc, "Avg_Jam_Speed", "DOUBLE")
    arcpy.AddField_management(output_fc, "Avg_Jam_Length", "DOUBLE")
    arcpy.AddField_management(output_fc, "Avg_Jam_Delay", "DOUBLE")

    with arcpy.da.UpdateCursor(output_fc, ["RoadInventory_ID", "Jams", "Number_of_Jams", "Avg_Jam_Speed",
                                           "Avg_Jam_Length", "Avg_Jam_Delay"]) as cursor:
        for row in cursor:
            if row[0] in segment_data_dictionary:
                # concatenated_jams = ", ".join(str(s) for s in segment_data_dict[row[0]])
                # row[1] = concatenated_jams
                number_jams = 0
                total_speed = 0
                total_length = 0
                total_delay = 0
                for jam in segment_data_dictionary[row[0]]:
                    if not jam_dictionary[jam][7]:
                        number_jams += 1
                        total_speed += jam_dictionary[jam][3]
                        total_length += jam_dictionary[jam][4]
                        total_delay += jam_dictionary[jam][5]
                row[2] = number_jams
                row[3] = total_speed / float(number_jams)
                row[4] = total_length / float(number_jams)
                row[5] = total_delay / float(number_jams)
                cursor.updateRow(row)
    del cursor
    return


jam_file = r"U:\Projects\Tasks_For_Bonnie\Jams_At_City_Level_082416\Swansea\data.gdb\JAMS"
road_file = r"U:\Projects\Base_Data\MassGIS\MassGIS.gdb\RoadInventory2014"
municipality_file = r"U:\Projects\Base_Data\MassGIS\MassGIS.gdb\Municipal_Boundary"
pickle_file = r"U:\Projects\Tasks_For_Bonnie\Jams_At_City_Level_082416\Swansea\segment_data_dict.p"
geodatabase = r"U:\Projects\Tasks_For_Bonnie\Jams_At_City_Level_082416\Swansea\data.gdb"
output_file = os.path.join(geodatabase, "Road_Segments_With_Jams")

segment_data_dict, jam_dict = calculate_nearest_segment_to_jam(geodatabase, jam_file, municipality_file, road_file, pickle_file)
output_data(geodatabase, segment_data_dict, jam_dict, road_file, output_file)
