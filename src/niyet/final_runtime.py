from __future__ import annotations

from pathlib import Path

from .runtime import NiyetRuntime


class FinalDemoRuntime(NiyetRuntime):
    """NIYET runtime for the integrated final prototype.

    The reviewed v1 responder profile set stays frozen for the published benchmark.
    The final prototype uses a separately versioned synthetic profile set so product
    iteration cannot silently change previously reported retrieval/allocation metrics.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        super().__init__(data_dir)
        self.responders = self._load_responders(
            self.data_dir / "responder_profiles_final_v2.json"
        )
        self.responder_by_id = {
            item.responder.id: item for item in self.responders
        }
