"""
WebSocket endpoints for real-time scan progress.

Frontend usage:
    const ws = new WebSocket(`ws://localhost:8000/ws/scans/${scanId}?token=${jwt}`)
    ws.onmessage = (e) => { const evt = JSON.parse(e.data); /* update UI */ }
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.services.event_bus import get_bus
from app.utils.auth import decode_token
from app.utils.logger import logger

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/scans/{scan_id}")
async def scan_progress(
    websocket: WebSocket,
    scan_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """Stream live progress events for a scan.

    Event shape:
        {
            "ts": ISO8601,
            "topic": "scan:<id>",
            "stage": "fetch" | "ai_detect" | "temporal" | "complete" | "error",
            "message": str,
            "progress": 0-100,
            "data": optional payload
        }
    """
    try:
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    topic = f"scan:{scan_id}"
    logger.info(f"[WS] Client subscribed to {topic}")

    bus = get_bus()
    try:
        await websocket.send_json({
            "stage": "connected",
            "message": f"Subscribed to {topic}",
            "scan_id": scan_id,
            "progress": 0,
        })
        async for event in bus.subscribe(topic):
            await websocket.send_json(event)
            if event.get("stage") in ("complete", "error"):
                break
    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected from {topic}")
    except Exception as e:
        logger.error(f"[WS] Error in {topic}: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
