# Imports GEE and Initializes with Cloud Project
import ee

# import geemap
from dotenv import load_dotenv
import os

load_dotenv()

EE_PROJECT = os.getenv("CLOUD_PROJECT")
ASSET_PATH = os.getenv("PRIVATE_ASSET_PATH")

ee.Initialize(project=EE_PROJECT)

print(ee.__version__)


#  Load Data to Use in Analyses

# Load Public Assets
mod44 = ee.ImageCollection("MODIS/006/MOD44B")
rap_veg = ee.ImageCollection("projects/rap-data-365417/assets/vegetation-cover-v3")
hansen_gfc = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")
protected_areas = ee.FeatureCollection("WCMC/WDPA/current/polygons")

# Load Private Assets
ntri_villages = ee.FeatureCollection(ASSET_PATH + "NTRI-villages")
ntri_extent = ee.FeatureCollection(ASSET_PATH + "NTRI-boundary")
glad_bareground = ee.Image(ASSET_PATH + "bare_00N_030E")

# Key Variables and Constants
# Export Folder
export_folder = "ntri_bg_data"

# Projection and Scale Constants
mod44_projection = mod44.first().projection()
mod44_scale = mod44_projection.nominalScale().getInfo()
mod44_crs = mod44_projection.crs().getInfo()

# Date filters for Pre and Post Project Time Periods
pre_project_filter = ee.Filter.date("2010", "2016")
post_project_filter = ee.Filter.date("2016", "2021")

# Key Band Names
mod44_bgr_band = "Percent_NonVegetated"

# Mask areas of water (created from Hansen Global Forest Cover Dataset)
land_mask = hansen_gfc.select("datamask").eq(1)

# Create pixel area image (in ha)
area = ee.Image.pixelArea().multiply(0.0001).updateMask(land_mask).rename("area")

# Village Selection
assessment_village_names = [
    "Eleng'ata Dapash",
    "Engaruka chini",
    "Kakoi",
    "Katikati",
    "Kimana",
    "Kitwai A",
    "Losirwa",
    "Matale A",
    "Nadonjukin",
    "Ngoswak",
    "Olchoroonyokie",
    "Sangaiwe",
]

# Filter Villag Collection to Assessment Villages
assessment_villages = ntri_villages.filter(
    ee.Filter.inList("Village", assessment_village_names)
)

# Select Bare Ground Band
mod44_bgr = mod44.select(mod44_bgr_band)

# Filter by Date
mod44_bgr_pre = mod44_bgr.filter(pre_project_filter).mean().rename("mod_bgr_pre")
mod44_bgr_post = mod44_bgr.filter(post_project_filter).mean().rename("mod_bgr_post")

# Convert Percent Pixel to Area
mod44_bgr_area = (
    mod44_bgr_pre.addBands(mod44_bgr_post).divide(100).multiply(area).addBands(area)
)

# Calculate Cumulative Areas (total and bare ground pre and post) for each village
village_bgr_area_mod44 = mod44_bgr_area.reduceRegions(
    collection=assessment_villages,
    scale=mod44_scale,
    crs=mod44_crs,
    reducer=ee.Reducer.sum(),
).map(
    lambda feature: feature.select(
        ["Vil_Mtaa_N", "area", "mod_bgr_pre", "mod_bgr_post"], None, False
    )
)

village_bgr_area_export = ee.batch.Export.table.toDrive(
    collection=village_bgr_area_mod44,
    description="NTRI_village_bareground_area",
    fileFormat="CSV",
    fileNamePrefix="village_bareground_area",
    folder=export_folder,
)

village_bgr_area_export.start()
