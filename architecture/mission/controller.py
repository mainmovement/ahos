"""M14 mission controller. It schedules phases. It does not trade or promote."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MissionController:
    phase: str = "IDLE"
    live: bool = False

    def start(self) -> str:
        if self.phase == "HALT":
            return "HALT"
        self.phase = "RUNNING"
        self.live = False
        return self.phase

    def pause(self) -> str:
        if self.phase == "RUNNING":
            self.phase = "PAUSED"
        return self.phase

    def halt(self) -> str:
        self.phase = "HALT"
        self.live = False
        return self.phase

    def promote(self) -> bool:
        return False

    def enable_live(self) -> bool:
        self.live = False
        return False
