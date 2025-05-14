# streamlit_app.py
import streamlit as st
from arcgis.features import FeatureLayer
from shapely.geometry import Point, shape

# === CONFIG ===
PARCEL_LAYER_URL = "https://gis.lpcgov.org/arcgis/rest/services/Operational_Layers/Parcel_Related/MapServer/4"
DISTRICTS_LAYER_URL = "https://services2.arcgis.com/ilLrLpXfElYxSy9y/arcgis/rest/services/Planning_District_Outline/FeatureServer/0"

# === Streamlit UI ===
st.title("District Plan Lookup by APN")
apn_input = st.text_input("Enter Parcel Number (APN)")

if apn_input:
    parcel_layer = FeatureLayer(PARCEL_LAYER_URL)
    parcel_query = parcel_layer.query(where=f"APN = '{apn_input}'", out_fields="*", return_geometry=True)

    if not parcel_query.features:
        st.error("Parcel not found.")
        st.stop()

    parcel_geom = parcel_query.features[0].geometry
    rings = parcel_geom["rings"]
    coords = rings[0]
    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    x = sum(xs) / len(xs)
    y = sum(ys) / len(ys)

    st.write("Centroid (WGS84):", {"longitude": x, "latitude": y})

    # Use centroid directly in WGS84
    point_geom = Point(x, y)
    reprojected_point = {
        "x": x,
        "y": y,
        "spatialReference": {"wkid": 4326}
    }

    # Query all intersecting polygons
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
