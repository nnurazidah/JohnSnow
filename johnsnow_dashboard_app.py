# johnsnow_dashboard_app.py
# Streamlit + Folium Dashboard for John Snow Cholera Data

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from shapely.geometry import Point

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(page_title="John Snow Cholera Dashboard", layout="wide")
st.title("🗺️ John Snow’s 1854 Cholera Outbreak Dashboard")
st.markdown("""
This dashboard provides a spatial reconstruction of the 1854 cholera outbreak, integrating Excel-based datasets of cholera deaths, water pumps, and area polygons into an interactive geovisualization.
""")

# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.header("Map Controls")
show_deaths = st.sidebar.checkbox("Show Cholera Deaths", value=True)
show_pumps = st.sidebar.checkbox("Show Water Pumps", value=True)
show_area = st.sidebar.checkbox("Show Area Polygons", value=True)

basemap_choice = st.sidebar.selectbox(
    "Select Basemap",
    ["OpenStreetMap", "CartoDB Positron", "Esri WorldImagery"]
)

# ---------------- DATA LOADING ----------------
@st.cache_data
def load_data():
    deaths_df = pd.read_excel("data/cholera_deaths.xlsx")
    pumps_df = pd.read_excel("data/pumps.xlsx")
    deaths_gdf = gpd.GeoDataFrame(
        deaths_df,
        geometry=[Point(xy) for xy in zip(deaths_df["y"], deaths_df["x"])],
        crs="EPSG:4326"
    )
    pumps_gdf = gpd.GeoDataFrame(
        pumps_df,
        geometry=[Point(xy) for xy in zip(pumps_df["y"], pumps_df["x"])],
        crs="EPSG:4326"
    )
    return deaths_gdf, pumps_gdf

@st.cache_data
def load_area_shapefile():
    area_gdf = gpd.read_file("cholera-deaths/polys.shp")
    if area_gdf.crs != "EPSG:4326":
        area_gdf = area_gdf.to_crs("EPSG:4326")
    return area_gdf

deaths_gdf, pumps_gdf = load_data()
area_gdf = load_area_shapefile()

# ---------------- MAP CENTER ----------------
center_lat = deaths_gdf.geometry.y.mean()
center_lon = deaths_gdf.geometry.x.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=None)

# ---------------- BASEMAP ----------------
if basemap_choice == "OpenStreetMap":
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
elif basemap_choice == "CartoDB Positron":
    folium.TileLayer("CartoDB Positron", name="CartoDB Positron").add_to(m)
elif basemap_choice == "Esri WorldImagery":
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri WorldImagery",
        overlay=False,
        control=True
    ).add_to(m)

# ---------------- ADD CHOLERA DEATHS ----------------
if show_deaths:
    death_cluster = MarkerCluster(name="Cholera Deaths").add_to(m)
    for _, row in deaths_gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,
            color="red",
            fill=True,
            fill_opacity=0.7,
            popup="Death Location"
        ).add_to(death_cluster)

# ---------------- ADD WATER PUMPS ----------------
if show_pumps:
    for _, row in pumps_gdf.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup="Water Pump",
            icon=folium.Icon(color="blue", icon="tint", prefix="fa")
        ).add_to(m)

# ---------------- ADD AREA POLYGONS ----------------
if show_area:
    folium.GeoJson(
        data=area_gdf.to_json(),
        name="Cholera Area Polygons",
        style_function=lambda feature: {
            'fillColor': 'orange',
            'color': 'orange',
            'weight': 2,
            'fillOpacity': 0.2,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[col for col in area_gdf.columns if col != 'geometry'],
            aliases=[col for col in area_gdf.columns if col != 'geometry']
        )
    ).add_to(m)

# ---------------- LAYER CONTROL ----------------
folium.LayerControl().add_to(m)

# ---------------- DISPLAY MAP ----------------
st.subheader("Interactive Cholera Map")
st_folium(m, width=1100, height=600)

# ---------------- SUMMARY INFO ----------------
st.subheader("Dataset Summary")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Death Points", len(deaths_gdf))
with col2:
    st.metric("Total Water Pumps", len(pumps_gdf))
