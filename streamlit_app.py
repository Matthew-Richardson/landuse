# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer
from shapely.geometry import shape

# === CONFIG ===
PARCEL_FEATURE_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === UI ===
st.title("Simple Parcel Finder")
apn_input = st.text_input("Enter Parcel Number (APN)")

if st.button("Find Parcel") and apn_input:
    parcel_layer = FeatureLayer(PARCEL_FEATURE_URL)
    parcel_query = parcel_layer.query(where=f"APN = '{apn_input}'", out_fields="*", return_geometry=True)

    if not parcel_query.features:
        st.error("Parcel not found.")
        st.stop()

    parcel_feature = parcel_query.features[0]
    parcel_attrs = parcel_feature.attributes
    st.subheader("Parcel Attributes")
    for key, value in parcel_attrs.items():
        st.write(f"{key}: {value}")

    # Calculate parcel centroid from geometry
    rings = parcel_feature.geometry["rings"]
    coords = rings[0]
    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    centroid = {
        "x": sum(xs) / len(xs),
        "y": sum(ys) / len(ys),
        "spatialReference": {"wkid": 4326}
    }

    # Query district by centroid point
    district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
    district_query = district_layer.query(
        geometry=centroid,
        geometry_type="esriGeometryPoint",
        spatial_rel="esriSpatialRelIntersects",
        out_fields="PLANNAME"
    )

    if not district_query.features:
        st.error("No planning district found at parcel centroid.")
    else:
        plan_name = district_query.features[0].attributes['PLANNAME']
        st.subheader("Planning District")
        st.write(plan_name)
