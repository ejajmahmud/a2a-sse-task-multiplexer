"""Core A2A Server-Sent Events (SSE) task stream multiplexer and sequence reorderer."""
from typing import Any, Dict, List


class A2ASSEMultiplexer:
    """Ingests, deduplicates, and orders concurrent A2A task SSE frames."""

    TERMINAL_STATES = {"completed", "failed", "canceled"}

    def __init__(self, expected_tasks: List[str] = None):
        self.expected_tasks = set(expected_tasks or [])
        self._buffers: Dict[str, Dict[int, Dict[str, Any]]] = {}
        self._next_seq: Dict[str, int] = {}
        self._terminal: Dict[str, str] = {}

    def ingest(self, task_id: str, seq: int, state: str, payload: Dict[str, Any] = None) -> bool:
        if seq < 1:
            raise ValueError("Sequence numbers must be >= 1")
        buf = self._buffers.setdefault(task_id, {})
        next_expected = self._next_seq.get(task_id, 1)
        if seq < next_expected or seq in buf:
            return False

        buf[seq] = {"task_id": task_id, "seq": seq, "state": state, "payload": dict(payload or {})}
        return True

    def drain_ordered(self, task_id: str) -> List[Dict[str, Any]]:
        buf = self._buffers.get(task_id, {})
        cursor = self._next_seq.get(task_id, 1)
        drained: List[Dict[str, Any]] = []
        while cursor in buf:
            evt = buf.pop(cursor)
            drained.append(evt)
            if evt["state"] in self.TERMINAL_STATES:
                self._terminal[task_id] = evt["state"]
            cursor += 1
        self._next_seq[task_id] = cursor
        return drained

    def drain_all(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for tid in sorted(self._buffers.keys()):
            out.extend(self.drain_ordered(tid))
        return out

    def status_summary(self) -> Dict[str, Any]:
        tasks = self.expected_tasks | set(self._buffers.keys()) | set(self._terminal.keys())
        completed = sum(1 for t in tasks if self._terminal.get(t) == "completed")
        failed = sum(1 for t in tasks if self._terminal.get(t) in ("failed", "canceled"))
        return {
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "all_done": len(tasks) > 0 and (completed + failed) == len(tasks),
        }
