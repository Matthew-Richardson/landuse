# streamlit_app.py
import streamlit as st
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.mapping import WebMap
from arcgis.geometry import project
import tempfile
import os
import base64

# === CONFIG ===
PARCEL_FEATURE_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"
DISTRICTS_LAYER_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Planning_and_Land_Use_Layers/MapServer/2"
ORTHO_LAYER_URL = "https://gis.lpcgov.org/arcgis/rest/services/Orthos/Ortho_2023/MapServer"
DISTRICT_LAYER_MAP = {
    "FORT LEWIS MESA PLAN": "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Planning_and_Land_Use_Layers/MapServer/4",
    "SOUTH EAST LA PLATA": None,
    "ANIMAS VALLEY": None,
    "BAYFIELD DISTRICT PLAN": None,
    "DURANGO DISTRICT PLAN": None,
    "FLORIDA MESA": None,
    "LA POSTA ROAD": None,
    "FLORIDA ROAD": None,
    "JUNCTION CREEK": None,
    "NORTH COUNTY": None,
    "VALLECITO": None,
    "WEST DURANGO": None
}
EXCEL_PATH = "LandUse_Master.xlsx"

# === INIT GIS SESSION with OAuth ===
gis = GIS("https://www.arcgis.com", client_id="YOUR_CLIENT_ID")
gis.authenticate()

# === UI ===
st.title("Parcel Land Use Summary Generator")
apn_input = st.text_input("Enter Parcel Number (APN)")

if st.button("Generate Report") and apn_input:
    df = pd.read_excel(EXCEL_PATH)

    parcel_layer = FeatureLayer(PARCEL_FEATURE_URL)
    parcel_query = parcel_layer.query(where=f"APN = '{apn_input}'", out_fields="*", return_geometry=True)

    if not parcel_query.features:
        st.error("Parcel not found.")
        st.stop()

    parcel_feature = parcel_query.features[0]
    parcel_geom = parcel_feature.geometry

    district_layer = FeatureLayer(DISTRICTS_LAYER_URL)
    district_query = district_layer.query(geometry=parcel_geom, spatial_rel="esriSpatialRelIntersects", out_fields="PLANNAME")

    if not district_query.features:
        st.error("Parcel is not located within any planning district.")
        st.stop()

    plan_name = district_query.features[0].attributes['PLANNAME'].strip().upper()

    if plan_name == "SOUTH EAST LA PLATA":
        summary_text = f"""
Parcel ID: {apn_input}
District Plan: SOUTH EAST LA PLATA
Land Use: No accepted land use code
"""
        st.subheader("Summary")
        st.text(summary_text)
        st.download_button("Download Summary", summary_text, file_name=f"{apn_input}_summary.txt")
        st.stop()

    land_use_url = DISTRICT_LAYER_MAP.get(plan_name)
    if not land_use_url:
        st.error(f"No land use layer configured for district plan: {plan_name}")
        st.stop()

    land_use_layer = FeatureLayer(land_use_url)
    land_use_query = land_use_layer.query(geometry=parcel_geom, spatial_rel="esriSpatialRelIntersects", out_fields="TYPE")

    if not land_use_query.features:
        st.error("No intersecting land use polygon found for this parcel.")
        st.stop()

    land_use_type = land_use_query.features[0].attributes['TYPE']

    match = df[
        (df['DISTRICT PLAN'].str.upper() == plan_name.upper()) &
        (df['TYPE'].str.upper() == land_use_type.upper())
    ]

    if match.empty:
        st.warning("Land use type not found in Excel reference.")
        summary_text = f"""
Parcel ID: {apn_input}
District Plan: {plan_name}
Zone: {land_use_type}
Description: No summary available.
"""
    else:
        zone = match.iloc[0]['TYPE']
        density = match.iloc[0]['SIZE']
        description = match.iloc[0]['DESC']
        summary_text = f"""
Parcel ID: {apn_input}
District Plan: {plan_name}
Zone: {zone}
Density: {density}
Description: {description}
"""

    st.subheader("Land Use Summary")
    st.text(summary_text)
    st.download_button("Download Summary", summary_text, file_name=f"{apn_input}_summary.txt")

    def display_and_download_image(img_bytes, caption, filename):
        st.image(img_bytes, caption=caption)
        b64 = base64.b64encode(img_bytes).decode()
        href = f'<a href="data:image/jpeg;base64,{b64}" download="{filename}">Download {caption}</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.subheader("Map 1: Context Map")
    try:
        context_map = WebMap()
        context_map.add_layer({"url": PARCEL_FEATURE_URL, "popupInfo": {}, "labelingInfo": [{"labelExpressionInfo": {"expression": "$feature.APN"}, "symbol": {"type": "esriTS", "color": [255, 0, 0, 255], "haloColor": [255, 255, 255, 255], "haloSize": 1.5, "font": {"size": 12, "weight": "bold"}}}], "renderer": {"type": "simple", "symbol": {"type": "esriSFS", "style": "esriSFSSolid", "color": [255, 0, 0, 64], "outline": {"color": [255, 0, 0, 255], "width": 1}}}}, options={"title": "Parcel"})
        context_map.set_extent(parcel_geom['extent'])
        context_img = context_map.export_map()
        display_and_download_image(context_img, "Context Map", f"{apn_input}_context.jpg")
    except Exception as e:
        st.warning(f"Could not generate context map: {e}")

    st.subheader("Map 2: Ortho Imagery Map")
    try:
        ortho_map = WebMap()
        ortho_map.add_layer({"url": ORTHO_LAYER_URL, "opacity": 1.0})
        ortho_map.add_layer({"url": PARCEL_FEATURE_URL, "popupInfo": {}, "labelingInfo": [{"labelExpressionInfo": {"expression": "$feature.APN"}, "symbol": {"type": "esriTS", "color": [255, 0, 0, 255], "haloColor": [255, 255, 255, 255], "haloSize": 1.5, "font": {"size": 12, "weight": "bold"}}}], "renderer": {"type": "simple", "symbol": {"type": "esriSLS", "style": "esriSLSSolid", "color": [255, 0, 0, 255], "width": 2}}}, options={"title": "Parcel Outline"})
        ortho_map.set_extent(parcel_geom['extent'])
        ortho_img = ortho_map.export_map()
        display_and_download_image(ortho_img, "Ortho Imagery Map", f"{apn_input}_ortho.jpg")
    except Exception as e:
        st.warning(f"Could not generate ortho map: {e}")

    st.subheader("Map 3: Land Use Classification Map")
    try:
        landuse_map = WebMap()
        landuse_map.add_layer({"url": land_use_url, "opacity": 0.6})
        landuse_map.add_layer({"url": PARCEL_FEATURE_URL, "popupInfo": {}, "labelingInfo": [{"labelExpressionInfo": {"expression": "$feature.APN"}, "symbol": {"type": "esriTS", "color": [255, 0, 0, 255], "haloColor": [255, 255, 255, 255], "haloSize": 1.5, "font": {"size": 12, "weight": "bold"}}}], "renderer": {"type": "simple", "symbol": {"type": "esriSLS", "style": "esriSLSSolid", "color": [255, 0, 0, 255], "width": 2}}}, options={"title": "Parcel"})
        landuse_map.set_extent(parcel_geom['extent'])
        landuse_img = landuse_map.export_map()
        display_and_download_image(landuse_img, "Land Use Classification Map", f"{apn_input}_landuse.jpg")
    except Exception as e:
        st.warning(f"Could not generate land use map: {e}")