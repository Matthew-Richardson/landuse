# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer
from shapely.geometry import shape
from shapely.geometry import Point

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
    geojson_geom = {
        "type": "Polygon",
        "coordinates": parcel_geom["rings"]
    }
    parcel_shape = shape(geojson_geom)
    centroid = parcel_shape.centroid
    centroid_point = {
        "x": centroid.x,
        "y": centroid.y,
        "spatialReference": {"wkid": 4326}
    }

    district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
    district_query = district_layer.query(
        geometry=centroid_point,
        geometry_type="esriGeometryPoint",
        spatial_rel="esriSpatialRelIntersects",
        out_fields="PLANNAME"
    )

    if not district_query.features:
        st.error("Parcel centroid is not located within any planning district.")
        st.stop()

    detected_plan = district_query.features[0].attributes['PLANNAME'].strip().upper()
    st.subheader("Detected Planning District")
    st.write(detected_plan)
