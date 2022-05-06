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

log_obj.info(" --- populating for - UIC".format())
utility.populate_BO_UIC_score(config.UICs_copy, 'UIC_Score')

log_obj.info(" --- populating for - green streets".format())
utility.populate_BO_green_street_score(config.green_streets_copy, 'GS_Score')

#calc scores based on intersect alone
value = 3 # set by Heidi - 3 if overlap, 0 if not

utility.fillField_ifOverlap(config.block_objects_copy, config.critical_fac_copy, "critical_fac_Score", value)
utility.fillField_ifOverlap(config.block_objects_copy, config.schools_copy, "critical_fac_Score", value)

utility.fillField_ifOverlap(config.block_objects_copy, config.SRTS_copy, "SRTS_Score", value)

utility.fillField_ifOverlap(config.block_objects_copy, config.ped_districts, "ped_district_Score", value)

# convert all Nulls in Score fields to value of 0
log_obj.info(" - zero out Score fields (remove Nulls) - ".format())
utility.set_selected_field_Nulls_to_zero(config.block_objects_copy, 'Score')

log_obj.info(" - add and populate Category fields (score sums) - ".format())
utility.populate_category_fields(config.block_objects_copy, config.categories)

#log_obj.info(" - add and populate sum of Category values - ".format())
# didn't actually need this - keep for now
#utility.populate_category_sums(config.block_objects_copy, "category_sums", config.categories)

# bin upper, middle, lower 1/3 of values within each category and assign 3,2,1
for key in config.categories.keys():
    log_obj.info(" - add and populate binned value for - {}".format(key))
    utility.populate_binned_score(config.block_objects_copy, key)

log_obj.info(" - add and populate Binned_Sum - ".format())
utility.populate_bin_sums(config.block_objects_copy, 'Binned_Sum', 'binned')

log_obj.info(" - save block objects to disk - {}".format(config.output_gdb))
arcpy.CopyFeatures_management(config.block_objects_copy, os.path.join(config.output_gdb, "BO_TEST1"))
arcpy.CopyFeatures_management(config.UICs_copy, os.path.join(config.output_gdb, "UICs_TEST1"))

log_obj.info("PROCESS COMPLETE - Nuisance Flooding CoF - ".format())