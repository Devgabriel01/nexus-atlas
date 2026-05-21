"""
High-level AI analysis orchestrator.
Combines YOLO detection, SAM segmentation, and spectral analysis.
"""
from pathlib import Path
from typing import List, Dict, Any

from ai_models.detector import SatelliteDetector
from ai_models.segmentation import GeoSegmenter


class GeospatialAnalyzer:
    def __init__(self):
        self.detector = SatelliteDetector()
        self.segmenter = GeoSegmenter()

    def full_analysis(
        self,
        image_path: str,
        lat_min: float = 0.0,
        lat_max: float = 1.0,
        lon_min: float = 0.0,
        lon_max: float = 1.0,
    ) -> Dict[str, Any]:
        """Run full AI pipeline on a satellite image."""
        detections = self.detector.detect(
            image_path,
            lat_min=lat_min, lat_max=lat_max,
            lon_min=lon_min, lon_max=lon_max,
        )

        # Cluster detections by proximity
        clusters = self._cluster_detections(detections)

        # Assess overall threat
        threat_level = self._assess_threat(detections)

        return {
            "image_path": image_path,
            "detection_count": len(detections),
            "detections": detections,
            "clusters": clusters,
            "threat_level": threat_level,
            "summary": self._build_summary(detections, threat_level),
        }

    def _cluster_detections(self, detections: List[Dict]) -> List[Dict]:
        if not detections:
            return []
        # Simple geographic clustering
        clusters = []
        used = set()
        for i, d in enumerate(detections):
            if i in used:
                continue
            cluster = [d]
            used.add(i)
            for j, other in enumerate(detections):
                if j in used:
                    continue
                dist = ((d["latitude"] - other["latitude"]) ** 2 + (d["longitude"] - other["longitude"]) ** 2) ** 0.5
                if dist < 0.05:
                    cluster.append(other)
                    used.add(j)
            if len(cluster) > 1:
                clusters.append({
                    "center_lat": sum(c["latitude"] for c in cluster) / len(cluster),
                    "center_lon": sum(c["longitude"] for c in cluster) / len(cluster),
                    "size": len(cluster),
                    "types": list(set(c["class"] for c in cluster if "class" in c)),
                })
        return clusters

    def _assess_threat(self, detections: List[Dict]) -> str:
        if not detections:
            return "none"
        high_conf = [d for d in detections if d.get("confidence", 0) > 0.7]
        critical_types = [d for d in detections if d.get("severity") in ("high", "critical")]
        if len(critical_types) > 2 or len(high_conf) > 5:
            return "high"
        if len(critical_types) > 0 or len(high_conf) > 2:
            return "medium"
        return "low"

    def _build_summary(self, detections: List[Dict], threat: str) -> str:
        if not detections:
            return "No significant objects detected in analyzed region."
        types = {}
        for d in detections:
            cls = d.get("class", "unknown")
            types[cls] = types.get(cls, 0) + 1
        type_str = ", ".join(f"{v} {k}(s)" for k, v in types.items())
        return (
            f"AI analysis detected {len(detections)} objects: {type_str}. "
            f"Overall threat assessment: {threat.upper()}."
        )
