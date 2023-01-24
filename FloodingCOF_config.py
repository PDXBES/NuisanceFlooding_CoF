import os
import arcpy
import FloodingCOF_utility
from datetime import datetime


print("Nuisance Flooding CoF - Starting Config: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

output_gdb = r"\\besfile1\ccsp\Mapping\Gdb\Stormwater_NuisanceFlooding_CoF_dev.gdb"

log_file = r"\\besfile1\ccsp\Mapping\dev\log\NF_CoF_log"

connections = r"\\besfile1\grp117\DAshney\Scripts\connections"

EGH_PUBLIC = os.path.join(connections, "egh_public on gisdb1.rose.portland.local.sde")
ASSETS_PDOT = os.path.join(connections, "AssetsPDOT on GISDB1.sde")

print(" - Formatting inputs: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

tsp_classes = EGH_PUBLIC + r"\EGH_PUBLIC.ARCMAP_ADMIN.tsp_classifications_pdx"

#Foot
ped_districts = EGH_PUBLIC + r"\EGH_PUBLIC.ARCMAP_ADMIN.pedestrian_districts_pdx"
ped_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\ped_class", "Pedestrian in ('CCTP', 'CW', 'PD', 'LS', 'NW')")
peak_arrivals = ASSETS_PDOT + r"\ASSETS_PDOT.ARCMAP_ADMIN.transit_peak_arrival_pbot_pdx"
service_buffer = ASSETS_PDOT + r"\ASSETS_PDOT.ARCMAP_ADMIN.transit_service_buffer_pbot_pdx"

#Vehicle
transit_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\transit_class", "Transit not in ( 'N/A' , 'IPR' , 'UNK' )")
traffic_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\traffic_class", "Traffic <> 'RT'")
freight_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\freight_class", "Freight not in ( 'LS' , 'N/A' , 'RBL' , 'RML' , 'UNK', 'FD' )")
emergency_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\emergency_class")
bike_class = arcpy.MakeFeatureLayer_management(tsp_classes, r"in_memory\bike_class")
SRTS = "https://services.arcgis.com/quVN97tn06YNGj9s/arcgis/rest/services/SRTSinvestmentroutes_public/FeatureServer/0"

#Facility
zoning = r"\\besfile1\StormWaterProgram\Data\RAFT\RAWQ\landuse_for_wq2.tif" #fragile
zoning_vector = arcpy.RasterToPolygon_conversion(zoning, r"in_memory\zoning_vector", "NO_SIMPLIFY", "Category", "MULTIPLE_OUTER_PART")
critical_fac = EGH_PUBLIC + r"\EGH_PUBLIC.ARCMAP_ADMIN.critical_facilities_pbem_pdx"
schools = EGH_PUBLIC + r"\EGH_PUBLIC.ARCMAP_ADMIN.schools_metro"

#CVI
CVI = EGH_PUBLIC + r"\EGH_Public.ARCMAP_ADMIN.CVI_BES_pdx"

#for LoF
UICs = EGH_PUBLIC + r"\EGH_Public.ARCMAP_ADMIN.UIC_BES_PDX"
active_UICs = arcpy.MakeFeatureLayer_management(UICs, r"in_memory\active_UICs", "opsStatus NOT IN( 'NB' , 'PA' )")
green_streets = EGH_PUBLIC + r"\EGH_Public.ARCMAP_ADMIN.GRST_INSP_BES_PDX"

# if these are important they should really live somewhere else
#block_objects = r"\\besfile1\ASM_AssetMgmt\Projects\Interagency Risk Grid\BlockEval\Data\Arc\GDB\block_working.gdb\block_diss3" # first version
#block_objects = r"\\besfile1\ASM_AssetMgmt\Projects\Interagency Risk Grid\BlockEval\Data\Arc\GDB\block_working_v2.gdb\block_objects" # second version
block_objects = r"\\besfile1\ASM_AssetMgmt\Projects\Interagency Risk Grid\BlockEval\Data\Arc\GDB\block_automation.gdb\block_objects"

print(" - Reading inputs into memory: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
ped_districts_copy = arcpy.CopyFeatures_management(ped_districts, r"in_memory\ped_districts_copy")
ped_class_copy = arcpy.CopyFeatures_management(ped_class, r"in_memory\ped_class_copy")
peak_arrivals_copy = arcpy.CopyFeatures_management(peak_arrivals, r"in_memory\peak_arrivals_copy")
service_buffer_copy = arcpy.CopyFeatures_management(service_buffer, r"in_memory\service_buffer_copy") # don't think this is needed
transit_class_copy = arcpy.CopyFeatures_management(transit_class, r"in_memory\transit_class_copy")
traffic_class_copy = arcpy.CopyFeatures_management(traffic_class, r"in_memory\traffic_class_copy")
freight_class_copy = arcpy.CopyFeatures_management(freight_class, r"in_memory\freight_class_copy")
emergency_class_copy = arcpy.CopyFeatures_management(emergency_class, r"in_memory\emergency_class_copy")
bike_class_copy = arcpy.CopyFeatures_management(bike_class, r"in_memory\bike_class_copy")
SRTS_copy = arcpy.CopyFeatures_management(SRTS, r"in_memory\SRTS_copy")
zoning_copy = arcpy.CopyFeatures_management(zoning_vector, r"in_memory\zoning_copy")
critical_fac_copy = arcpy.CopyFeatures_management(critical_fac, r"in_memory\critical_fac_copy")
schools_copy = arcpy.CopyFeatures_management(schools, r"in_memory\schools_copy")
CVI_copy = arcpy.CopyFeatures_management(CVI, r"in_memory\CVI_copy")
UICs_copy = arcpy.CopyFeatures_management(active_UICs, r"in_memory\UICs_copy")
green_streets_copy = arcpy.CopyFeatures_management(green_streets, r"in_memory\green_streets")
block_objects_copy = arcpy.CopyFeatures_management(block_objects, r"in_memory\block_objects_copy")

FloodingCOF_utility.populate_UIC_Age(UICs_copy, 'installDate', 'Age_Days')

#take of max of AM / PM arrivals - creates 'arrivals_all' field
FloodingCOF_utility.calc_max_arrivals(peak_arrivals_copy)

ped_route_dict = {'MCW':3, 'CW':2, 'NW':1, 'PD':1, 'LS':1}
transit_route_dict = {'RT':3, 'RTMTP':3, 'MTP':2, 'TA':2, 'LS':1}
traffic_route_dict = {'RTMCT':3, 'MCT':3, 'NC':2, 'DC':2, 'CS':1, 'TA':1}
freight_route_dict = {'RT':3, 'PT':2, 'MT':2, 'TA':1}
emergency_route_dict = {'MAJ':3, 'SEC':2, 'MIN':1}
bike_route_dict = {'MCB':3, 'CB':2, 'LS':1}
zoning_dict = {'COM':3, 'HeavyIND':2, 'LightIND':2, 'MFR':1, 'SFR':1}
#values for CVI and frequent service (peak arrivals) are coded in utility.calc_CVI_scores and utility.calc_freq_svc_scores because they use ranges

source_field_score_text_dict = {
                     ped_class_copy: ['Pedestrian', ped_route_dict],
                     transit_class_copy: ['Transit', transit_route_dict],
                     traffic_class_copy: ['Traffic', traffic_route_dict],
                     freight_class_copy: ['Freight', freight_route_dict],
                     emergency_class_copy: ['Emergency', emergency_route_dict],
                     bike_class_copy: ['Bicycle', bike_route_dict],
                     zoning_copy: ['Category', zoning_dict]
                     }

CVI_dict = {CVI_copy: 'OVERALL_RANK'}
freq_svc_dict = {peak_arrivals_copy: 'arrivals_all'}

categories = {
            'Foot_Sum': ['MAX_Pedestrian_Score', 'MAX_arrivals_all_Score', 'SRTS_Score', 'ped_district_Score'],
            'Vehicle_Sum': ['MAX_Transit_Score', 'MAX_Traffic_Score', 'MAX_Freight_Score', 'MAX_Emergency_Score', 'MAX_Bicycle_Score'],
            'Facility_Sum': ['MAX_Category_Score', 'critical_fac_Score'],
            'CVI_Sum': ['MAX_OVERALL_RANK_Score']
            }

# wish there was a better way, these are set manually to split CoF into 5 bins
# if the values/ range in CoF change then this list needs to change as well
CoF_bin_breaks = [4, 6, 8, 10]

print("Nuisance Flooding CoF - Config Complete: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))