"""
Geographic segmentation using Segment Anything Model (SAM).
Used to isolate regions of interest for further analysis.
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional


class GeoSegmenter:
    def __init__(self):
        self._predictor = None
        self._load_model()

    def _load_model(self):
        try:
            from segment_anything import SamPredictor, sam_model_registry
            model_path = Path(__file__).parent / "weights" / "sam_vit_b.pth"
            if model_path.exists():
                sam = sam_model_registry["vit_b"](checkpoint=str(model_path))
                self._predictor = SamPredictor(sam)
                print("[SAM] Model loaded.")
            else:
                print(f"[SAM] Model not found at {model_path}. Skipping.")
        except ImportError:
            print("[SAM] segment_anything not installed.")
        except Exception as e:
            print(f"[SAM] Load failed: {e}")

    def segment_image(
        self,
        image_path: str,
        point_prompts: Optional[List[List[int]]] = None,
    ) -> List[Dict[str, Any]]:
        """Segment objects in a satellite image."""
        if self._predictor is None:
            return []

        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return []
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._predictor.set_image(image_rgb)

            if point_prompts is None:
                h, w = image.shape[:2]
                point_prompts = [[w // 2, h // 2]]

            masks, scores, _ = self._predictor.predict(
                point_coords=np.array(point_prompts),
                point_labels=np.ones(len(point_prompts), dtype=int),
                multimask_output=True,
            )

            segments = []
            for mask, score in zip(masks, scores):
                contours, _ = __import__("cv2").findContours(
                    mask.astype(np.uint8), __import__("cv2").RETR_EXTERNAL, __import__("cv2").CHAIN_APPROX_SIMPLE
                )
                area = int(mask.sum())
                segments.append({
                    "score": float(score),
                    "area_pixels": area,
                    "contour_count": len(contours),
                })

            return segments

        except Exception as e:
            print(f"[SAM] Segmentation failed: {e}")
            return []
