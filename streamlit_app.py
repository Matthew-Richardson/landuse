# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer

# === CONFIG ===
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === Hardcoded Centroid in WGS84 ===
x = -107.80174291778516
y = 37.49508874613804

st.title("District Plan from Hardcoded Coordinates")
st.write("Using Centroid (WGS84):", {"longitude": x, "latitude": y})

from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
x_merc, y_merc = transformer.transform(x, y)
manual_point = {
    "x": x_merc,
    "y": y_merc,
    "spatialReference": {"wkid": 3857}
}

district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
layer_info = district_layer.properties
sr = layer_info.extent.spatialReference['wkid']
st.write("Layer Spatial Reference WKID:", sr)
district_query = district_layer.query(
    geometry=manual_point,
    geometry_type="esriGeometryPoint",
    spatial_rel="esriSpatialRelIntersects",
    out_fields="PLANNAME"
)

st.write("Raw query result:", district_query)

if not district_query.features:
    st.error("No planning district found at specified coordinates.")
else:
    plan_name = district_query.features[0].attributes['PLANNAME']
    st.subheader("Planning District at Point")
    st.write(plan_name)
