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
        self.cross_sections = ''  # Cross sections
        self.dem = in_dem  # The terrain DEM
        self.fld_lines = ''  # Flood lines
        self.fld_polys = ''  # Flood polygons
        self.outfolder = outfolder  # The output folder for the data
        self.profile_baselines = ''  # Profile Baselines
        self.workspace = in_workspace  # Workspace of the data
        self.wsel = in_wsel  # The WSEL Grid


        # Set the Workspace
        arcpy.env.workspace = self.workspace

        # Get the location of the needed feature classes
        if self.workspace[-4:] in ['.gdb', '.mdb']:
            self.database_table_check()
        else:
            self.shapefile_table_check()

    def add_ground_elevations_area(self):
        """Add ground elevation values from the DEM to Buffers_3D feature class"""

        # Check to see if any buffers exists, if not return
        if not arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D'):
            return

        # Add Surface Information
        arcpy.AddSurfaceInformation_3d(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D',
                                       self.dem, 'Z_MIN;Z_MAX', 'BILINEAR')

        # Update Test_Points based on the Buffers_3D values
        if arcpy.Exists('test_points_lyr'):
            arcpy.Delete_management('test_points_lyr')
        if arcpy.Exists('buffers_3d_lyr'):
            arcpy.Delete_management('buffers_3d_lyr')

        arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'test_points_lyr')
        arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D', 'buffers_3d_lyr')

        arcpy.JoinField_management('test_points_lyr', 'OBJECTID', 'buffers_3d_lyr', 'ORIG_FID',
                                   'Z_Min;Z_Max')

        # Calculate the MinElev and MaxElev fields
        arcpy.CalculateField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'MinElev', '!Z_Min!', 'PYTHON')

        arcpy.CalculateField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'MaxElev', '!Z_Max!', 'PYTHON')

        # Recalculate the values
        self.calc_difference()

    def add_ground_elevations_points(self):
        """Add ground elevation values from the DEM to Test_Points feature class"""
        # Add Surface Information
        arcpy.ddd.AddSurfaceInformation(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        self.dem, 'Z', 'BILINEAR')

        # Values stored in GrdELEV field
        arcpy.CalculateField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'GrELEV', '!Z!', 'PYTHON')

        # Calculate all the NULL GrdElev values to -9999
        if arcpy.Exists("point_lyr"):
            arcpy.Delete_management("point_lyr")
        arcpy.MakeFeatureLayer_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                          "point_lyr", "GrELEV IS NULL")
        arcpy.CalculateField_management('point_lyr', 'GrELEV', '-9999', 'PYTHON')

        # Drop the Z field
        arcpy.DeleteField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'Z')

    def add_wsel_elevations_points(self):
        """Add WSEL elevation values to Test_Points feature class"""
        # Add Surface Information
        arcpy.ddd.AddSurfaceInformation(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        self.wsel, 'Z', 'BILINEAR')

        # Values stored in FldELEV field
        arcpy.CalculateField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                        'FldELEV', '!Z!', 'PYTHON')

        # Calculate all the NULL FldELEV values to -9999
        if arcpy.Exists("point_lyr"):
            arcpy.Delete_management("point_lyr")
        arcpy.MakeFeatureLayer_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                          "point_lyr", "FldELEV IS NULL")
        arcpy.CalculateField_management('point_lyr', 'FldELEV', '-9999', 'PYTHON')

        # Drop the Z field
        arcpy.DeleteField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'Z')

    def assign_water_names(self):
        """Attribute the WTR_NM_1 and WTR_NM_2 field in Test_Points"""
        # Get a list of unique waternames
        water_names = sorted(list(
            set([(row[0]) for row in arcpy.da.SearchCursor(self.cross_sections, 'WTR_NM')])))

        # Iterate through the water names
        for water_name in water_names:
            self.printer("\t{}".format(water_name))

            # Create the bounding box around the cross sections
            self.create_bounding_box(water_name)

            # Select all the Test Points that intersect the bounding box that don't have
            # WTR_NM_1 populated
            points_null = arcpy.MakeFeatureLayer_management(
                self.outfolder + '\\FBS_Audit.gdb\\Test_Points', "points_null",
                "WTR_NM_1 IS NULL")

            arcpy.SelectLayerByLocation_management(
                points_null, "INTERSECT", self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

            arcpy.CalculateField_management(points_null, 'WTR_NM_1',
                                            "'" + str(water_name) + "'", 'PYTHON')

            # Select all the Test Points that intersect the bounding box that have WTR_NM_1
            # populated and WTR_NM_2 is null and the water name doesn't equal WTR_NM_1
            points_null_2 = arcpy.MakeFeatureLayer_management(
                self.outfolder + '\\FBS_Audit.gdb\\Test_Points', "points_null_2",
                "WTR_NM_1 IS NOT NULL AND WTR_NM_2 IS NULL AND WTR_NM_1 <> '" + water_name + "'")

            points_sel_2 = arcpy.SelectLayerByLocation_management(
                points_null_2, "INTERSECT", self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

            arcpy.CalculateField_management(points_sel_2,
                                            'WTR_NM_2', "'" + str(water_name) + "'", 'PYTHON')

            # Delete all the temporary layers and bounding_box
            arcpy.Delete_management("points_null")
            arcpy.Delete_management("points_null_2")

    def assign_water_names_near(self):
        """Assigns water names to the Test Points based on a Near Table"""
        # Remove the Near Table if it already exists
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Near_Table'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Near_Table')

        # Remove Test_Point layer if it exists
        if arcpy.Exists('test_point_layer'):
            arcpy.Delete_management('test_point_layer')

        # Create Test_Point layer
        test_point_layer = arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\Test_Points', 'test_point_layer')

        # Remove S_Profil_Balsn layer if it exists
        if arcpy.Exists('profil_basln_layer'):
            arcpy.Delete_management('profil_basln_layer')

        # Create S_Profil_Basln layer
        profil_basln_layer = arcpy.MakeFeatureLayer_management(
            self.profile_baselines, 'profil_basln_layer')

        # Generate Near Table
        arcpy.GenerateNearTable_analysis(test_point_layer, profil_basln_layer,
                                         self.outfolder + '\\FBS_Audit.gdb\\Near_Table',
                                         closest='CLOSEST', method='PLANAR')

        # Remove Near_Table layer if it exists
        if arcpy.Exists('near_table_layer'):
            arcpy.Delete_management('near_table_layer')

        # Create Near_Table layer
        near_table_layer = arcpy.MakeTableView_management(
            self.outfolder + '\\FBS_Audit.gdb\\Near_Table', 'near_table_layer')

        # Run Add Join Near Table to Test Points based on IN_FID
        arcpy.JoinField_management(
            test_point_layer, 'OBJECTID', near_table_layer, 'IN_FID', ['IN_FID', 'NEAR_FID'])

        # Join S_Profil_Basln to Test Points based on NEAR_FID
        if str(self.profile_baselines).endswith(".shp"):
            id_field = "FID"
        else:
            id_field = "OBJECTID"

        arcpy.JoinField_management(
            test_point_layer, 'NEAR_FID', profil_basln_layer, id_field, ['WTR_NM'])

        # Remove the WTR_NM, IN_FID and NEAR_FID fields if they already exists
        field_list = arcpy.ListFields(test_point_layer)
        for field in field_list:
            if str(field.name) in ['WTR_NM_1', 'WTR_NM_2', 'IN_FID', 'NEAR_FID']:
                arcpy.DeleteField_management(test_point_layer, field.name)

    def calc_difference(self):
        """Calculates the absolute difference of the Flood Elevation and Ground Elevation values"""
        # Create a feature layer
        if arcpy.Exists("test_points_lyr"):
            arcpy.Delete_management("test_points_lyr")
        test_points_lyr = arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\Test_Points', "test_points_lyr")

        # Make an update cursor and iterate through each row
        field_list = ['FldELEV', 'MinElev', 'MaxElev', 'GrELEV', 'ElevDIFF', 'RiskClass',
                      'Tolerance', 'Status']
        with arcpy.da.UpdateCursor(test_points_lyr, field_list) as update_cursor:

            for update_row in update_cursor:
                fld_elev = update_row[0]
                min_elev = update_row[1]
                max_elev = update_row[2]
                gr_elev = update_row[3]
                tolerance = update_row[6]
                status = update_row[7]

                # If FldElev != -9999 and GrElev == -9999: Unknown
                if fld_elev != -9999 and gr_elev == -9999:
                    update_row[4] = -9999
                    update_row[7] = "U"

                # If FldElev == -9999 and GrElev != -9999: FAIL
                elif fld_elev == -9999 and gr_elev != -9999:
                    update_row[4] = -9999
                    update_row[7] = "U"

                # If FldElev == -9999 and GrElev == -9999: N/A
                elif fld_elev == -9999 and gr_elev == -9999:
                    update_row[4] = 0
                    update_row[7] = "NA"

                # If ABS(FldELEV - GrELEV) > Tolerance: PASS
                elif abs(fld_elev - gr_elev) <= tolerance:
                    update_row[4] = abs(fld_elev - gr_elev)
                    update_row[7] = "P"

                # Else: FAIL
                else:
                    update_row[4] = abs(fld_elev - gr_elev)
                    update_row[7] = "F"

                # Calculate if MinElev and MaxElev are populated and Status is 'F'
                if str(min_elev) not in ['None', 'Null', 'NULL'] and \
                   str(max_elev) not in ['None', 'Null', 'NULL'] and \
                   status == 'F':
                    if min_elev - tolerance <= fld_elev <= max_elev + tolerance:
                        update_row[4] = -9999
                        update_row[7] = 'P'

                # Update the row
                update_cursor.updateRow(update_row)

    def check_failed_points(self):
        """For each point that Fails, create a 38 foot horizontal buffer feature class"""
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

    def cleanup(self):
        """Cleanup any remaining items"""
        # Drop unneeded fields
        field_drop_list = ['ORIG_FID', 'DFIRM_ID', 'VERSION_ID', 'FLD_LN_ID', 'LN_TYP',
                           'SOURCE_CIT', 'Z_Min', 'Z_Max']

        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Test_Points'):
            field_list = arcpy.ListFields(self.outfolder + '\\FBS_Audit.gdb\\Test_Points')
            for field in field_list:
                if field.name in field_drop_list:
                    arcpy.DeleteField_management(self.outfolder + '\\FBS_Audit.gdb\\Test_Points',
                                                 field.name)

        # Delete the Buffers_3D feature class
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Buffers_3D')

        # Delete any remaining bounding boxes
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\bounding_box'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

        # Delete the Near Table
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\Near_Table'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\Near_Table')

    def create_bounding_box(self, water_name):
        """Create a bounding box for the water name"""
        # Remove a bounding_box feature class if it already exists
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\bounding_box'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

        # Select the cross sections for the current water_name
        if arcpy.Exists("xs_sel"):
            arcpy.Delete_management("xs_sel")
        xs_sel = arcpy.MakeFeatureLayer_management(self.cross_sections, "xs_sel",
                                                   "WTR_NM = '" + water_name + "'")

        # Simplify them in memory
        if arcpy.Exists("in_memory//simple_xs"):
            arcpy.Delete_management("in_memory//simple_xs")
        if arcpy.Exists("in_memory//simple_xs_Pnt"):
            arcpy.Delete_management("in_memory//simple_xs_Pnt")
        simple_xs = arcpy.SimplifyLine_cartography(
            xs_sel, "in_memory//simple_xs", "POINT_REMOVE", "100 Feet")

        # Create a temporary shapefile to hold each boundary
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\bounding_box_temp'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\bounding_box_temp')

        bounding_box_temp = arcpy.CreateFeatureclass_management(
            self.outfolder + '\\FBS_Audit.gdb', 'bounding_box_temp', 'POLYGON',
            spatial_reference=arcpy.Describe(self.cross_sections).spatialReference.factoryCode)

        # Create a sorted list of the stream stations for the current water name
        station_list = sorted(list(set([(row[0]) for row in arcpy.da.SearchCursor(xs_sel,
                                                                                  'STREAM_STN')])))

        # Create a polygon for every two cross sections and store them in the temporary shapefile
        def create_polygon(in_xs_path, station_1, station_2, out_fc):
            """Creates a polygon based on two cross sections"""
            sel_station = str(station_1) + ", " + str(station_2)

            xs_stations = arcpy.MakeFeatureLayer_management(
                in_xs_path, "xs_stations", "\"STREAM_STN\" IN (" + sel_station + ")")

            if arcpy.Exists("in_memory\\clip_boundary"):
                arcpy.Delete_management("in_memory\\clip_boundary")

            boundary = arcpy.MinimumBoundingGeometry_management(
                xs_stations, "in_memory\\clip_boundary", "CONVEX_HULL", "LIST", "WTR_NM")

            arcpy.Append_management(boundary, out_fc, "NO_TEST")
            arcpy.Delete_management("xs_stations")
            arcpy.Delete_management("in_memory\\clip_boundary")

        # Iterate through the stream station list sending every two stations to the
        # create_polygon function
        for station in range(0, len(station_list) - 1):
            create_polygon(simple_xs, station_list[station],
                           station_list[station + 1], bounding_box_temp)

        # Dissolve the features and remove the temporary shapefile
        if arcpy.Exists(self.outfolder + '\\FBS_Audit.gdb\\bounding_box'):
            arcpy.Delete_management(self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

        arcpy.Dissolve_management(
            bounding_box_temp,
            self.outfolder + '\\FBS_Audit.gdb\\bounding_box')

        # Remove the temporary bounding box
        arcpy.Delete_management(bounding_box_temp)

    def create_file_geodatabase(self):
        """Create an empty File Geodatabase"""
        fbs_db = self.outfolder + '\\FBS_Audit.gdb'
        if arcpy.Exists(fbs_db):
            arcpy.Delete_management(fbs_db)

        arcpy.CreateFileGDB_management(self.outfolder, 'FBS_Audit.gdb')

        # Create the Pass/Fail Domain
        p_f_domain = "PassFail"
        p_f_dict = {"P": "Pass", "F": "Fail", "NA": "NA", "U": "Unknown"}
        arcpy.CreateDomain_management(self.outfolder + '\\FBS_Audit.gdb', p_f_domain,
                                      "PassFail", "TEXT", "CODED")
        for code in p_f_dict:
            arcpy.AddCodedValueToDomain_management(self.outfolder + '\\FBS_Audit.gdb',
                                                   p_f_domain, code, p_f_dict[code])

        # Create the Exception Domain
        exp_domain = "Exception"
        exp_dict = {"PFD": "PFD Exception", "Erosion": "Erosion Exception",
                    "Runup": "Runup Exception", "Combined": "Combined Exception",
                    "OT": "OT Exception", "River_Coast": "River Coast Exception"}
        arcpy.CreateDomain_management(self.outfolder + '\\FBS_Audit.gdb', exp_domain,
                                      "Exception", "TEXT", "CODED")
        for code in exp_dict:
            arcpy.AddCodedValueToDomain_management(self.outfolder + '\\FBS_Audit.gdb',
                                                   exp_domain, code, exp_dict[code])

        # Create the Risk Class Domain
        risk_class = "RiskClass"
        risk_dict = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}
        arcpy.CreateDomain_management(self.outfolder + '\\FBS_Audit.gdb', risk_class,
                                      "Risk Class", "TEXT", "CODED")
        for code in risk_dict:
            arcpy.AddCodedValueToDomain_management(self.outfolder + '\\FBS_Audit.gdb',
                                                   risk_class, code, risk_dict[code])

        # Create the Tolerance Domain
        tolerance = "Tolerance"
        tol_dict = {"1.0": "1.0", "0.5": "0.5"}
        arcpy.CreateDomain_management(self.outfolder + '\\FBS_Audit.gdb', tolerance,
                                      "Tolerance", "FLOAT", "CODED")
        for code in tol_dict:
            arcpy.AddCodedValueToDomain_management(self.outfolder + '\\FBS_Audit.gdb',
                                                   tolerance, code, tol_dict[code])

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
        if arcpy.Exists('sfha_lines'):
            arcpy.Delete_management('sfha_lines')
        sfha_lines = arcpy.MakeFeatureLayer_management(
            self.outfolder + '\\FBS_Audit.gdb\\SFHA_Lines', 'sfha_lines')

        # Remove the flood lines not associated with the polygons
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
        arcpy.AddField_management(test_points_lyr, "RiskClass", "TEXT", field_length=2,
                                  field_domain="RiskClass")
        arcpy.AddField_management(test_points_lyr, "Tolerance", "FLOAT",
                                  field_precision=6, field_scale=2, field_domain="Tolerance")
        arcpy.AddField_management(test_points_lyr, "Status", "TEXT", field_length=2,
                                  field_domain="PassFail")
        arcpy.AddField_management(test_points_lyr, "Validation", "TEXT", field_length=20,
                                  field_domain="Exception")
        arcpy.AddField_management(test_points_lyr, "Comment", "TEXT", field_length=100)

        # Calculate the RiskClass to A for everything
        arcpy.CalculateField_management(test_points_lyr, "RiskClass", "\"A\"", "PYTHON_9.3")

        # Calculate the Tolerance
        arcpy.CalculateField_management(test_points_lyr, "Tolerance", "1", "PYTHON_9.3")

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

    def is_empty_table_check(self):
        """Checks if the required tables are empty"""

        # Get a count of the features.  If the count is 0, return an error an exit
        result = arcpy.GetCount_management(self.fld_lines)
        count = int(result[0])
        if count == 0:
            self.printer("S_Fld_Haz_Ln is empty.  Cannot proceed.  Exiting...", True)

        result = arcpy.GetCount_management(self.fld_polys)
        count = int(result[0])
        if count == 0:
            self.printer("S_Fld_Haz_Ar is empty.  Cannot proceed.  Exiting...", True)

        result = arcpy.GetCount_management(self.profile_baselines)
        count = int(result[0])
        if count == 0:
            self.printer("S_Profil_Basln is empty.  Cannot proceed.  Exiting...", True)

        result = arcpy.GetCount_management(self.cross_sections)
        count = int(result[0])
        if count == 0:
            self.printer("S_XS is empty.  Cannot proceed.  Exiting...", True)

    @staticmethod
    def printer(message, error=False):
        """Prints for both ArcToolbox and Command Line"""
        print(message)
        if not error:
            arcpy.AddMessage(message)
        else:
            arcpy.AddError(message)
            sys.exit(1)

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
        not_matching = []

        dem_spa_ref = str(arcpy.Describe(self.dem).spatialReference.factoryCode)

        if str(arcpy.Describe(self.wsel).spatialReference.factoryCode) != dem_spa_ref:
            not_matching.append("WSEL")

        if str(arcpy.Describe(self.fld_lines).spatialReference.factoryCode) != dem_spa_ref:
            not_matching.append("Flood Lines")

        if str(arcpy.Describe(self.fld_polys).spatialReference.factoryCode) != dem_spa_ref:
            not_matching.append("Flood Polygons")

        if str(arcpy.Describe(self.profile_baselines).spatialReference.factoryCode) != dem_spa_ref:
            not_matching.append("Profile Baselines")

        if str(arcpy.Describe(self.cross_sections).spatialReference.factoryCode) != dem_spa_ref:
            not_matching.append("Cross sections")

        if not_matching:
            self.printer("The following element's spatial references do not match the DEMs: " +
                         ", ".join(not_matching) + "\nExiting...", True)


