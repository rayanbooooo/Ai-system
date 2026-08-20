"""Pluggable interface for optionally drawing the AZAREL step-stair lines,
pivot dots, and number tags on a live chart. See docs/OPEN_QUESTIONS.md
("Phase 5: live chart annotation via CDP") before implementing a real,
connection-backed version of this.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from scanner.structure.models import Setup


class ChartAnnotator(ABC):
    @abstractmethod
    def draw_setup(self, setup: Setup) -> None:
        """Draw the step-stair segments, pivot dots, and "1"-"6" number
        tags for a completed Setup, per the AZAREL visual rules in
        docs/AZAREL_STRATEGY.md. Implementations must never erase prior
        history - only add.
        """
        raise NotImplementedError
