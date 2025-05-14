# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer

# === CONFIG ===
PARCEL_FEATURE_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"

# === UI ===
st.title("Simple Parcel Finder")
apn_input = st.text_input("Enter Parcel Number (APN)")

if st.button("Find Parcel") and apn_input:
    parcel_layer = FeatureLayer(PARCEL_FEATURE_URL)
    parcel_query = parcel_layer.query(where=f"APN = '{apn_input}'", out_fields="*", return_geometry=False)

    if not parcel_query.features:
        st.error("Parcel not found.")
        st.stop()

    parcel_attrs = parcel_query.features[0].attributes
    st.subheader("Parcel Attributes")
    for key, value in parcel_attrs.items():
        st.write(f"{key}: {value}")