if __name__ == "__main__":
    # Get user input
    dem = sys.argv[1]
    wsel = sys.argv[2]
    workspace = sys.argv[3]
    out = sys.argv[4]
    fast_names = sys.argv[5]

    # Create an instance of the class and run it
    print("Starting....\n")
    arcpy.AddMessage("Starting....\n")
    fbs_audit = FbsAudit(dem, wsel, workspace, out)

    arcpy.AddMessage("Creating file geodatabase")
    print("Creating file geodatabase")
    fbs_audit.create_file_geodatabase()

    arcpy.AddMessage("Checking spatial reference")
    print("Checking spatial reference")
    fbs_audit.spatial_reference_check()

    arcpy.AddMessage("Checking for empty tables")
    print("Checking for empty tables")
    fbs_audit.is_empty_table_check()

    arcpy.AddMessage("Creating SFHA polyons")
    print("Creating SFHA polyons")
    fbs_audit.create_sfha_flood_polys()

    arcpy.AddMessage("Creating SFHA lines")
    print("Creating SFHA lines")
    fbs_audit.create_sfha_flood_lines()

    arcpy.AddMessage("Creating Test Points")
    print("Creating Test Points")
    fbs_audit.create_test_points()

    arcpy.AddMessage("Add Ground Elevations")
    print("Add Ground Elevations")
    fbs_audit.add_ground_elevations_points()

    arcpy.AddMessage("Add WSEL Elevations")
    print("Add WSEL Elevations")
    fbs_audit.add_wsel_elevations_points()

    arcpy.AddMessage("Calculate differences")
    print("Calculate differences")
    fbs_audit.calc_difference()

    arcpy.AddMessage("Second Pass")
    print("Second Pass")
    fbs_audit.check_failed_points()

    arcpy.AddMessage("Calculate Max/Min value")
    print("Calculate Max/Min value")
    fbs_audit.add_ground_elevations_area()

    arcpy.AddMessage("Adding Water Names to Test_Points")
    print("Adding Water Names to Test_Points")
    if fast_names in ['true', 'True', True]:
        fbs_audit.assign_water_names_near()
    else:
        fbs_audit.assign_water_names()

    arcpy.AddMessage("Cleanup")
    print("Cleanup")
    fbs_audit.cleanup()

    arcpy.AddMessage("\nAll Done")
    print("\nAll Done")
