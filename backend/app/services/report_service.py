import json
from pathlib import Path
from datetime import datetime, timezone
from app.database import AsyncSessionLocal
from app.models.report import Report
from app.models.scan import Scan
from app.models.anomaly import Anomaly
from app.utils.logger import logger
from app.services.ai_service import get_ai_service

REPORTS_DIR = Path("./reports")
REPORTS_DIR.mkdir(exist_ok=True)


async def generate_report(report_id: str):
    """Background task to generate PDF and JSON exports."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return

        scan_result = await db.execute(select(Scan).where(Scan.id == report.scan_id))
        scan = scan_result.scalar_one_or_none()

        anomalies_result = await db.execute(
            select(Anomaly).where(Anomaly.scan_id == report.scan_id)
        )
        anomalies = anomalies_result.scalars().all()

        try:
            # Build threat level
            critical = sum(1 for a in anomalies if a.severity == "critical")
            high = sum(1 for a in anomalies if a.severity == "high")

            if critical > 0:
                threat_level = "critical"
            elif high > 2:
                threat_level = "high"
            elif len(anomalies) > 5:
                threat_level = "medium"
            else:
                threat_level = "low"

            # Build analysis — try AI first, fall back to template
            full_analysis = None
            recommendations = None
            headline = None

            ai = get_ai_service()
            if ai.is_configured and scan is not None:
                try:
                    ai_result = await ai.interpret_scan(scan, list(anomalies), threat_level)
                    if ai_result:
                        full_analysis = ai_result.get("analysis")
                        recommendations = ai_result.get("recommendations")
                        headline = ai_result.get("headline")
                        logger.info(f"[REPORT {report_id}] AI interpretation produced.")
                except Exception as e:
                    logger.warning(f"[REPORT {report_id}] AI interpretation failed: {e}")

            if not full_analysis:
                full_analysis = _build_analysis_text(scan, anomalies, threat_level)
            if not recommendations:
                recommendations = _build_recommendations(anomalies, threat_level)

            anomaly_summary = {
                "total": len(anomalies),
                "by_severity": {
                    "critical": critical,
                    "high": high,
                    "medium": sum(1 for a in anomalies if a.severity == "medium"),
                    "low": sum(1 for a in anomalies if a.severity == "low"),
                },
                "by_type": {},
            }
            for a in anomalies:
                anomaly_summary["by_type"][a.anomaly_type] = (
                    anomaly_summary["by_type"].get(a.anomaly_type, 0) + 1
                )

            # Export JSON
            json_path = REPORTS_DIR / f"{report_id}.json"
            export_data = {
                "report_id": report_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "scan": {
                    "id": scan.id if scan else None,
                    "name": scan.name if scan else None,
                    "bounds": {
                        "lat_min": scan.lat_min, "lat_max": scan.lat_max,
                        "lon_min": scan.lon_min, "lon_max": scan.lon_max,
                    } if scan else None,
                },
                "threat_level": threat_level,
                "headline": headline,
                "ai_generated": bool(headline),
                "full_analysis": full_analysis,
                "anomaly_summary": anomaly_summary,
                "recommendations": recommendations,
                "anomalies": [
                    {
                        "id": a.id,
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "lat": a.latitude,
                        "lon": a.longitude,
                        "confidence": a.confidence,
                        "description": a.description,
                    }
                    for a in anomalies
                ],
            }
            json_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")

            # Generate PDF
            pdf_path = _generate_pdf(report_id, export_data)

            report.threat_level = threat_level
            report.full_analysis = full_analysis
            report.recommendations = recommendations
            report.anomaly_summary = anomaly_summary
            report.json_path = str(json_path)
            report.pdf_path = str(pdf_path) if pdf_path else None
            await db.commit()
            logger.info(f"[REPORT {report_id}] Generated successfully.")

        except Exception as e:
            logger.error(f"[REPORT {report_id}] Failed: {e}", exc_info=True)


def _build_analysis_text(scan, anomalies, threat_level: str) -> str:
    if not scan:
        return "Analysis unavailable."
    return (
        f"NEXUS ATLAS — Geospatial Intelligence Report\n"
        f"Region: {scan.name}\n"
        f"Coordinates: [{scan.lat_min:.4f}, {scan.lon_min:.4f}] to [{scan.lat_max:.4f}, {scan.lon_max:.4f}]\n"
        f"Threat Assessment: {threat_level.upper()}\n\n"
        f"A total of {len(anomalies)} anomalies were detected in this region. "
        f"Advanced AI analysis using YOLOv8 object detection and temporal change analysis "
        f"was applied to multi-spectral satellite imagery. "
        f"Patterns indicate {'significant activity requiring immediate attention' if threat_level in ('critical', 'high') else 'moderate activity for continued monitoring'}."
    )


def _build_recommendations(anomalies, threat_level: str) -> list:
    recs = []
    if threat_level == "critical":
        recs.append("IMMEDIATE: Deploy rapid-response geospatial monitoring to this region.")
        recs.append("Escalate findings to relevant operational command.")
    if any(a.anomaly_type == "structure" for a in anomalies):
        recs.append("Schedule high-resolution re-scan to confirm structural detections.")
    if any(a.anomaly_type == "vegetation" for a in anomalies):
        recs.append("Cross-reference NDVI data with historical baselines.")
    recs.append("Archive imagery for long-term trend analysis.")
    return recs


def _generate_pdf(report_id: str, data: dict) -> Path | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

        pdf_path = REPORTS_DIR / f"{report_id}.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("NEXUS ATLAS — INTELLIGENCE REPORT", styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"Report ID: {report_id}", styles["Normal"]))
        story.append(Paragraph(f"Generated: {data['generated_at']}", styles["Normal"]))
        story.append(Paragraph(f"Threat Level: {data['threat_level'].upper()}", styles["Heading2"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Executive Analysis", styles["Heading2"]))
        story.append(Paragraph(data.get("full_analysis", ""), styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

        if data.get("recommendations"):
            story.append(Paragraph("Recommendations", styles["Heading2"]))
            for rec in data["recommendations"]:
                story.append(Paragraph(f"• {rec}", styles["Normal"]))

        story.append(Spacer(1, 0.5 * cm))
        summary = data.get("anomaly_summary", {})
        story.append(Paragraph(f"Total Anomalies Detected: {summary.get('total', 0)}", styles["Heading3"]))

        doc.build(story)
        return pdf_path
    except ImportError:
        logger.warning("reportlab not installed — skipping PDF generation")
        return None
