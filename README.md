# MapCreator
This tool help to generate base_import map.txt file which is the main component for map in the [Apollo](https://github.com/ApolloAuto/apollo) . We use prepared geotiff file our territory for map generation.  According to the file information there is a comparison of coordinates on the image with real coordinates. Accuracy of objects size depend on geotiff file. We use ``` gdalinfo ``` for information about geotiff file. 

Information about our geotiff file
```
 
Coordinate System is:
PROJCS["WGS 84 / UTM zone 39N",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",51],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",500000],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["EPSG","32639"]]
    Origin = (357745.018840000033379,6181870.420440000481904)
    Pixel Size = (0.205375334528076,-0.205372475295642)


```
When we make map we use geographic coordinates of  left upper corner like a local center.  We implement the lanes, roads, stop signs and signals. The implementation of junctions works using lanes without borders. The relation of signal and stop signs with stop lanes sets by hand. Overlaps also set by hand.


##### Process of map creation 
[![](http://img.youtube.com/vi/muWFqz1OA2I/0.jpg)](http://www.youtube.com/watch?v=muWFqz1OA2I "Map making process")
