"""NDVI computation using Earth Engine or local raster files."""
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional


class NDVIAnalyzer:
    def compute(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        date_start: str = "2023-01-01",
        date_end: str = "2024-01-01",
        tif_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if tif_path and Path(tif_path).exists():
            return self._compute_from_tif(tif_path)
        return self._compute_via_gee(lat_min, lat_max, lon_min, lon_max, date_start, date_end)

    def _compute_from_tif(self, tif_path: str) -> Dict[str, Any]:
        try:
            import rasterio
            with rasterio.open(tif_path) as src:
                # Assume band 1 = NIR, band 2 = Red  (Sentinel-2 B8, B4)
                if src.count >= 2:
                    nir = src.read(1).astype(float)
                    red = src.read(2).astype(float)
                else:
                    band = src.read(1).astype(float)
                    nir = red = band

                denom = nir + red
                denom[denom == 0] = 1e-6
                ndvi = (nir - red) / denom
                ndvi = np.clip(ndvi, -1, 1)

                return {
                    "ndvi_mean": float(np.nanmean(ndvi)),
                    "ndvi_min": float(np.nanmin(ndvi)),
                    "ndvi_max": float(np.nanmax(ndvi)),
                    "ndvi_std": float(np.nanstd(ndvi)),
                    "vegetation_fraction": float(np.mean(ndvi > 0.3)),
                    "source": "local_tif",
                }
        except Exception as e:
            return {"error": str(e), "source": "local_tif"}

    def _compute_via_gee(
        self, lat_min, lat_max, lon_min, lon_max, date_start, date_end
    ) -> Dict[str, Any]:
        try:
            import ee
            ee.Initialize()
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

            stats = ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.minMax(), sharedInputs=True
                ),
                geometry=region,
                scale=30,
                maxPixels=1e9,
            ).getInfo()

            return {
                "ndvi_mean": stats.get("NDVI_mean", 0.0),
                "ndvi_min": stats.get("NDVI_min", 0.0),
                "ndvi_max": stats.get("NDVI_max", 0.0),
                "source": "gee",
            }
        except Exception as e:
            return {
                "error": str(e),
                "ndvi_mean": 0.0,
                "ndvi_min": 0.0,
                "ndvi_max": 0.0,
                "source": "mock",
            }
