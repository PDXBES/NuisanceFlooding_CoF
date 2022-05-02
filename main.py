import config
import utility
import arcpy
import os

arcpy.env.overwriteOutput = True

log_obj = utility.Logger(config.log_file)

log_obj.info("STARTING PROCESS - Nuisance Flooding CoF - ".format())

log_obj.info(" - add and populate Scores - ".format())

#calc scores based on fields with text strings
for key, value in config.source_field_score_text_dict.items():
    log_obj.info(" --- populating for - {}".format(value[0]))
    utility.populate_BO_MAX_score_for_text(key, value[0], value[1])

#calc scores based on fields with value ranges
log_obj.info(" --- populating for - CVI".format())
utility.populate_BO_MAX_score_for_CVI(config.CVI_dict)

log_obj.info(" --- populating for - frequent service".format())
utility.populate_BO_MAX_score_for_freq_svc(config.freq_svc_dict)

#calc scores based on intersect alone


# convert all Nulls in Score fields to value of 0
log_obj.info(" - zero out Score fields (remove Nulls) - ".format())
utility.set_selected_field_Nulls_to_zero(config.block_objects_copy, 'Score')

log_obj.info(" - save block objects to disk - {}".format(config.output_gdb))
arcpy.CopyFeatures_management(config.block_objects_copy, os.path.join(config.output_gdb, "BO_TEST1"))

log_obj.info("PROCESS COMPLETE - Nuisance Flooding CoF - ".format())