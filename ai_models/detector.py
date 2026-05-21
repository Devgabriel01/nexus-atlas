"""
YOLOv8 satellite object detector.
Detects: roads, runways, structures, ships, urban areas, vehicles.
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

MODEL_PATH = Path(__file__).parent / "weights" / "yolov8n.pt"
CLASSES_OF_INTEREST = {
    "road", "runway", "building", "ship", "vehicle",
    "water", "forest", "urban", "structure",
}

SEVERITY_MAP = {
    "runway": "high",
    "ship": "medium",
    "building": "low",
    "vehicle": "medium",
    "structure": "high",
    "road": "low",
    "water": "low",
    "urban": "low",
    "forest": "low",
}


class SatelliteDetector:
    def __init__(self):
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            if MODEL_PATH.exists():
                self._model = YOLO(str(MODEL_PATH))
            else:
                # Download nano model on first use
                MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
                self._model = YOLO("yolov8n.pt")
                print(f"[YOLO] Model loaded from ultralytics hub")
        except Exception as e:
            print(f"[YOLO] Model load failed: {e}. Running in mock mode.")

    def detect(
        self,
        image_path: str,
        confidence_threshold: float = 0.25,
        # Approximate geographic bounds for coordinate conversion
        lat_min: float = 0.0,
        lat_max: float = 1.0,
        lon_min: float = 0.0,
        lon_max: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if self._model is None:
            return self._mock_detections(lat_min, lat_max, lon_min, lon_max)

        try:
            import cv2

            img = cv2.imread(image_path)
            if img is None:
                print(f"[YOLO] Cannot read image: {image_path}")
                return []

            h, w = img.shape[:2]
            results = self._model(image_path, conf=confidence_threshold, verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    cls_name = result.names.get(cls_id, "unknown")
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2

                    lat = lat_max - (cy / h) * (lat_max - lat_min)
                    lon = lon_min + (cx / w) * (lon_max - lon_min)

                    detections.append({
                        "type": "structure",
                        "severity": SEVERITY_MAP.get(cls_name, "low"),
                        "latitude": lat,
                        "longitude": lon,
                        "confidence": conf,
                        "description": f"YOLOv8 detected: {cls_name}",
                        "interpretation": self._interpret(cls_name, conf),
                        "detected_by": "yolov8",
                        "class": cls_name,
                        "bbox": [x1, y1, x2, y2],
                    })

            return detections

        except Exception as e:
            print(f"[YOLO] Detection failed: {e}")
            return []

    def _interpret(self, cls_name: str, confidence: float) -> str:
        interpretations = {
            "runway": f"Potential airstrip or paved surface detected (conf: {confidence:.2f}). Recommend further surveillance.",
            "ship": f"Maritime vessel identified (conf: {confidence:.2f}). Cross-reference with AIS data.",
            "building": f"Structure detected (conf: {confidence:.2f}). Compare with historical baseline.",
            "vehicle": f"Motorized vehicle identified (conf: {confidence:.2f}). Possible activity zone.",
            "structure": f"Unclassified structure (conf: {confidence:.2f}). Manual review recommended.",
        }
        return interpretations.get(cls_name, f"Object of class '{cls_name}' detected with {confidence:.2f} confidence.")

    def _mock_detections(self, lat_min, lat_max, lon_min, lon_max) -> List[Dict[str, Any]]:
        """Return plausible mock detections when model is unavailable."""
        import random
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min
        mock = []
        for _ in range(random.randint(0, 3)):
            cls = random.choice(["building", "road", "vehicle"])
            mock.append({
                "type": "structure",
                "severity": SEVERITY_MAP.get(cls, "low"),
                "latitude": lat_min + random.random() * lat_range,
                "longitude": lon_min + random.random() * lon_range,
                "confidence": round(0.3 + random.random() * 0.6, 3),
                "description": f"[MOCK] {cls} detected",
                "interpretation": self._interpret(cls, 0.5),
                "detected_by": "yolov8_mock",
                "class": cls,
            })
        return mock
