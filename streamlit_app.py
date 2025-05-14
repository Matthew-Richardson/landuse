# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer
from shapely.geometry import shape
from pyproj import Transformer

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
    parcel_sr = parcel_feature.geometry.get("spatialReference", {"wkid": 4326})
    centroid = {
        "x": sum(xs) / len(xs),
        "y": sum(ys) / len(ys),
        "spatialReference": parcel_sr
    }

    # Convert centroid to WGS84 for display only
    transformer = Transformer.from_crs(f"EPSG:{parcel_sr['wkid']}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(centroid['x'], centroid['y'])
    st.write("Centroid (WGS84):", {"longitude": lon, "latitude": lat})
