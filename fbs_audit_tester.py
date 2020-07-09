"""Tester for the FBS_Audit tool"""
from fbs_audit import FbsAudit

# Get user input
dem = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\Terrain\ter'
db = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\FBS_Audit_Development.gdb'
outfolder = r'D:\Tools\FBS_Audit\Test_Data\FBS_Audit_Development\Output'

# Create an instance of the class and run it
print("Starting....\n")
fbs_audit = FbsAudit(dem, db, outfolder)

print("Creating file geodatabase")
# fbs_audit.create_file_geodatabase()
print("\t...done")

print("Checking spatial reference")
# fbs_audit.spatial_reference_check()
print("\t...done")

print("\nAll Done")
