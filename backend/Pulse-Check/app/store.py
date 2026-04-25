import asyncio
from datetime import datetime, timezone
from typing import Optional


# Possible states a monitor can be in
STATUS_ACTIVE = "active"
STATUS_DOWN   = "down"
STATUS_PAUSED = "paused"


# Holds everything we know about one monitored device
class Monitor:
    def __init__(self, id: str, timeout: int, alert_email: str):
        self.id          = id
        self.timeout     = timeout           # how many seconds before alert fires
        self.alert_email = alert_email
        self.status      = STATUS_ACTIVE
        self.task: Optional[asyncio.Task] = None


class MonitorStore:
    # _monitors is a dictionary: device id -> Monitor object

    def __init__(self):
        self._monitors: dict[str, Monitor] = {}

    def get(self, monitor_id: str) -> Optional[Monitor]:
        return self._monitors.get(monitor_id)

    def add(self, monitor: Monitor):
        self._monitors[monitor.id] = monitor

    def remove(self, monitor_id: str):
        self._monitors.pop(monitor_id, None)

    def all(self) -> list[Monitor]:
        return list(self._monitors.values())


# One shared store used by the whole app
monitor_store = MonitorStore()


async def run_countdown(monitor: Monitor):
    await asyncio.sleep(monitor.timeout)

    # If we get here, no heartbeat came in time, fire the alert
    monitor.status = STATUS_DOWN
    alert = {
        "ALERT": f"Device {monitor.id} is down!",
        "time": datetime.now(timezone.utc).isoformat()
    }
    print(alert)


def start_timer(monitor: Monitor):
    # Cancel any running countdown and start a fresh one
    if monitor.task and not monitor.task.done():
        monitor.task.cancel()
    monitor.task = asyncio.create_task(run_countdown(monitor))


def stop_timer(monitor: Monitor):
    # Cancel the countdown without firing the alert (used when pausing)
    if monitor.task and not monitor.task.done():
        monitor.task.cancel()
        monitor.task = None
