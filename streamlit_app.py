# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer

# === CONFIG ===
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === Hardcoded Centroid in WGS84 ===
x = -107.80174291778516
y = 37.49508874613804

st.title("District Plan Lookup")
st.write("Centroid (WGS84):", {"longitude": x, "latitude": y})

manual_point = {
    "x": x,
    "y": y,
    "spatialReference": {"wkid": 4326}
}

district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
district_query = district_layer.query(
    geometry=manual_point,
    geometry_type="esriGeometryPoint",
    spatial_rel="esriSpatialRelIntersects",
    out_fields="PLANNAME"
)

if not district_query.features:
    st.error("No planning district found at specified coordinates.")
else:
    st.subheader("All Intersecting Districts")
    for feature in district_query.features:
        st.write(feature.attributes['PLANNAME'])
