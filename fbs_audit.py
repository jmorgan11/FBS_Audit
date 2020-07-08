1. Start a new GIS project.
2. Load all applicable digital data into the GIS Project.
3. Build a study level TIN = TIN_STUDYX using the digital terrain information. If the
study terrain data is non-digital, the terrain maps will have to be scanned and
georeferenced so that ground elevations can be assigned to the points by hand.
4. Extract the Zone A 1-percent annual flood lines and export them to a new
shapefile/feature class = APPROX_FLD_HAZ_LN_STUDYX and add the new file
to the GIS project.
5. Extract the Zone A 1-percent annual flood polygons and export them to a new
shapefile/feature class = APPROX_FLD_HAZ_PLY_STUDYX and add the new
file to the GIS project.
6. Clip the S_WTR_LN with the APPROX_FLD_HAZ_PLY_STUDYX polygon
feature to create a new APPROX_WTR_LN shapefile/feature class.
7. Note: If there is no S_WTR_LN in the ZONE A areas, one will have to be created
manually using the base map information before the clipping can occur.
8. Using the APPROX_WTR_LN file, create a new point shapefile/feature class =
A_WTR_PTS_STUDYX, which has points that are evenly spaced along the
APPROX_WTR_LN (every 500ft) and add the TEST_PTS_STUDYX to the GIS
project.
9. Create a new line shapefile/feature class, audit cross-section lines
(A_XS_STUDYX), by drawing audit cross sections perpendicular to
APPROX_WTR_LN at the A_WTR_PTS_STUDYX.
10. Assign every A_XS_STUDYX a unique ID.
11. Intersect the A_XS_STUDYXs with the APPROX_FLD_HAZ_LN_STUDYX and
use the intersection points of the two to create a new point shapefile/feature
class AUDIT_STUDYX_PTS being sure to transfer the A_XS_STUDYXs unique
IDs to the AUDIT_STUDYX_PTS.
12. Add the following fields to the TEST_PTS_STUDYX attribute table.
a. GrELEV1 – type = numeric, 6, 2
b. GrELEV2 – type = numeric, 6, 2
c. ElevDIFF – type = numeric, 6, 2
d. RiskClass – type = string, length = 2
e. Status – type = string, length = 2
f. Validation – type = string, length = 20
g. Comment – type = string, length = 100
13. Intersect AUDIT_STUDYX_PTS with the TIN_STUDYX to transfer the
interpolated terrain elevations onto the AUDIT_STUDYX_PTS GrdELEV attribute
field.
14. Note: If terrain was not available in digital format, terrain elevations will have to
be assigned by hand from the georeferenced terrain maps.
15. Break the resulting AUDIT_STUDYX_PTS into two new shapefile/feature class
by doing a unique selection on the attribute XS_ID field and export the first
selection to AUDIT_STUDYX_PTS1, reverse the selection and export the second
selection to AUDIT_STUDYX_PTS2.
16. Do a table join of AUDIT_STUDYX_PTS2 to AUDIT_STUDYX_PTS1.
17. Calculate the ElevDIFF of AUDIT_STUDYX_PTS1 by subtracting GrELEV1 from
GrELEV2.
18. Determine if the AUDIT_STUDYX_PTS1 passes the equal to or greater than the
95-percent pass percentage at the +/- ½ contour threshold; if so, then the study
passes and no more analysis is necessary, skip to Step 27.
19. If the AUDIT_STUDYX_PTS1 fails the equal to or greater than the 95-percent
pass percentage at the +/- ½ contour threshold, then intersect the
AUDIT_STUDYX_PTS1 with the X_RiskClassifications shapefile to transfer the
Risk Classes onto the AUDIT_STUDYX_PTS1.
20. Determine the status of each point based on tolerances of its risk class and
calculate into the Status field the attribute Pass = “P” and Fail = “F”.
21. Select out the individual Risk Classes to their own
AUDIT_STUDYX_PTS1_RskClass shapefile/feature.
22. Determine the pass rate for each audit study’s risk class, if the study now passes
at the Risk Class level, no more analysis is necessary, skip to Step 27.
23. If the AUDIT_STUDYX_PTS fails the equal to or greater than pass rate for each
audit study’s risk classes then intersect the AUDIT_STUDYX_PTS with the NHD
100k subbasin shapefile.
24. Add new filed attribute to the AUDIT_STUDYX_PTS file.
a. Subbasin – type = string, length = 50
25. Calculate the Subbassin field in the AUDIT_STUDYX_PTS file with the
intersected NHD 100k subbasin shapefile.
26. Now determine the AUDIT_STUDYX_PTS pass rate for each audit study’s risk
classes at the subbasin level.
27. Record/Report Results in FBS Self-Certification Report.
28. Submit FBS Self-Certification Report along with the spatial files to the MIP
