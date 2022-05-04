import logging
import logging.config
import sys
import arcpy
import config


# https://stackoverflow.com/questions/6386698/how-to-write-to-a-file-using-the-logging-python-module
def Logger(file_name):
    formatter = logging.Formatter(fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                                  datefmt='%Y/%m/%d %H:%M:%S')  # %I:%M:%S %p AM|PM format
    logging.basicConfig(filename='%s.log' % (file_name),
                        format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S', filemode='a', level=logging.INFO)
    log_obj = logging.getLogger()
    log_obj.setLevel(logging.DEBUG)
    # log_obj = logging.getLogger().addHandler(logging.StreamHandler())

    # console printer
    screen_handler = logging.StreamHandler(stream=sys.stdout)  # stream=sys.stdout is similar to normal print
    screen_handler.setFormatter(formatter)
    logging.getLogger().addHandler(screen_handler)

    log_obj.info("Starting log session..")
    return log_obj

def get_field_value_as_dict(input, key_field, value_field):
    value_dict = {}
    with arcpy.da.SearchCursor(input, (key_field, value_field)) as cursor:
        for row in cursor:
            value_dict[row[0]] = row[1]
    return value_dict

def assign_field_value_from_dict(input_dict, target, target_key_field, target_field):
    with arcpy.da.UpdateCursor(target, (target_key_field, target_field)) as cursor:
        for row in cursor:
            for key, value in input_dict.items():
                if row[0] == key:
                    row[1] = value
            cursor.updateRow(row)

def get_and_assign_field_value(source, source_key_field, source_field, target, target_key_field, target_field):
    value_dict = get_field_value_as_dict(source, source_key_field, source_field)
    assign_field_value_from_dict(value_dict, target, target_key_field, target_field)

def list_field_names(input_fc):
    field_names = []
    fields = arcpy.ListFields(input_fc)
    for field in fields:
        field_names.append(field.name)
    return field_names

def add_field_if_needed(input_fc, field_to_add, field_type, scale = None, length = None):
    field_names = list_field_names(input_fc)
    if field_to_add not in field_names:
        arcpy.AddField_management(input_fc, field_to_add, field_type, scale, length)

def calc_scores_from_text(source_fc, source_field, target_field, score_dict):
    with arcpy.da.UpdateCursor(source_fc, [source_field, target_field]) as cursor:
        for row in cursor:
            for key, value in score_dict.items():
                if key == row[0]:
                    row[1] = value
            cursor.updateRow(row)

# could not quickly come up with a way to do this using the dict method
def calc_CVI_scores(source_fc, source_field, target_field):
    with arcpy.da.UpdateCursor(source_fc, [source_field, target_field]) as cursor:
        for row in cursor:
            if row[0] <= 160:
                row[1] = 1
            elif row[0] > 160 and row[0] <= 320:
                row[1] = 2
            elif row[0] > 320:
                row[1] = 3
            else:
                pass
            cursor.updateRow(row)

# could not quickly come up with a way to do this using the dict method
def calc_freq_svc_scores(source_fc, source_field, target_field):
    with arcpy.da.UpdateCursor(source_fc, [source_field, target_field]) as cursor:
        for row in cursor:
            if row[0] <= 10:
                row[1] = 1
            elif row[0] > 10 and row[0] <= 15:
                row[1] = 2
            elif row[0] > 15:
                row[1] = 3
            else:
                pass
            cursor.updateRow(row)

def populate_BO_MAX_score_for_text(input_fc, source_field, score_dict):
    score_field = source_field + "_Score"
    add_field_if_needed(input_fc, score_field, "SHORT")
    calc_scores_from_text(input_fc, source_field, score_field, score_dict)
    sect = arcpy.analysis.PairwiseIntersect([input_fc, config.block_objects_copy], r"in_memory\{}".format(source_field), "ALL", "#", "INPUT")
    max_stat = arcpy.analysis.Statistics(sect, r"in_memory\max_stat", [[score_field, 'MAX']], 'All_ID')
    arcpy.JoinField_management(config.block_objects_copy, 'All_ID', max_stat, 'All_ID', ["MAX_" + score_field])
    arcpy.Delete_management(sect)
    arcpy.Delete_management(max_stat)

def populate_BO_MAX_score_for_CVI(CVI_dict):
    for key, value in CVI_dict.items():
        score_field = value + "_Score"
        add_field_if_needed(key, score_field, "SHORT")
        calc_CVI_scores(key, value, score_field)
        sect = arcpy.analysis.PairwiseIntersect([key, config.block_objects_copy], r"in_memory\{}".format(value), "ALL", "#", "INPUT")
        max_stat = arcpy.analysis.Statistics(sect, r"in_memory\max_stat", [[score_field, 'MAX']], 'All_ID')
        arcpy.JoinField_management(config.block_objects_copy, 'All_ID', max_stat, 'All_ID', ["MAX_" + score_field])
        arcpy.Delete_management(sect)
        arcpy.Delete_management(max_stat)

def populate_BO_MAX_score_for_freq_svc(freq_service_dict):
    for key, value in freq_service_dict.items():
        score_field = value + "_Score"
        add_field_if_needed(key, score_field, "SHORT")
        calc_freq_svc_scores(key, value, score_field)
        sect = arcpy.analysis.PairwiseIntersect([key, config.block_objects_copy], r"in_memory\{}".format(value), "ALL", "#", "INPUT")
        max_stat = arcpy.analysis.Statistics(sect, r"in_memory\max_stat", [[score_field, 'MAX']], 'All_ID')
        arcpy.JoinField_management(config.block_objects_copy, 'All_ID', max_stat, 'All_ID', ["MAX_" + score_field])
        arcpy.Delete_management(sect)
        arcpy.Delete_management(max_stat)

def calc_max_arrivals(input_fc):
    new_field = 'arrivals_all'
    add_field_if_needed(input_fc, new_field, 'SHORT')
    with arcpy.da.UpdateCursor(input_fc, ['AMPeakArrivals', 'PMPeakArrivals', new_field]) as cursor:
        for row in cursor:
            if row[0] is None or row[1] is None:
                row[2] = 0
            else:
                if row[0] > row[1]:
                    row[2] = row[0]
                elif row[1] > row[0]:
                    row[2] = row[1]
                elif row[0] == row[1]:
                    row[2] = row[0]
                else:
                    pass
            cursor.updateRow(row)

def selected_field_names(input_fc, text_string_to_find):
    selected_names = []
    for name in list_field_names(input_fc):
        if text_string_to_find in name:
            selected_names.append(name)
    return selected_names

#set all Nulls found in the specified fields to 0
def set_selected_field_Nulls_to_zero(input_fc, text_string_to_find):
    selected_names_list = selected_field_names(input_fc, text_string_to_find)
    with arcpy.da.UpdateCursor(input_fc, selected_names_list) as cursor:
        for row in cursor:
            count = 0
            while count < len(selected_names_list):
                if row[count] is None:
                    row[count] = 0
                count = count + 1
            cursor.updateRow(row)

def fillField_ifOverlap(input, overlapFC, target_field, value):
    #input_layer = "input_layer"

    add_field_if_needed(input, target_field, "SHORT")

    #arcpy.MakeFeatureLayer_management(input, input_layer)
    selection = arcpy.SelectLayerByLocation_management(input, "INTERSECT", overlapFC)
    arcpy.CalculateField_management(selection, target_field, value)

def add_category_fields(input_fc, category_dict):
    for key in category_dict.keys():
        add_field_if_needed(input_fc, key, "SHORT")

def get_field_list_from_category_dict(key, value):
    field_list = []
    field_list.append(key)
    for item in value:
        field_list.append(item)
    return field_list

def get_keys_list_from_category_dict(category_dict):
    keys = []
    for key in category_dict.keys():
        keys.append(key)
    return keys

def populate_category_fields(input_fc, category_dict):
    add_category_fields(input_fc, category_dict)
    for key, value in category_dict.items():
        field_list = get_field_list_from_category_dict(key, value)
        with arcpy.da.UpdateCursor(input_fc, field_list) as cursor:
            for row in cursor:
                row[0] = sum(row[1:])
                cursor.updateRow(row)

def populate_new_field_with_sum_of_others(input_fc, new_field_name, binned_fields):
    add_field_if_needed(input_fc, new_field_name, 'SHORT')
    fields = [new_field_name]
    for field in binned_fields:
        fields.append(field)
    with arcpy.da.UpdateCursor(input_fc, fields) as cursor:
        for row in cursor:
            row[0] = sum(row[1:])
            cursor.updateRow(row)

def populate_category_sums(input_fc, new_field_name, category_dict):
    keys_list = get_keys_list_from_category_dict(category_dict)
    populate_new_field_with_sum_of_others(input_fc, new_field_name, keys_list)

def get_field_value_set(input_fc, field):
    value_list = []
    with arcpy.da.SearchCursor(input_fc, [field]) as cursor:
        for row in cursor:
            value_list.append(row[0])
    value_set = set(value_list)
    return value_set

def get_break_value_list(value_set):
    break_list = []
    break_1 = int(((len(value_set)+1)/3)) # find int length of distinct value list + 1 (bc 0 is a value), divide into 3rds
    break_list.append(break_1)
    break_list.append(break_1*2)
    return break_list

def populate_binned_score(input_fc, field):
    value_set = get_field_value_set(input_fc, field)
    break_value_list = get_break_value_list(value_set)
    bin_field = field + "_binned"
    add_field_if_needed(input_fc, bin_field, "SHORT")
    with arcpy.da.UpdateCursor(input_fc, [field, bin_field]) as cursor:
        for row in cursor:
            if row[0] <= break_value_list[0]:
                row[1] = 1
            elif row[0] > break_value_list[0] and row[0] <= break_value_list[1]:
                row[1] = 2
            elif row[0] > break_value_list[1]:
                row[1] = 3
            cursor.updateRow(row)

def populate_bin_sums(input_fc, new_field_name, text_string_to_find):
    binned_fields = selected_field_names(input_fc, text_string_to_find)
    populate_new_field_with_sum_of_others(input_fc, new_field_name, binned_fields)














