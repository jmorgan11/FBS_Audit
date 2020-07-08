# TODO: Check for spatial analyst license

# TODO: Create an empty File Geodatabase

# TODO: Get the spatial reference system

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
#   - S_GEN_STRUCT - (Optional)
#   - S_TRNSPORT_LN (or aerials) - (Optional)
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
#     c. FldELEV    – Numeric, 6, 2
#     d. MinElev    - Numeric, 6, 2
#     e. MaxElev    - Numeric, 6, 2
#     f. GrELEV     – Numeric, 6, 2
#     g. ElevDIFF   – Numeric, 6, 2
#     h. RiskClass  – String, length = 2
#     i. Tolerance  - Numeric, 6, 2
#     j. Status     – String, length = 2
#     k. Validation – String, length = 20
#     l. Comment    – String, length = 100

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
