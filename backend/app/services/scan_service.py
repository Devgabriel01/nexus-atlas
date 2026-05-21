import asyncio
from datetime import datetime, timezone
from pathlib import Path
from app.database import AsyncSessionLocal
from app.models.scan import Scan, ScanStatus
from app.models.anomaly import Anomaly
from app.utils.logger import logger
from app.services.event_bus import get_bus

bus = get_bus()


async def _emit(scan_id: str, stage: str, message: str, progress: int, **extra):
    """Helper: publish a progress event to the scan's WebSocket topic."""
    payload = {"stage": stage, "message": message, "progress": progress, "scan_id": scan_id}
    payload.update(extra)
    await bus.publish(f"scan:{scan_id}", payload)


async def run_full_scan(scan_id: str):
    """Background task that orchestrates the full scan pipeline."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        try:
            scan.status = ScanStatus.PROCESSING
            await db.commit()
            await _emit(scan_id, "started", "Pipeline initialized", 5)
            logger.info(f"[SCAN {scan_id}] Starting pipeline...")

            # ── Stage 1: satellite imagery ───────────────────────────
            await _emit(scan_id, "fetch", "Fetching Sentinel-2 imagery...", 15)
            logger.info(f"[SCAN {scan_id}] Fetching satellite data...")
            image_paths = await _fetch_satellite_images(scan)
            await _emit(scan_id, "fetch", f"{len(image_paths)} images downloaded", 35,
                        images=len(image_paths))

            # ── Stage 2: SAR (Sentinel-1) if requested ───────────────
            sar_anomalies = []
            if scan.scan_type and "sar" in str(scan.scan_type).lower():
                await _emit(scan_id, "sar", "Fetching Sentinel-1 SAR data...", 45)
                sar_anomalies = await _run_sar_analysis(scan)
                await _emit(scan_id, "sar", f"SAR returned {len(sar_anomalies)} signals", 55)

            # ── Stage 3: AI detection ─────────────────────────────────
            await _emit(scan_id, "ai_detect", "Running YOLO + segmentation...", 60)
            logger.info(f"[SCAN {scan_id}] Running AI anomaly detection...")
            ai_anomalies = await _run_ai_detection(scan, image_paths)
            await _emit(scan_id, "ai_detect", f"AI found {len(ai_anomalies)} objects", 75,
                        ai_count=len(ai_anomalies))

            # ── Stage 4: temporal change ──────────────────────────────
            temporal_anomalies = []
            if scan.date_start and scan.date_end:
                await _emit(scan_id, "temporal", "Comparing before/after imagery...", 82)
                logger.info(f"[SCAN {scan_id}] Running temporal analysis...")
                temporal_anomalies = await _run_temporal_analysis(scan)
                await _emit(scan_id, "temporal",
                            f"{len(temporal_anomalies)} change zones detected", 92,
                            temporal_count=len(temporal_anomalies))

            anomalies_data = ai_anomalies + temporal_anomalies + sar_anomalies

            # ── Stage 5: persist ──────────────────────────────────────
            for a_data in anomalies_data:
                anomaly = Anomaly(
                    scan_id=scan_id,
                    anomaly_type=a_data.get("type", "unknown"),
                    severity=a_data.get("severity", "medium"),
                    latitude=a_data.get("latitude", scan.center_lat or 0),
                    longitude=a_data.get("longitude", scan.center_lon or 0),
                    confidence=a_data.get("confidence", 0.0),
                    description=a_data.get("description"),
                    ai_interpretation=a_data.get("interpretation"),
                    detected_by=a_data.get("detected_by", "system"),
                    object_class=a_data.get("class"),
                )
                db.add(anomaly)

            scan.anomaly_count = len(anomalies_data)
            scan.confidence_score = (
                sum(a.get("confidence", 0) for a in anomalies_data) / max(len(anomalies_data), 1)
            )
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now(timezone.utc)
            scan.meta = {
                "images_downloaded": len(image_paths),
                "ai_detections": len(ai_anomalies),
                "temporal_changes": len(temporal_anomalies),
                "sar_signals": len(sar_anomalies),
                "processing_pipeline": ["satellite_fetch", "ai_detection", "temporal_analysis", "sar"],
            }
            await db.commit()
            await _emit(scan_id, "complete",
                        f"Scan complete — {scan.anomaly_count} anomalies", 100,
                        anomaly_count=scan.anomaly_count,
                        confidence_score=scan.confidence_score)
            logger.info(f"[SCAN {scan_id}] Completed. {scan.anomaly_count} anomalies found.")

        except Exception as e:
            logger.error(f"[SCAN {scan_id}] Failed: {e}", exc_info=True)
            scan.status = ScanStatus.FAILED
            await db.commit()
            await _emit(scan_id, "error", f"Pipeline failed: {e}", 100, error=str(e))


async def _fetch_satellite_images(scan: Scan) -> list:
    """Fetch satellite imagery via Google Earth Engine."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "geospatial"))
        from earth_engine import EarthEngineClient

        client = EarthEngineClient()
        paths = client.download_region(
            lat_min=scan.lat_min,
            lat_max=scan.lat_max,
            lon_min=scan.lon_min,
            lon_max=scan.lon_max,
            date_start=scan.date_start or "2023-01-01",
            date_end=scan.date_end or "2024-01-01",
            scan_id=scan.id,
        )
        return paths
    except Exception as e:
        logger.warning(f"GEE fetch failed ({e}), using mock data")
        return []


async def _run_ai_detection(scan: Scan, image_paths: list) -> list:
    """Run YOLOv8 and anomaly detection on downloaded images."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "ai_models"))
        try:
            from satellite_detector import SatelliteAwareDetector
            detector = SatelliteAwareDetector()
        except Exception:
            from detector import SatelliteDetector
            detector = SatelliteDetector()
        results = []
        for img_path in image_paths:
            detections = detector.detect(img_path)
            results.extend(detections)
        return results
    except Exception as e:
        logger.warning(f"AI detection failed ({e}), returning empty results")
        return []


async def _run_temporal_analysis(scan: Scan) -> list:
    """Compare before/after images for change detection."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "geospatial"))
        from temporal import TemporalAnalyzer

        analyzer = TemporalAnalyzer()
        changes = analyzer.analyze(
            scan_id=scan.id,
            lat_min=scan.lat_min, lat_max=scan.lat_max,
            lon_min=scan.lon_min, lon_max=scan.lon_max,
            date_start=scan.date_start,
            date_end=scan.date_end,
        )
        return changes
    except Exception as e:
        logger.warning(f"Temporal analysis failed ({e})")
        return []


async def _run_sar_analysis(scan: Scan) -> list:
    """Run Sentinel-1 SAR change detection (cloud-penetrating radar)."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "geospatial"))
        from sar import SARAnalyzer

        analyzer = SARAnalyzer()
        results = analyzer.detect_changes(
            scan_id=scan.id,
            lat_min=scan.lat_min, lat_max=scan.lat_max,
            lon_min=scan.lon_min, lon_max=scan.lon_max,
            date_start=scan.date_start or "2023-01-01",
            date_end=scan.date_end or "2024-01-01",
        )
        return results
    except Exception as e:
        logger.warning(f"SAR analysis failed ({e})")
        return []
