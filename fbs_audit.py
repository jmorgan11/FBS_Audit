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

    def __init__(self, in_dem, in_wsel, in_workspace, outfolder):
        """Receives the DEM, flood lines, flood polygons, water lines and cross sections"""
        self.dem = in_dem # The terrain DEM
        self.wsel = in_wsel # The WSEL Grid
        self.workspace = in_workspace # Workspace of the data
        self.outfolder = outfolder # The output folder for the data
        self.fld_lines = '' # Flood lines
        self.fld_polys = '' # Flood polygons
        self.cross_sections = '' # Cross sections
        self.profile_baselines = '' # Profile Baselines

        # Set the Workspace
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
        """Set required tables in a database to run an FBS Audit"""
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
        """Set required tables in a folder to run an FBS Audit"""
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

    def create_sfha_flood_polys(self):
        """Creates the sfha flood polygons"""

        # Select all the Zone AE polygons
        if arcpy.Exists("ae_zone_polys"):
            arcpy.Delete_management("ae_zone_polys")
        zone_delim = arcpy.AddFieldDelimiters(self.fld_polys, 'FLD_ZONE')
        ae_zone_polys = arcpy.MakeFeatureLayer_management(
            self.fld_polys, "ae_zone_polys", zone_delim + " = 'AE'")

        # Remove existing flood polygon feature class in the output database
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\SFHA_Areas'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\SFHA_Areas')

        # Dissolve them to merge the floodways into the AE zones
        arcpy.Dissolve_management(ae_zone_polys, self.outfolder + '\\FBS_Audit.gdb\\SFHA_Areas',
                                  "FLD_ZONE", multi_part='SINGLE_PART')

        # Select all the Zone A polygons
        if arcpy.Exists("a_zone_polys"):
            arcpy.Delete_management("a_zone_polys")
        zone_delim = arcpy.AddFieldDelimiters(self.fld_polys, 'FLD_ZONE')
        a_zone_polys = arcpy.MakeFeatureLayer_management(
            self.fld_polys, "a_zone_polys", zone_delim + " = 'A'")

        # Append these to to SFHA_Area polygons
        arcpy.Append_management(a_zone_polys, self.outfolder + '\\FBS_Audit.gdb\\SFHA_Areas',
                                "NO_TEST")

        # Reset self.fld_polys path
        self.fld_polys = self.outfolder + '\\FBS_Audit.gdb\\SFHA_Areas'

    def create_sfha_flood_lines(self):
        """Creates the sfha flood lines"""
        # Make a feature layer of the flood lines of the SFHA boundaries
        if arcpy.Exists("fld_line_lyr"):
            arcpy.Delete_management("fld_line_lyr")
        ln_typ_delim = arcpy.AddFieldDelimiters(self.fld_lines, 'LN_TYP')
        fld_line_lyr = arcpy.MakeFeatureLayer_management(
            self.fld_lines, "fld_line_lyr",
            ln_typ_delim + " IN ('2034', 'SFHA / Flood Zone Boundary')")

        # Delete any existing flood lines
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines')

        # Copy them to the File Geodatabase
        arcpy.CopyFeatures_management(fld_line_lyr,
                                      self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines')

        # Reset self.flood_lines to point to the new flood lines
        self.fld_lines = self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines'

        # Make a new feature layer to SFHA_lines
        if arcpy.Exists('shfa_lines'):
            arcpy.Delete_management('sfha_lines')
        sfha_lines = arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines', 'sfha_lines')

        # Remove the floodlines not associated with the polygons
        if arcpy.Exists("zone_polys"):
            arcpy.Delete_management("zone_polys")
        zone_polys = arcpy.MakeFeatureLayer_management(self.fld_polys, "zone_polys")
        arcpy.SelectLayerByLocation_management(sfha_lines, "SHARE_A_LINE_SEGMENT_WITH", zone_polys,
                                               invert_spatial_relationship='INVERT')
        arcpy.DeleteFeatures_management(sfha_lines)

        # Select all the Zone A polygons
        if arcpy.Exists("a_zone_polys"):
            arcpy.Delete_management("a_zone_polys")
        zone_delim = arcpy.AddFieldDelimiters(self.fld_polys, 'FLD_ZONE')
        a_zone_polys = arcpy.MakeFeatureLayer_management(
            self.fld_polys, "a_zone_polys", zone_delim + " = 'A'")

        # Select all the Zone AE polygons
        if arcpy.Exists("ae_zone_polys"):
            arcpy.Delete_management("ae_zone_polys")
        zone_delim = arcpy.AddFieldDelimiters(self.fld_polys, 'FLD_ZONE')
        ae_zone_polys = arcpy.MakeFeatureLayer_management(
            self.fld_polys, "ae_zone_polys", zone_delim + " = 'AE'")

        # Select from self.flood_lines all lines that share a boundary with the Zone AE polygons
        ae_lines = arcpy.SelectLayerByLocation_management(
            sfha_lines, "SHARE_A_LINE_SEGMENT_WITH", ae_zone_polys)

        # From the selected flood lines, select lines that share a boundary with the Zone A polygons
        common_lines = arcpy.SelectLayerByLocation_management(
            ae_lines, "SHARE_A_LINE_SEGMENT_WITH", a_zone_polys, selection_type='SUBSET_SELECTION')
        arcpy.DeleteFeatures_management(common_lines)

    def create_test_points(self):
        """Create the Test_Points feature class"""

        test_points = self.outfolder + '\\FBS_Audit.gdb\\Test_Points'

        # Create points every 100 ft along the Flood Lines
        if arcpy.Exists(test_points):
            arcpy.Delete_management(test_points)
        arcpy.GeneratePointsAlongLines_management(self.fld_lines, test_points,
                                                  "DISTANCE", Distance='100 feet')

        # Create a feature layer
        if arcpy.Exists("test_points_lyr"):
            arcpy.Delete_management("test_points_lyr")
        test_points_lyr = arcpy.MakeFeatureLayer_management(test_points, "test_points_lyr")

        # Add the needed fields to Test_Points
        arcpy.AddField_management(test_points_lyr, "WTR_NM_1", "TEXT", field_length=100)
        arcpy.AddField_management(test_points_lyr, "WTR_NM_2", "TEXT", field_length=100)
        arcpy.AddField_management(test_points_lyr, "FldELEV", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "MinElev", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "MaxElev", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "GrELEV", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "ElevDIFF", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "RiskClass", "TEXT", field_length=2)
        arcpy.AddField_management(test_points_lyr, "Tolerance", "FLOAT",
                                  field_precision=6, field_scale=2)
        arcpy.AddField_management(test_points_lyr, "Status", "TEXT", field_length=2)
        arcpy.AddField_management(test_points_lyr, "Validation", "TEXT", field_length=20)
        arcpy.AddField_management(test_points_lyr, "Comment", "TEXT", field_length=100)

        # Calculate the RiskClass to A for everything
        arcpy.CalculateField_management(test_points_lyr, "RiskClass", "\"A\"", "PYTHON_9.3")

        # Calculate the Tolerance
        arcpy.CalculateField_management(test_points_lyr, "Tolerance", "0.5", "PYTHON_9.3")

        # Drop unneeded fields
        field_drop_list = ['ORIG_FID', 'DFIRM_ID', 'VERSION_ID', 'FLD_LN_ID', 'LN_TYP',
                           'SOURCE_CIT', 'SHAPE_Length']

        field_list = arcpy.ListFields(self.outfolder + '\\FBS_Audit.gdb\\Test_Points')
        for field in field_list:
            if field.name in field_drop_list:
                arcpy.management.DeleteField(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                             field.name)

    def add_ground_elevations_points(self):
        """Add ground elevation values from the DEM to Test_Points feature class"""
        # Add Surface Information
        arcpy.ddd.AddSurfaceInformation(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        self.dem, 'Z', 'BILINEAR')

        # Values stored in GrdELEV field
        arcpy.management.CalculateField(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'GrELEV', '!Z!', 'PYTHON')

        # Calculate all the NULL GrdElev values to -9999
        if arcpy.Exists("point_lyr"):
            arcpy.Delete_management("point_lyr")
        arcpy.MakeFeatureLayer_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                          "point_lyr", "GrELEV IS NULL")
        arcpy.management.CalculateField('point_lyr', 'GrELEV', '-9999', 'PYTHON')

        # Drop the Z field
        arcpy.management.DeleteField(self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'Z')

    def add_ground_elevations_area(self):
        """Add ground elevation values from the DEM to Buffers feature class"""

        # Check to see if any buffers exists, if not return
        if not arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Buffers'):
            return
        
        # Add Surface Information
        arcpy.AddSurfaceInformation_3d(self.outfolder + '\\FBS_Audit.gdb\\Buffers',
                                       self.dem, "Z_MIN;Z_MAX", "BILINEAR", "", "1", "0",
                                       "NO_FILTER")

        # Values stored in MinElev field
        arcpy.management.CalculateField(self.outfolder + '\\FBS_Audit.gdb\\Buffers',
                                        'MinElev', '!Z_MIN!', 'PYTHON')

        # Values stored in MaxElev field
        arcpy.management.CalculateField(self.outfolder + '\\FBS_Audit.gdb\\Buffers',
                                        'MaxElev', '!Z_MAX!', 'PYTHON')        

    def add_wsel_elevations_points(self):
        """Add WSEL elevation values to Test_Points feature class"""
        # Add Surface Information
        arcpy.ddd.AddSurfaceInformation(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        self.wsel, 'Z', 'BILINEAR')

        # Values stored in FldELEV field
        arcpy.management.CalculateField(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'FldELEV', '!Z!', 'PYTHON')

        # Calculate all the NULL FldELEV values to -9999
        if arcpy.Exists("point_lyr"):
            arcpy.Delete_management("point_lyr")
        arcpy.MakeFeatureLayer_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                          "point_lyr", "FldELEV IS NULL")
        arcpy.management.CalculateField('point_lyr', 'FldELEV', '-9999', 'PYTHON')

        # Drop the Z field
        arcpy.management.DeleteField(self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'Z')             

    def calc_difference(self):
        """Calculates the absolute difference of the Flood Elevation and Ground Elevation values"""
        # Make an update cursor and iterate through each row
        with arcpy.da.UpdateCursor(
                self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                ['FldELEV', 'GrELEV', 'ElevDIFF', 'Tolerance', 'Status']) as cursor:

            for row in cursor:
                fld_elev = row[0]
                gr_elev = row[1]
                tolerance = row[3]

                # If FldElev != -9999 and GrElev == -9999: FAIL
                if fld_elev != -9999 and gr_elev == -9999:
                    row[2] = -9999
                    row[4] = "F"

                # If FldElev == -9999 and GrElev != -9999: FAIL
                elif fld_elev == -9999 and gr_elev != -9999:
                    row[2] = -9999
                    row[4] = "U"

                # If FldElev == -9999 and GrElev == -9999: N/A
                elif fld_elev == -9999 and gr_elev == -9999:
                    row[2] = 0
                    row[4] = "U"

                # If ABS(FldELEV - GrELEV) > Tolerance: PASS
                elif abs(fld_elev - gr_elev) <= tolerance:
                    row[2] = abs(fld_elev - gr_elev)
                    row[4] = 'P'

                # Else: FAIL
                else:
                    row[2] = abs(fld_elev - gr_elev)
                    row[4] = "F"

                # Update the row
                cursor.updateRow(row)

    def check_failed_points(self):
        """For each point that Fails, recheck with 38 foot horizontal tolerance"""
        # Select all the points that fail
        if arcpy.Exists("point_lyr"):
            arcpy.Delete_management("point_lyr")
        point_lyr = arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
            "point_lyr", "Status = 'F'")

        # Check if any 'F' points exists, if not return
        result = arcpy.GetCount_management(point_lyr)
        if int(result[0]) == 0:
            return
            
        # Create a buffer for the point at 38 feet
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Buffers'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Buffers')
        arcpy.Buffer_analysis(
            point_lyr, self.outfolder + '\\FBS_Audit.gdb\\Buffers',
            "19 Feet", dissolve_option="NONE", method="GEODESIC")

        # Make a Z enabled Buffer feature class.  This is needed for the
        # 'Add Surface Information' tool
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D')
        arcpy.CreateFeatureclass_management(
            self.outfolder + '\\FBS_Audit.gdb',
            'Buffers_3D',
            geometry_type="POLYGON",
            template=self.outfolder + '\\FBS_Audit.gdb\\Buffers',
            has_z='ENABLED',
            spatial_reference=arcpy.Describe(self.fld_lines).spatialReference.factoryCode)

        # Append the Buffers to Buffers_3D
        arcpy.Append_management(self.outfolder + '\\FBS_Audit.gdb\\Buffers',
                                self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D',
                                "NO_TEST")

        # Delete the Buffers feature class
        arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Buffers')
                                            

    def assign_water_names(self):
        """Attribute the WTR_NM_1 field in APPROX_TEST_PTS_STUDY"""
        #   - Create a bounding box for each stream
        #   - Select all points that fall into each box
        #   - Update the WTR_NM_1 field with the box's WTR_NM field
        #       - If WTR_NM_1 is populated, put the value in WTR_NM2
        print("To be done")

    def generate_report(self):
        """Output Report"""
        print("To be done")

    def add_domains(self):
        """Add Domains to the database"""
        print("To be done")


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
    wsel = sys.argv[2]
    workspace = sys.argv[3]
    out = sys.argv[4]

    # Create an instance of the class and run it
    fbs_audit = FbsAudit(dem, wsel, workspace, out)
