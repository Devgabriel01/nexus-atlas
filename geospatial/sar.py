"""
Sentinel-1 SAR (Synthetic Aperture Radar) analysis.

SAR penetrates clouds, smoke, darkness — critical for monitoring tropical regions
and detecting human-built structures (ships, vehicles, deforestation) that are
otherwise obscured.

This module uses Google Earth Engine's `COPERNICUS/S1_GRD` collection
(Ground Range Detected, IW mode, VV+VH polarizations).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import ee
    import geemap
    SAR_AVAILABLE = True
except ImportError:
    SAR_AVAILABLE = False

SCANS_DIR = Path("./scans")


class SARAnalyzer:
    """
    Sentinel-1 SAR change detection using log-ratio of VV backscatter
    between two time windows. High |log-ratio| = strong scattering change
    (e.g. forest → bare soil = +, structure built = +/-, flooding = -).
    """

    def __init__(self) -> None:
        self._initialized = False
        if SAR_AVAILABLE:
            self._init_gee()

    def _init_gee(self) -> None:
        import os
        try:
            project = os.environ.get("GEE_PROJECT")
            if project:
                ee.Initialize(project=project)
            else:
                ee.Initialize()
            self._initialized = True
            print("[SAR] Earth Engine ready for Sentinel-1 queries.")
        except Exception as e:
            print(f"[SAR] Init failed: {e} — SAR features disabled.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_changes(
        self,
        scan_id: str,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        date_start: str, date_end: str,
        threshold_db: float = 3.0,
        download: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Detect significant backscatter changes between two halves of the time range.

        Returns a list of anomaly dicts compatible with the scan pipeline.
        """
        if not self._initialized:
            print("[SAR] Mock mode — returning empty.")
            return []

        try:
            region = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)
            mid = _midpoint_date(date_start, date_end)

            base = (
                ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(region)
                .filter(ee.Filter.eq("instrumentMode", "IW"))
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                .select("VV")
            )

            before = base.filterDate(date_start, mid).median()
            after = base.filterDate(mid, date_end).median()

            count_before = base.filterDate(date_start, mid).size().getInfo()
            count_after = base.filterDate(mid, date_end).size().getInfo()
            print(f"[SAR] Scenes — before: {count_before}, after: {count_after}")
            if count_before == 0 or count_after == 0:
                return []

            # Log-ratio in dB; |diff| > threshold_db is a strong change
            diff = after.subtract(before).rename("logratio_db")
            mask = diff.abs().gt(threshold_db)
            changes = diff.updateMask(mask)

            # Save composite as a GeoTIFF for the report
            anomalies: List[Dict[str, Any]] = []
            if download:
                scan_dir = SCANS_DIR / scan_id
                scan_dir.mkdir(parents=True, exist_ok=True)
                scale = _pick_scale(lat_min, lat_max, lon_min, lon_max)
                try:
                    out_path = str(scan_dir / "sar_changes.tif")
                    geemap.ee_export_image(
                        diff, filename=out_path, scale=scale, region=region
                    )
                    print(f"[SAR] Exported {out_path}")
                except Exception as e:
                    print(f"[SAR] export failed: {e}")

            # Sample N hotspot points where the mask is True
            try:
                samples = changes.sample(
                    region=region,
                    scale=_pick_scale(lat_min, lat_max, lon_min, lon_max),
                    numPixels=50,
                    geometries=True,
                    seed=42,
                ).getInfo()
                features = samples.get("features", []) if isinstance(samples, dict) else []
            except Exception as e:
                print(f"[SAR] sampling failed: {e}")
                features = []

            for f in features[:25]:
                geom = f.get("geometry", {})
                coords = geom.get("coordinates", [None, None])
                logratio = f.get("properties", {}).get("logratio_db", 0)
                severity = _severity_from_db(abs(logratio))
                anomalies.append({
                    "type": "sar_change",
                    "severity": severity,
                    "latitude": float(coords[1]) if coords[1] is not None else 0.0,
                    "longitude": float(coords[0]) if coords[0] is not None else 0.0,
                    "confidence": min(abs(logratio) / 10.0, 1.0),
                    "description": f"SAR backscatter change {logratio:+.1f} dB "
                                   f"(VV-pol Sentinel-1, cloud-penetrating)",
                    "detected_by": "sentinel-1-sar",
                    "class": "backscatter_anomaly",
                })

            print(f"[SAR] Produced {len(anomalies)} change anomalies")
            return anomalies

        except Exception as e:
            print(f"[SAR] Analysis error: {e}")
            return []

    def flood_extent(
        self,
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        date_start: str, date_end: str,
        water_threshold_db: float = -17.0,
    ) -> Optional[Dict[str, Any]]:
        """Estimate flooded area: SAR VV pixels below threshold dB are water."""
        if not self._initialized:
            return None
        region = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)
        img = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(region)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV")
            .median()
        )
        water = img.lt(water_threshold_db)
        try:
            area_m2 = water.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=30,
                maxPixels=1e9,
            ).getInfo()
            return {"flooded_m2": area_m2.get("VV", 0)}
        except Exception as e:
            print(f"[SAR] flood_extent failed: {e}")
            return None


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _midpoint_date(d1: str, d2: str) -> str:
    from datetime import datetime, timedelta
    fmt = "%Y-%m-%d"
    t1 = datetime.strptime(d1, fmt)
    t2 = datetime.strptime(d2, fmt)
    mid = t1 + (t2 - t1) / 2
    return mid.strftime(fmt)


def _pick_scale(lat_min, lat_max, lon_min, lon_max) -> int:
    area = abs(lat_max - lat_min) * abs(lon_max - lon_min)
    if area < 0.1:
        return 30
    if area < 0.5:
        return 60
    if area < 2.0:
        return 100
    if area < 8.0:
        return 200
    return 500


def _severity_from_db(db_abs: float) -> str:
    if db_abs >= 8:
        return "critical"
    if db_abs >= 6:
        return "high"
    if db_abs >= 4:
        return "medium"
    return "low"
