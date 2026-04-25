from fastapi import APIRouter, HTTPException

from app.models import RegisterRequest, MonitorResponse
from app.store import (
    Monitor, monitor_store,
    start_timer, stop_timer,
    STATUS_ACTIVE, STATUS_PAUSED
)

router = APIRouter()


@router.post("/monitors", status_code=201)
async def register_monitor(body: RegisterRequest):
    # Don't allow registering the same device twice
    if monitor_store.get(body.id):
        raise HTTPException(status_code=409, detail=f"Monitor '{body.id}' already exists.")

    monitor = Monitor(id=body.id, timeout=body.timeout, alert_email=body.alert_email)
    monitor_store.add(monitor)
    start_timer(monitor)

    return MonitorResponse(
        id=monitor.id,
        status=monitor.status,
        timeout=monitor.timeout,
        alert_email=monitor.alert_email,
        message=f"Monitor registered. Countdown started for {monitor.timeout} seconds."
    )


@router.post("/monitors/{id}/heartbeat", status_code=200)
async def heartbeat(id: str):
    monitor = monitor_store.get(id)

    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{id}' not found.")

    # If the device was paused, a heartbeat wakes it back up
    monitor.status = STATUS_ACTIVE
    start_timer(monitor)

    return MonitorResponse(
        id=monitor.id,
        status=monitor.status,
        timeout=monitor.timeout,
        alert_email=monitor.alert_email,
        message="Heartbeat received. Timer reset."
    )


@router.post("/monitors/{id}/pause", status_code=200)
async def pause_monitor(id: str):
    monitor = monitor_store.get(id)

    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{id}' not found.")

    stop_timer(monitor)
    monitor.status = STATUS_PAUSED

    return MonitorResponse(
        id=monitor.id,
        status=monitor.status,
        timeout=monitor.timeout,
        alert_email=monitor.alert_email,
        message="Monitor paused. No alerts will fire until next heartbeat."
    )


# check the current status of any monitor
@router.get("/monitors/{id}", status_code=200)
async def get_monitor(id: str):
    monitor = monitor_store.get(id)

    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor '{id}' not found.")

    return MonitorResponse(
        id=monitor.id,
        status=monitor.status,
        timeout=monitor.timeout,
        alert_email=monitor.alert_email
    )


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "pulse-check"}
