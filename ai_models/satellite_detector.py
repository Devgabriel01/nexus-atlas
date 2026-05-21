"""
Satellite-trained object detector — drop-in replacement for the COCO YOLO
that detects aircraft, ships, vehicles in overhead imagery.

Strategy:
1. Try a pretrained-on-satellite YOLOv8 weight if available in `weights/yolov8-satellite.pt`
2. Fallback: try a HuggingFace model via `ultralytics.YOLO("yolov8n.pt")` + custom
   class remapping for aerial imagery.
3. Final fallback: COCO model with confidence threshold tuned for overhead view.

For full performance, train on RarePlanes (aircraft) or xView (general aerial)
using `train_satellite_yolo.py` and drop the resulting .pt into `weights/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import os


WEIGHTS_DIR = Path(__file__).parent / "weights"
SATELLITE_WEIGHTS = WEIGHTS_DIR / "yolov8-satellite.pt"
COCO_FALLBACK = WEIGHTS_DIR / "yolov8n.pt"

# RarePlanes/xView class subset relevant to NEXUS use cases
AERIAL_CLASSES_OF_INTEREST = {
    "aircraft", "small_aircraft", "large_aircraft", "helicopter",
    "ship", "vessel", "tanker", "fishing_boat", "barge",
    "truck", "vehicle", "car", "bus", "construction_vehicle",
    "building", "warehouse", "storage_tank", "structure",
}

SEVERITY_MAP = {
    "aircraft": "high", "small_aircraft": "high", "large_aircraft": "critical",
    "helicopter": "high",
    "ship": "medium", "vessel": "medium", "tanker": "high", "barge": "medium",
    "fishing_boat": "low",
    "truck": "low", "vehicle": "low", "car": "low", "bus": "low",
    "construction_vehicle": "medium",
    "building": "low", "warehouse": "medium", "storage_tank": "medium",
    "structure": "medium",
}


class SatelliteAwareDetector:
    """YOLOv8 wrapper that prefers satellite-trained weights, with graceful fallback."""

    def __init__(self) -> None:
        self._model = None
        self._mode = "uninitialized"
        self._load()

    def _load(self) -> None:
        try:
            from ultralytics import YOLO
        except ImportError:
            print("[SAT-DET] ultralytics not installed — disabled.")
            return

        if SATELLITE_WEIGHTS.exists():
            self._model = YOLO(str(SATELLITE_WEIGHTS))
            self._mode = "satellite_trained"
            print(f"[SAT-DET] Loaded satellite-trained model: {SATELLITE_WEIGHTS.name}")
            return
        # Optional: pull pre-trained satellite weight from HuggingFace
        hf_model = os.environ.get("SATELLITE_YOLO_HF_REPO")
        if hf_model:
            try:
                from huggingface_hub import hf_hub_download
                local = hf_hub_download(repo_id=hf_model, filename="model.pt")
                self._model = YOLO(local)
                self._mode = "huggingface"
                print(f"[SAT-DET] Loaded HF model: {hf_model}")
                return
            except Exception as e:
                print(f"[SAT-DET] HF fetch failed: {e}")

        # Final fallback: COCO model, tuned conf
        if COCO_FALLBACK.exists():
            self._model = YOLO(str(COCO_FALLBACK))
        else:
            self._model = YOLO("yolov8n.pt")  # downloads
        self._mode = "coco_fallback"
        print("[SAT-DET] Running with COCO weights (limited accuracy on satellite imagery).")

    @property
    def mode(self) -> str:
        return self._mode

    def detect(
        self,
        image_path: str,
        confidence_threshold: float = 0.20,
        bounds: tuple | None = None,
    ) -> List[Dict[str, Any]]:
        if self._model is None:
            return []
        try:
            results = self._model.predict(image_path, conf=confidence_threshold, verbose=False)
        except Exception as e:
            print(f"[SAT-DET] predict failed: {e}")
            return []

        out: List[Dict[str, Any]] = []
        for r in results:
            names = r.names if hasattr(r, "names") else {}
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = names.get(cls_id, f"class_{cls_id}").lower().replace(" ", "_")
                conf = float(box.conf[0])
                # In COCO fallback, accept any overhead-relevant class
                if self._mode == "coco_fallback":
                    if cls_name in ("airplane", "boat", "truck", "car", "bus", "person"):
                        cls_label = {
                            "airplane": "aircraft", "boat": "ship", "truck": "truck",
                            "car": "vehicle", "bus": "bus", "person": "vehicle",
                        }[cls_name]
                    else:
                        continue
                else:
                    if cls_name not in AERIAL_CLASSES_OF_INTEREST:
                        continue
                    cls_label = cls_name

                xyxy = box.xyxy[0].tolist()
                cx_norm = (xyxy[0] + xyxy[2]) / 2 / r.orig_shape[1]
                cy_norm = (xyxy[1] + xyxy[3]) / 2 / r.orig_shape[0]
                lat, lon = _to_geo(cx_norm, cy_norm, bounds)

                out.append({
                    "type": "structure" if "build" in cls_label or "warehouse" in cls_label
                            else cls_label,
                    "severity": SEVERITY_MAP.get(cls_label, "medium"),
                    "latitude": lat,
                    "longitude": lon,
                    "confidence": conf,
                    "description": f"{cls_label} detected (model={self._mode}, conf={conf:.2f})",
                    "detected_by": f"yolov8-{self._mode}",
                    "class": cls_label,
                })
        return out


def _to_geo(cx_norm: float, cy_norm: float, bounds: tuple | None):
    if not bounds:
        return cx_norm, cy_norm  # raw normalized values
    lat_min, lat_max, lon_min, lon_max = bounds
    lat = lat_max - (cy_norm * (lat_max - lat_min))
    lon = lon_min + (cx_norm * (lon_max - lon_min))
    return lat, lon
