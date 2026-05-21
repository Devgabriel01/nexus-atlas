"""Generate heatmap overlays from anomaly point clouds."""
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional


class HeatmapGenerator:
    def generate(
        self,
        points: List[Tuple[float, float, float]],  # (lat, lon, weight)
        output_path: str,
        width: int = 512,
        height: int = 512,
        sigma: int = 15,
    ) -> Optional[str]:
        """Generate a heatmap PNG from geographic points."""
        try:
            import cv2

            heatmap = np.zeros((height, width), dtype=np.float32)

            if not points:
                return None

            lats = [p[0] for p in points]
            lons = [p[1] for p in points]
            weights = [p[2] for p in points]

            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)

            lat_range = lat_max - lat_min or 1
            lon_range = lon_max - lon_min or 1

            for lat, lon, weight in points:
                px = int((lon - lon_min) / lon_range * (width - 1))
                py = int((lat_max - lat) / lat_range * (height - 1))
                if 0 <= px < width and 0 <= py < height:
                    heatmap[py, px] += weight

            # Gaussian blur for smooth heatmap
            heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigma)

            # Normalize and apply colormap
            if heatmap.max() > 0:
                heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
            else:
                heatmap = heatmap.astype(np.uint8)

            colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

            # Add alpha channel
            alpha = np.where(heatmap > 10, 180, 0).astype(np.uint8)
            bgra = cv2.cvtColor(colored, cv2.COLOR_BGR2BGRA)
            bgra[:, :, 3] = alpha

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, bgra)
            return output_path

        except Exception as e:
            print(f"[HEATMAP] Generation failed: {e}")
            return None
