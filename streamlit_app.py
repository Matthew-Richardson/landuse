# streamlit_app.py
import streamlit as st
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import folium
from streamlit_folium import st_folium
import base64
from shapely.geometry import shape
import json
import io
from PIL import Image

# === CONFIG ===
PARCEL_FEATURE_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"
ORTHO_LAYER_URL = "https://gis.lpcgov.org/arcgis/rest/services/Orthos/Ortho_2023/MapServer"
DISTRICT_LAYER_MAP = {
    "SOUTH EAST LA PLATA": None,
    "NORTH COUNTY DISTRICT PLAN": "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/North_County/FeatureServer/0"
}
EXCEL_PATH = "LandUse_Master.xlsx"

# === INIT GIS SESSION with public access ===

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
    district_query = district_layer.query(
        geometry=parcel_geom,
        geometry_type="esriGeometryPolygon",
        spatial_rel="esriSpatialRelIntersects",
        out_fields="PLANNAME"
    )

    if not district_query.features:
        st.error("Parcel is not located within any planning district.")
        st.stop()

    plan_name = district_query.features[0].attributes['PLANNAME'].strip().upper()
    st.write(f"Detected PLANNAME: '{plan_name}'")

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
    try:
        land_use_query = land_use_layer.query(geometry=parcel_geom, spatial_rel="esriSpatialRelIntersects", out_fields="TYPE")
    except Exception as e:
        st.error("Failed to query the land use layer. It may require login or does not support spatial queries.")
        st.stop()

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

    # === Map Display with Polygon ===
    st.subheader("Parcel Map Preview")
    try:
        folium_map = folium.Map(zoom_start=17)
        geojson = {"type": "Feature", "geometry": parcel_geom, "properties": {"APN": apn_input}}
        folium.GeoJson(
            geojson,
            name="Parcel",
            tooltip=folium.GeoJsonTooltip(fields=["APN"]),
            style_function=lambda x: {"fillColor": "#ff0000", "color": "#ff0000", "weight": 2, "fillOpacity": 0.1}
        ).add_to(folium_map)

        coords = shape(parcel_geom).centroid.coords[0]
        folium_map.location = [coords[1], coords[0]]

        # Show interactive map
        st_data = st_folium(folium_map, width=700, height=500)

        st.markdown("### Download Map Image")
        st.markdown("Due to limitations in cloud rendering, download is only available via screenshot.")
    except Exception as e:
        st.warning(f"Could not generate preview map: {e}")
