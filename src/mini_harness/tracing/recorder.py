"""Human-readable JSONL recording with actual monotonic latency data."""

from pathlib import Path
from typing import Any

from mini_harness.session.store import SessionStore
from mini_harness.tracing.events import TraceEvent


class TraceRecorder:
    def __init__(self, path: Path) -> None:
        self.store = SessionStore(path)

    def record(
        self, event: str, turn_id: str, iteration: int, model: str, layer: str, **data: Any
    ) -> None:
        packet = TraceEvent(
            turn_id=turn_id, iteration=iteration, model=model, layer=layer, data=data
        )
        self.store.append(event, packet.model_dump())
