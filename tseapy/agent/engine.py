"""Background runner for the autonomous insights agent.

The :class:`InsightsEngine` runs the deterministic analyzers in a daemon thread
as soon as a dataset is loaded — the user never has to ask. It exposes a small,
thread-safe snapshot of its status and the ranked findings so the frontend can
poll progress and lazily fetch figures.

Because tseapy serves a single in-process dataset (Flask ``SimpleCache``), a
single module-level engine instance mirrors that model. See :data:`engine`.
"""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass, field

import pandas as pd

from tseapy.agent.analyzers import ANALYZERS
from tseapy.agent.findings import Finding

STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"


@dataclass
class _State:
    status: str = STATUS_IDLE
    completed: int = 0
    total: int = 0
    current: str = ""
    findings: list[Finding] = field(default_factory=list)
    error: str = ""
    signature: str | None = None


class InsightsEngine:
    """Runs analyzers in the background and stores ranked findings."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = _State()
        self._data: pd.DataFrame | None = None
        self._thread: threading.Thread | None = None

    @staticmethod
    def _signature(data: pd.DataFrame) -> str:
        """Cheap fingerprint so re-loading the same dataset is a no-op."""
        cols = ",".join(map(str, data.columns))
        return f"{data.shape[0]}x{data.shape[1]}:{cols}:{int(pd.util.hash_pandas_object(data.index).sum())}"

    def start(self, data: pd.DataFrame, *, force: bool = False, background: bool = True) -> None:
        """Launch an analysis run over ``data``.

        Re-running on an identical dataset is skipped unless ``force`` is set.
        Set ``background=False`` to run synchronously (used in tests).
        """
        signature = self._signature(data)
        with self._lock:
            already_running = self._state.status == STATUS_RUNNING
            same_dataset = self._state.signature == signature and self._state.status == STATUS_DONE
            if not force and (already_running or same_dataset):
                return
            self._data = data.copy()
            self._state = _State(
                status=STATUS_RUNNING,
                total=len(ANALYZERS),
                current=ANALYZERS[0][0] if ANALYZERS else "",
                signature=signature,
            )

        if background:
            thread = threading.Thread(target=self._run, args=(data.copy(),), daemon=True)
            self._thread = thread
            thread.start()
        else:
            self._run(data.copy())

    def _run(self, data: pd.DataFrame) -> None:
        try:
            for index, (label, analyzer) in enumerate(ANALYZERS):
                with self._lock:
                    self._state.current = label
                    self._state.completed = index
                try:
                    results = analyzer(data)
                except Exception:  # noqa: BLE001 - one analyzer must not sink the run
                    traceback.print_exc()
                    results = []
                with self._lock:
                    self._state.findings.extend(results)
                    self._state.findings.sort(key=lambda f: f.score, reverse=True)
            with self._lock:
                self._state.completed = len(ANALYZERS)
                self._state.current = ""
                self._state.status = STATUS_DONE
        except Exception as exc:  # noqa: BLE001 - surface unexpected failures to the UI
            traceback.print_exc()
            with self._lock:
                self._state.status = STATUS_ERROR
                self._state.error = str(exc)

    def status(self) -> dict:
        """Return a JSON-friendly snapshot of progress and finding counts."""
        with self._lock:
            state = self._state
            return {
                "status": state.status,
                "completed": state.completed,
                "total": state.total,
                "current": state.current,
                "finding_count": len(state.findings),
            }

    def findings(self) -> list[Finding]:
        """Return the current findings, ranked by descending score."""
        with self._lock:
            return list(self._state.findings)

    def get_finding(self, finding_id: str) -> Finding | None:
        with self._lock:
            for finding in self._state.findings:
                if finding.id == finding_id:
                    return finding
        return None

    def data(self) -> pd.DataFrame | None:
        """Return the dataset the current findings were computed from."""
        with self._lock:
            return self._data

    def reset(self) -> None:
        with self._lock:
            self._state = _State()
            self._data = None


# Module-level singleton mirroring tseapy's single-dataset model.
engine = InsightsEngine()
