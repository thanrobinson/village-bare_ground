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

# Load Public Assets
mod44 = ee.ImageCollection("MODIS/006/MOD44B")
rap_veg = ee.ImageCollection("projects/rap-data-365417/assets/vegetation-cover-v3")
hansen_gfc = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")
protected_areas = ee.FeatureCollection("WCMC/WDPA/current/polygons")
ag_2015 = ee.ImageCollection("users/potapovpeter/Global_cropland_2015")
ag_2019 = ee.ImageCollection("users/potapovpeter/Global_cropland_2019")

# Load Private Assets
ntri_villages = ee.FeatureCollection(ASSET_PATH + "NTRI-villages")
ntri_extent = ee.FeatureCollection(ASSET_PATH + "NTRI-boundary")
glad_bareground = ee.Image(ASSET_PATH + "bare_00N_030E")
rap_rl_samples = ee.FeatureCollection(ASSET_PATH + "us_rangeland_samples")

# Key Variables and Constants
# Export Folder
export_folder = "ntri_bg_data"

# Projection and Scale Constants
mod44_projection = mod44.first().projection()
mod44_scale = mod44_projection.nominalScale().getInfo()
mod44_crs = mod44_projection.crs().getInfo()

rap_projection = rap_veg.first().projection()
rap_scale = rap_projection.nominalScale().getInfo()
rap_crs = rap_projection.crs().getInfo()

glad_projection = glad_bareground.projection()
glad_scale = glad_projection.nominalScale().getInfo()
glad_crs = glad_projection.crs().getInfo()

ag_projection = ag_2015.first().projection()
ag_scale = ag_projection.nominalScale().getInfo()
ag_crs = ag_projection.crs().getInfo()


# Date filters for Pre and Post Project Time Periods
pre_project_filter = ee.Filter.date("2010", "2016")
post_project_filter = ee.Filter.date("2016", "2021")

# Key Band Names
mod44_bgr_band = "Percent_NonVegetated"
rap_bgr_band = "BGR"

# Mask areas of water (created from Hansen Global Forest Cover Dataset)
land_mask = hansen_gfc.select("datamask").eq(1)

# Create pixel area image (in ha)
area = ee.Image.pixelArea().multiply(0.0001).updateMask(land_mask).rename("area")


# Key Feature Collection Cleaning Functions
# Remove Geometries
def remove_geometries(feature):
    return ee.Feature(None, None).copyProperties(feature)


# Inner Join Parameters
filter_field = "system:index"
sample_filter = ee.Filter.equals(leftField=filter_field, rightField=filter_field)

sample_join = ee.Join.inner("primary", "secondary")


def clean_join(feature):
    primary = ee.Feature(feature.get("primary"))
    secondary = ee.Feature(feature.get("secondary"))
    return ee.Feature(None, None).copyProperties(primary).copyProperties(secondary)


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

# Filter Village Collection to Assessment Villages
assessment_villages = ntri_villages.filter(
    ee.Filter.inList("Village", assessment_village_names)
)

# Select Bare Ground Band
mod44_bgr = mod44.select(mod44_bgr_band)
rap_bgr = rap_veg.select(rap_bgr_band)


### MOD44 - RAP Comparison
# Filter by Date
mod44_bgr_pre = mod44_bgr.filter(pre_project_filter).mean().rename("mod_bgr_pre")
mod44_bgr_post = mod44_bgr.filter(post_project_filter).mean().rename("mod_bgr_post")

rap_bgr_pre = rap_bgr.filter(pre_project_filter).mean().rename("rap_bgr_pre")
rap_bgr_post = rap_bgr.filter(post_project_filter).mean().rename("rap_bgr_post")

# Convert Percent Pixel to Area
mod44_bgr_area = (
    mod44_bgr_pre.addBands(mod44_bgr_post)
    .divide(100)
    .multiply(area)
    .addBands(area.rename("mod_area"))
    .setDefaultProjection(mod44_projection)
)

rap_bgr_area = (
    rap_bgr_pre.addBands(rap_bgr_post)
    .divide(100)
    .multiply(area)
    .addBands(area.rename("rap_area"))
    .setDefaultProjection(rap_projection)
)

mod44_us_sample = mod44_bgr_area.reduceRegions(
    reducer=ee.Reducer.sum(),
    collection=rap_rl_samples,
    scale=mod44_scale,
    crs=mod44_crs,
)

rap_us_sample = rap_bgr_area.reduceRegions(
    reducer=ee.Reducer.sum(), collection=rap_rl_samples, scale=rap_scale, crs=rap_crs
)


mod44_rap_samples = sample_join.apply(
    mod44_us_sample, rap_us_sample, sample_filter
).map(clean_join)


mod44_rap_samples_export = ee.batch.Export.table.toDrive(
    collection=mod44_rap_samples,
    description="rap_mod44_bgr_areas",
    fileFormat="CSV",
    fileNamePrefix="rap_mod44_bgr_areas",
    folder=export_folder,
)


### MOD44 - GLAD Bare Ground Comparison
mod_bgr_2010 = (
    mod44_bgr.filterDate("2010", "2011")
    .first()
    .divide(100)
    .multiply(area)
    .addBands(area)
    .rename(["mod_bgr_area", "mod_area"])
    .setDefaultProjection(mod44_projection)
)

glad_bgr = (
    glad_bareground.divide(100)
    .multiply(area)
    .addBands(area)
    .rename(["glad_bgr_area", "glad_area"])
)

# Village area stats created for MOD44 dataset at MOD44 resolution and crs
village_mod_stats = mod_bgr_2010.reduceRegions(
    collection=assessment_villages,
    scale=mod44_scale,
    crs=mod44_crs,
    reducer=ee.Reducer.sum(),
).select(["Vil_Mtaa_N", "mod_area", "mod_bgr_area"])

# Village area stats created for GLAD dataset at GLAD resolution and crs
village_glad_stats = glad_bgr.reduceRegions(
    collection=assessment_villages,
    scale=glad_scale,
    crs=glad_crs,
    reducer=ee.Reducer.sum(),
).select(["Vil_Mtaa_N", "glad_area", "glad_bgr_area"])

mod44_glad_samples = sample_join.apply(
    village_mod_stats, village_glad_stats, sample_filter
).map(clean_join)

mod44_glad_export = ee.batch.Export.table.toDrive(
    collection=mod44_glad_samples,
    description="glad_mod44_bgr_areas",
    fileFormat="CSV",
    fileNamePrefix="glad_mod44_bgr_areas",
    folder=export_folder,
)

## agland Change
ag_area = (
    ag_2015.mosaic()
    .rename("ag_2015")
    .addBands(ag_2019.mosaic().rename("ag_2019"))
    .multiply(area)
    .addBands(area.rename("area"))
    .setDefaultProjection(ag_projection)
)

village_ag_stats = (
    ag_area.reduceRegions(
        collection=assessment_villages,
        scale=ag_scale,
        crs=ag_crs,
        reducer=ee.Reducer.sum(),
    )
    .select(["Vil_Mtaa_N", "ag_2015", "ag_2019", "area"])
    .map(remove_geometries)
)

ag_area_export = ee.batch.Export.table.toDrive(
    collection=village_ag_stats,
    description="village_ag_areas",
    fileFormat="CSV",
    fileNamePrefix="village_ag_areas",
    folder=export_folder,
)

# Export Runs
mod44_rap_samples_export.start()
mod44_glad_export.start()
ag_area_export.start()
