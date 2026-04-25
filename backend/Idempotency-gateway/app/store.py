import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

# Keys expire after 24 hours
KEY_TTL_HOURS = 24


# Holds the saved result for one payment
class StoredRecord:
    def __init__(self, request_hash: str, response_body: dict, status_code: int):
        self.request_hash = request_hash 
        self.response_body = response_body
        self.status_code = status_code
        self.created_at = datetime.now(timezone.utc)
        self.is_processing = False


class IdempotencyStore:

    def __init__(self):
        self._store: dict[str, StoredRecord] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    @staticmethod
    def hash_request(body: dict) -> str:
        serialized = json.dumps(body, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _is_expired(self, record: StoredRecord) -> bool:
        expiry_time = record.created_at + timedelta(hours=KEY_TTL_HOURS)
        return datetime.now(timezone.utc) > expiry_time

    def get(self, key: str) -> Optional[StoredRecord]:
        record = self._store.get(key)
        if record is None:
            return None

        # If the key is older than 24 hours, delete it and treat it as new
        if self._is_expired(record):
            del self._store[key]
            del self._locks[key]
            return None

        return record

    def save(self, key: str, request_hash: str, response_body: dict, status_code: int):
        record = self._store.get(key)
        if record:
            # Update the record that was marked as processing
            record.request_hash = request_hash
            record.response_body = response_body
            record.status_code = status_code
            record.is_processing = False
        else:
            self._store[key] = StoredRecord(request_hash, response_body, status_code)

    def mark_processing(self, key: str, request_hash: str):
        # Reserve the key before the 2-second delay starts
        # so any duplicate that comes in knows to wait
        self._store[key] = StoredRecord(request_hash, {}, 0)
        self._store[key].is_processing = True

    async def acquire_lock(self, key: str):
        lock = self._get_lock(key)
        await lock.acquire()

    def release_lock(self, key: str):
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()


idempotency_store = IdempotencyStore()
