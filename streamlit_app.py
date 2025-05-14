# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer

# === CONFIG ===
PARCEL_FEATURE_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === UI ===
st.title("Parcel District Detector")
apn_input = st.text_input("Enter Parcel Number (APN)")

if st.button("Check District") and apn_input:
    parcel_layer = FeatureLayer(PARCEL_FEATURE_URL)
    parcel_query = parcel_layer.query(where=f"APN = '{apn_input}'", out_fields="*", return_geometry=True)

    if not parcel_query.features:
        st.error("Parcel not found.")
        st.stop()

    parcel_geom = parcel_query.features[0].geometry

    district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
    district_query = district_layer.query(
        geometry=parcel_geom,
        geometry_type="esriGeometryPolygon",
        spatial_rel="esriSpatialRelContains",
        out_fields="PLANNAME"
    )

    if not district_query.features:
        st.error("Parcel is not located within any planning district.")
        st.stop()

    detected_plan = district_query.features[0].attributes['PLANNAME'].strip().upper()
    st.subheader("Detected Planning District")
    st.write(detected_plan)
