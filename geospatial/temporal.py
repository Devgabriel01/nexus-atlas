"""Temporal change detection between two satellite image epochs."""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional


class TemporalAnalyzer:
    def analyze(
        self,
        scan_id: str,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        from earth_engine import EarthEngineClient
        client = EarthEngineClient()
        before_path, after_path = client.get_temporal_pair(
            lat_min, lat_max, lon_min, lon_max,
            date_start or "2022-01-01",
            date_end or "2024-01-01",
            scan_id=scan_id,
        )

        if not before_path or not after_path:
            return []

        return self._detect_changes(before_path, after_path, lat_min, lat_max, lon_min, lon_max)

    def _detect_changes(
        self,
        before_path: str,
        after_path: str,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
    ) -> List[Dict[str, Any]]:
        try:
            import cv2
            import rasterio

            def load_rgb(path):
                with rasterio.open(path) as src:
                    if src.count >= 3:
                        r = src.read(1)
                        g = src.read(2)
                        b = src.read(3)
                        img = np.stack([r, g, b], axis=-1)
                    else:
                        band = src.read(1)
                        img = np.stack([band, band, band], axis=-1)
                    img = ((img - img.min()) / (img.max() - img.min() + 1e-6) * 255).astype(np.uint8)
                    return img

            before_img = load_rgb(before_path)
            after_img = load_rgb(after_path)

            if before_img.shape != after_img.shape:
                h = min(before_img.shape[0], after_img.shape[0])
                w = min(before_img.shape[1], after_img.shape[1])
                before_img = before_img[:h, :w]
                after_img = after_img[:h, :w]

            before_gray = cv2.cvtColor(before_img, cv2.COLOR_RGB2GRAY)
            after_gray = cv2.cvtColor(after_img, cv2.COLOR_RGB2GRAY)

            diff = cv2.absdiff(before_gray, after_gray)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            h, w = before_img.shape[:2]
            lat_range = lat_max - lat_min
            lon_range = lon_max - lon_min

            anomalies = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 100:
                    continue
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Convert pixel coords to geographic
                lat = lat_max - (cy / h) * lat_range
                lon = lon_min + (cx / w) * lon_range

                severity = "low"
                if area > 5000:
                    severity = "critical"
                elif area > 2000:
                    severity = "high"
                elif area > 500:
                    severity = "medium"

                anomalies.append({
                    "type": "temporal_change",
                    "severity": severity,
                    "latitude": lat,
                    "longitude": lon,
                    "confidence": min(0.99, area / 10000),
                    "description": f"Significant surface change detected (area: {area:.0f}px)",
                    "interpretation": "Temporal analysis indicates land-use or environmental change.",
                    "detected_by": "temporal_cv",
                    "class": "change_zone",
                })

            return anomalies[:50]  # cap results

        except Exception as e:
            print(f"[TEMPORAL] Change detection failed: {e}")
            return []
