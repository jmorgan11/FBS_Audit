"""Tester for the FBS_Audit tool"""
from fbs_audit import FbsAudit

# Get user input
#-------------CLARK-----------------------------------------------------
dem = r'D:\Tools\FBS_Audit\Test_Data_2\DEM\clark_.tif'
db = r'D:\Tools\FBS_Audit\Test_Data_2\FBS_Audit_Test_2\Clark.gdb'
outfolder = r'D:\Tools\FBS_Audit\Test_Data_2\FBS_Audit_Test_2\Output'
wsel = r'D:\Tools\FBS_Audit\Test_Data_2\WSEL_Grid\WSE_01pct_SP.tif'

###-------------Klamath-----------------------------------------------------
##dem = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\Terrain\terrain.tif'
##db = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\FBS_Audit_Development.gdb'
##outfolder = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\Output'
##wsel = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\WSEL\WSE_01pct.tif'

# Create an instance of the class and run it
print("Starting....\n")
fbs_audit = FbsAudit(dem, wsel, db, outfolder)

print("Creating file geodatabase")
fbs_audit.create_file_geodatabase()

print("Checking spatial reference")
fbs_audit.spatial_reference_check()

print("Creating SFHA polyons")
fbs_audit.create_sfha_flood_polys()

print("Creating SFHA lines")
fbs_audit.create_sfha_flood_lines()

print("Creating Test Points")
fbs_audit.create_test_points()

print("Add Ground Elevations")
fbs_audit.add_ground_elevations_points()

print("Add WSEL Elevations")
fbs_audit.add_wsel_elevations_points()

print("Calculate differences")
fbs_audit.calc_difference()

print("Second Pass")
fbs_audit.check_failed_points()

print("Calculate Max/Min value")
fbs_audit.add_ground_elevations_area()

print("Adding Water Names to Test_Points")
fbs_audit.assign_water_names_near()

print("Cleanup")
fbs_audit.cleanup()

print("\nAll Done")
