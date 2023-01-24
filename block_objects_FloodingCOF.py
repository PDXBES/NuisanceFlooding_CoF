import FloodingCOF_config
import FloodingCOF_utility
import arcpy
import os

arcpy.env.overwriteOutput = True

log_obj = FloodingCOF_utility.Logger(FloodingCOF_config.log_file)

log_obj.info("STARTING PROCESS - Nuisance Flooding CoF - ".format())

log_obj.info(" - add and populate Scores - ".format())

#calc scores based on fields with text strings
for key, value in FloodingCOF_config.source_field_score_text_dict.items():
    log_obj.info(" --- populating for - {}".format(value[0]))
    FloodingCOF_utility.populate_BO_MAX_score_for_text(key, value[0], value[1])

#calc scores based on fields with value ranges
log_obj.info(" --- populating for - CVI".format())
FloodingCOF_utility.populate_BO_MAX_score_for_CVI(FloodingCOF_config.CVI_dict)

log_obj.info(" --- populating for - frequent service".format())
FloodingCOF_utility.populate_BO_MAX_score_for_freq_svc(FloodingCOF_config.freq_svc_dict)

log_obj.info(" --- populating for - UIC".format())
FloodingCOF_utility.populate_BO_UIC_score(FloodingCOF_config.UICs_copy, 'UIC_Score')

log_obj.info(" --- populating for - green streets".format())
FloodingCOF_utility.populate_BO_green_street_score(FloodingCOF_config.green_streets_copy, 'GS_Score')

#calc scores based on intersect alone
value = 3 # set by Heidi - 3 if overlap, 0 if not

FloodingCOF_utility.fillField_ifOverlap(FloodingCOF_config.block_objects_copy, FloodingCOF_config.critical_fac_copy, "critical_fac_Score", value)
FloodingCOF_utility.fillField_ifOverlap(FloodingCOF_config.block_objects_copy, FloodingCOF_config.schools_copy, "critical_fac_Score", value)

FloodingCOF_utility.fillField_ifOverlap(FloodingCOF_config.block_objects_copy, FloodingCOF_config.SRTS_copy, "SRTS_Score", value)

FloodingCOF_utility.fillField_ifOverlap(FloodingCOF_config.block_objects_copy, FloodingCOF_config.ped_districts, "ped_district_Score", value)

log_obj.info(" - populate Connection Status - ".format())
FloodingCOF_utility.populate_surface_connection(FloodingCOF_config.UICs_copy, 'comment_', 'No_Connection')

# convert all Nulls in Score fields to value of 0
log_obj.info(" - zero out Score fields (remove Nulls) - ".format())
FloodingCOF_utility.set_selected_field_Nulls_to_zero(FloodingCOF_config.block_objects_copy, 'Score')
FloodingCOF_utility.set_selected_field_Nulls_to_zero(FloodingCOF_config.block_objects_copy, 'No_Connection')

log_obj.info(" - add and populate Category fields (score sums) - ".format())
FloodingCOF_utility.populate_category_fields(FloodingCOF_config.block_objects_copy, FloodingCOF_config.categories)

# bin upper, middle, lower 1/3 of values within each category and assign 3,2,1
for key in FloodingCOF_config.categories.keys():
    log_obj.info(" - add and populate binned value for - {}".format(key))
    FloodingCOF_utility.populate_binned_score_3rds(FloodingCOF_config.block_objects_copy, key)

log_obj.info(" - add and populate Binned_Sum (CoF) - ".format()) # this is the "CoF score"
FloodingCOF_utility.populate_bin_sums(FloodingCOF_config.block_objects_copy, 'CoF', 'binned')

log_obj.info(" - add and populate binned CoF - ".format())
FloodingCOF_utility.populate_binned_score_5ths(FloodingCOF_config.block_objects_copy, 'CoF')

log_obj.info(" - find the max/ mean between GS/ UIC scores - ".format())
GS_UIC_fields = ['MAX_UIC_Score', 'MAX_GS_Score']
FloodingCOF_utility.calc_max_of_two_fields(FloodingCOF_config.block_objects_copy, GS_UIC_fields, 'LoF_max')
FloodingCOF_utility.calc_mean_of_two_fields(FloodingCOF_config.block_objects_copy, GS_UIC_fields, 'LoF_mean')

log_obj.info(" - combine CoF/ LoF scores (multiply them) - ".format())
CoF_LoF_max_fields = ['LoF_max', 'CoF_binned']
FloodingCOF_utility.calc_multiple_of_two_fields(FloodingCOF_config.block_objects_copy, CoF_LoF_max_fields, 'Risk_max')
CoLoF_mean_fields = ['LoF_mean', 'CoF_binned']
FloodingCOF_utility.calc_multiple_of_two_fields(FloodingCOF_config.block_objects_copy, CoLoF_mean_fields, 'Risk_mean')

log_obj.info(" - save block objects to disk - {}".format(FloodingCOF_config.output_gdb))
arcpy.CopyFeatures_management(FloodingCOF_config.block_objects_copy, os.path.join(FloodingCOF_config.output_gdb, "Nuisance_Flooding_BOs"))

log_obj.info("PROCESS COMPLETE - Nuisance Flooding CoF - ".format())