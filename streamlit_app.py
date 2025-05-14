# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer
from shapely.geometry import Point, shape
from pyproj import Transformer

# === CONFIG ===
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === Hardcoded Centroid in WGS84 ===
x = -107.840644
y = 37.406496°

st.title("District Plan Lookup")
st.write("Centroid (WGS84):", {"longitude": x, "latitude": y})

# Reproject centroid to EPSG:3857 (Web Mercator)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x_merc, y_merc = transformer.transform(x, y)
reprojected_point = {
    "x": x_merc,
    "y": y_merc,
    "spatialReference": {"wkid": 3857}
}

# Query all intersecting polygons
point_geom = Point(x_merc, y_merc)
district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
district_query = district_layer.query(
    geometry=reprojected_point,
    geometry_type="esriGeometryPoint",
    spatial_rel="esriSpatialRelIntersects",
    out_fields="PLANNAME",
    return_geometry=True
)

# Check which geometry contains the point
matching_plan = None
for feature in district_query.features:
    polygon_geom = feature.geometry
    geojson_geom = {
        "type": "Polygon",
        "coordinates": polygon_geom["rings"]
    }
    polygon_shape = shape(geojson_geom)
    if polygon_shape.contains(point_geom):
        matching_plan = feature.attributes["PLANNAME"]
        break

if matching_plan:
    st.subheader("Detected Planning District")
    st.write(matching_plan)
else:
    st.error("No planning district polygon contains the centroid.")
