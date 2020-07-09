""" Performs an Flood Boundary Standard on FEMA Flood Polygons"""

# fbs_audit: Performs an Flood Boundary Standard on FEMA Flood Polygons
# author: Jesse Morgan
# contact: jesse.morgan@atkinsglobal.com
# date: 7/9/2020
# version: 1

import sys
import arcpy

class FbsAudit:
    """ Performs an Flood Boundary Standard on FEMA Flood Polygons"""

    def __init__(self, in_dem, in_workspace, outfolder):
        """Receives the DEM, flood lines, flood polygons, water lines and cross sections"""
        self.dem = in_dem # The terrain DEM
        self.workspace = in_workspace # Workspace of the data
        self.outfolder = outfolder # The output folder for the data
        self.fld_lines = ''
        self.fld_polys = ''
        self.cross_sections = ''
        self.profile_baselines = ''

        arcpy.env.workspace = self.workspace

        # Get the location of the needed feature classes
        if self.workspace[-4:] in ['.gdb', '.mdb']:
            self.database_table_check()
        else:
            self.shapefile_table_check()

    def create_file_geodatabase(self):
        """Create an empty File Geodatabase"""
        fbs_db = self.outfolder + '\\FBS_Audit.gdb'
        if arcpy.Exists(fbs_db):
            arcpy.Delete_management(fbs_db)

        arcpy.CreateFileGDB_management(self.outfolder, 'FBS_Audit.gdb')

    def database_table_check(self):
        """Check for required tables in a database to run an FBS Audit"""
        # Check for feature classes in the database
        if self.workspace[-4:] in ['.gdb', '.mdb']:

            feature_class_list = arcpy.ListFeatureClasses()

            for feature_class in feature_class_list:
                if str(feature_class) == 'S_Fld_Haz_Ln':
                    self.fld_lines = self.workspace + '\\S_Fld_Haz_Ln'
                elif str(feature_class) == 'S_Fld_Haz_Ar':
                    self.fld_polys = self.workspace + '\\S_Fld_Haz_Ar'
                elif str(feature_class) == 'S_Profil_Basln':
                    self.profile_baselines = self.workspace + '\\S_Profil_Basln'
                elif str(feature_class) == 'S_XS':
                    self.cross_sections = self.workspace + '\\S_XS'

            # Check in any datasets
            datasets = arcpy.ListDatasets()
            for dataset in datasets:
                feature_class_list = arcpy.ListFeatureClasses("*", "All", dataset)

                for feature_class in feature_class_list:
                    if str(feature_class) == 'S_Fld_Haz_Ln':
                        self.fld_lines = self.workspace + '\\' + dataset + '\\S_Fld_Haz_Ln'
                    elif str(feature_class) == 'S_Fld_Haz_Ar':
                        self.fld_polys = self.workspace + '\\' + dataset + '\\S_Fld_Haz_Ar'
                    elif str(feature_class) == 'S_Profil_Basln':
                        self.profile_baselines = self.workspace + '\\' + dataset + \
                                                 '\\S_Profil_Basln'
                    elif str(feature_class) == 'S_XS':
                        self.cross_sections = self.workspace + '\\' + dataset + '\\S_XS'

    def shapefile_table_check(self):
        """Check for required tables in a folder to run an FBS Audit"""
        # Check for feature classes in the folder (eg shapefiles)
        feature_class_list = arcpy.ListFeatureClasses()

        for feature_class in feature_class_list:
            if str(feature_class) == 'S_Fld_Haz_Ln.shp':
                self.fld_lines = self.workspace + '\\S_Fld_Haz_Ln.shp'
            elif str(feature_class) == 'S_Fld_Haz_Ar.shp':
                self.fld_polys = self.workspace + '\\S_Fld_Haz_Ar.shp'
            elif str(feature_class) == 'S_Profil_Basln.shp':
                self.profile_baselines = self.workspace + '\\S_Profil_Basln.shp'
            elif str(feature_class) == 'S_XS.shp':
                self.cross_sections = self.workspace + '\\S_XS.shp'

    def spatial_reference_check(self):
        """Check the spatial reference system used"""

        if arcpy.Describe(self.dem).spatialReference.factoryCode != \
           arcpy.Describe(self.fld_lines).spatialReference.factoryCode != \
           arcpy.Describe(self.fld_polys).spatialReference.factoryCode != \
           arcpy.Describe(self.profile_baselines).spatialReference.factoryCode != \
           arcpy.Describe(self.cross_sections).spatialReference.factoryCode:

            print("The spatial reference does not match between the feature classes" + \
                  "and the DEM.  Exiting...")

            sys.exit(1)

        # TODO: Get the unit of measurement vertically and horizontally

        # TODO: Load all applicable digital data into the GIS Project.
        #   - S_FLD_HAZ_LN
        #       - Check that LN_TYP is attributed
        #       - Check for multipart features
        #       - Run repair geometry
        #   - S_FLD_HAZ_AR
        #       - Check FLD_ZONE is attributed
        #       - Check ZONE_SUBTY is attributed
        #       - Check for multipart features
        #       - Run repair geometry
        #   - S_Profil_Basln (needed for mileage)
        #       - Check for Unique Names
        #       - Check STUDY_TYP is attributed
        #       - Check WTR_NM is attributed
        #       - Check for multipart features
        #       - Run repair geometry
        #   - S_XS
        #       - WTR_NM is attributed
        #       - WSEL_REG is attrubted
        #       - Check for multipart features
        #       - Run repair geometry
        #   - Terrain Data (WSEL / TIN)

        # TODO: Verify everything is in the same projection (reproject or fail)

        #                            Zone A RUN
        # --------------------------------------------------------------------------------
        # TODO: Create the APPROX_FLD_HAZ_LN_STUDY feature class
        #   - Select all Zone A polygons
        #   - Select all flood lines that share a boundary with selected polygons
        #   - Remove all selected flood lines that share a boundary with Zone AE polygons
        #   - Copy the remaing lines to the new feature class

        # TODO: Create the APPROX_FLD_HAZ_PLY_STUDY feature class
        #   - Select all the Zone A polygons
        #   - Copy them to the new feature class

        # TODO: Create the APPROX_PROFIL_BASLN
        #   - Select all Profile Baselines with an Approximate Study Type
        #   - Copy them to the new feature class

        # TODO: Create the A_XS_STUDY feature class
        #   - Select all the cross sections that intersect the APPROX_PROFIL_BASLN and have
        #     the same WTR_NM
        #   - Copy them to the new feature class

        # TODO: Create the APPROX_TEST_PTS_STUDY feature class
        #   - Create points every 100 ft along the APPROX_FLD_LN_STUDY feature class

        # TODO: Add the following fields to the APPROX_TEST_PTS_STUDY attribute table.
        #     a. WTR_NM_1   - String, length = 100
        #     b. WTR_NM_2   - String, length = 100
        #     c. FldELEV    - Numeric, 6, 2
        #     d. MinElev    - Numeric, 6, 2
        #     e. MaxElev    - Numeric, 6, 2
        #     f. GrELEV     - Numeric, 6, 2
        #     g. ElevDIFF   - Numeric, 6, 2
        #     h. RiskClass  - String, length = 2
        #     i. Tolerance  - Numeric, 6, 2
        #     j. Status     - String, length = 2
        #     k. Validation - String, length = 20
        #     l. Comment    - String, length = 100

        # TODO: Calculate the RiskClass to A for everything

        # TODO: Calculate the Tolerance

        # TODO: Add ground elevation values to APPROX_TEST_PTS_STUDY from the DEM
        #   - Use Add Surface Information
        #   - Values stored in GrdELEV field

        # TODO: Add WSEL elevation values to APPROX_TEST_PTS_STUDY from the WSEL Grid
        #   - Use Add Surface Information
        #   - Values stored in FldELEV field

        # TODO: Check if ABS(FldELEV - GrELEV) <= 1.0
        #   - If so, mark status as 'Pass'
        #   - else, mark status as 'Fail'

        # TODO: For each point that Fails, recheck with 38 foot horizontal tolerance
        #   - Create a buffer for the point at 38 feet
        #   - Get the max and min values from DEM within the buffer
        #       - Populate the MinElev
        #       - Populate the MaxElev
        #   - Check if the Fld_Elev is within the MinElev and MaxElev values,
        #     set to 'Pass'

        # TODO: Attribute the WTR_NM_1 field in APPROX_TEST_PTS_STUDY
        #   - Create a bounding box for each stream
        #   - Select all points that fall into each box
        #   - Update the WTR_NM_1 field with the box's WTR_NM field
        #       - If WTR_NM_1 is populated, put the value in WTR_NM2

        # TODO: Output Report


if __name__ == "__main__":
    # Check for spatial analyst license
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        print("Spatial Analyst license is required for this tool.")
        print("Unable to check out extension.  Exiting")
        sys.exit(1)

    # Get user input
    dem = sys.argv[1]
    workspace = sys.argv[2]
    out = sys.argv[3]

    # Create an instance of the class and run it
    fbs_audit = FbsAudit(dem, workspace, out)
