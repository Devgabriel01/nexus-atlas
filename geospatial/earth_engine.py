"""
Google Earth Engine integration — downloads Sentinel-2 and Landsat imagery.
Requires GEE authentication via service account or `earthengine authenticate`.
"""
import os
import json
from pathlib import Path
from typing import Optional
import sys

try:
    import ee
    import geemap
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False

SCANS_DIR = Path("./scans")
SCANS_DIR.mkdir(exist_ok=True)


class EarthEngineClient:
    def __init__(self):
        self._initialized = False
        if GEE_AVAILABLE:
            self._init_gee()

    def _init_gee(self):
        try:
            key_file = os.environ.get("GEE_KEY_FILE")
            project = os.environ.get("GEE_PROJECT")
            service_account = os.environ.get("GEE_SERVICE_ACCOUNT")

            if key_file and os.path.exists(key_file):
                credentials = ee.ServiceAccountCredentials(service_account, key_file)
                ee.Initialize(credentials, project=project)
            else:
                ee.Initialize(project=project)

            self._initialized = True
            print("[GEE] Initialized successfully.")
        except Exception as e:
            print(f"[GEE] Initialization failed: {e}. Running in mock mode.")

    def download_region(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        date_start: str,
        date_end: str,
        scan_id: str,
        cloud_threshold: float = 20.0,
    ) -> list:
        """Download Sentinel-2 imagery for a bounding box and time range."""
        scan_dir = SCANS_DIR / scan_id
        scan_dir.mkdir(exist_ok=True)

        if not self._initialized:
            print("[GEE] Mock mode — returning empty paths")
            return []

        region = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        count = collection.size().getInfo()
        print(f"[GEE] Found {count} Sentinel-2 scenes")

        if count == 0:
            return []

        # Composite best image
        image = collection.first()
        rgb = image.select(["B4", "B3", "B2"]).divide(10000)

        path_before = str(scan_dir / "sentinel_before.tif")
        scale = _pick_scale(lat_min, lat_max, lon_min, lon_max)
        geemap.ee_export_image(
            rgb,
            filename=path_before,
            scale=scale,
            region=region,
            file_per_band=False,
        )

        return [path_before] if Path(path_before).exists() else []

    def get_ndvi_image(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        date_start: str,
        date_end: str,
    ) -> Optional[object]:
        if not self._initialized:
            return None
        region = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)
        image = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .median()
        )
        nir = image.select("B8")
        red = image.select("B4")
        ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
        return ndvi

    def get_temporal_pair(
        self,
        lat_min, lat_max, lon_min, lon_max,
        date_start: str, date_end: str, scan_id: str,
    ) -> tuple:
        """Return (before_path, after_path) for temporal comparison."""
        scan_dir = SCANS_DIR / scan_id
        scan_dir.mkdir(exist_ok=True)

        if not self._initialized:
            return None, None

        mid = _midpoint_date(date_start, date_end)
        region = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)

        def get_composite(d1, d2):
            return (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(region)
                .filterDate(d1, d2)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
                .median()
                .select(["B4", "B3", "B2"])
                .divide(10000)
            )

        before = get_composite(date_start, mid)
        after = get_composite(mid, date_end)

        before_path = str(scan_dir / "before.tif")
        after_path = str(scan_dir / "after.tif")

        scale = _pick_scale(lat_min, lat_max, lon_min, lon_max)
        try:
            geemap.ee_export_image(before, filename=before_path, scale=scale, region=region)
            geemap.ee_export_image(after, filename=after_path, scale=scale, region=region)
        except Exception as e:
            print(f"[GEE] Export failed: {e}")
            return None, None

        return before_path, after_path


def _pick_scale(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> int:
    """Pick a GEE export scale (m/pixel) so the result stays under the 50 MB cap.
    Bigger regions → coarser pixels. 30 m is Sentinel-2 native-ish at 3 bands.
    """
    deg_area = abs(lat_max - lat_min) * abs(lon_max - lon_min)
    # Rough thresholds tuned for 3-band RGB float32
    if deg_area < 0.1:
        return 30   # ~ < 12 km × 12 km
    if deg_area < 0.5:
        return 60   # ~ < 60 km × 60 km
    if deg_area < 2.0:
        return 100
    if deg_area < 8.0:
        return 200
    return 500


def _midpoint_date(d1: str, d2: str) -> str:
    from datetime import datetime, timedelta
    fmt = "%Y-%m-%d"
    t1 = datetime.strptime(d1, fmt)
    t2 = datetime.strptime(d2, fmt)
    mid = t1 + (t2 - t1) / 2
    return mid.strftime(fmt)
