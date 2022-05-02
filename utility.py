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
    #print(value_dict)
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

def get_field_names(input_fc):
    field_names = []
    fields = arcpy.ListFields(input_fc)
    for field in fields:
        field_names.append(field.name)
    return field_names

def selected_field_names(input_fc, text_string_to_find):
    selected_names = []
    for name in get_field_names(input_fc):
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


