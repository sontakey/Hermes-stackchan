"""Core app framework: the ``StackchanApp`` base class and ``RenderResult``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

# Avatar faces supported by the stackchan-mcp gateway's set_avatar tool.
FACES = ("idle", "happy", "thinking", "sad", "surprised", "embarrassed", "off")


@dataclass
class RenderResult:
    """What an app wants the robot to say and show.

    An app's :meth:`StackchanApp.render` returns one of these. The runner then
    applies it to the device (or prints it, in ``--dry-run`` mode). Keeping
    ``render`` pure — returning data instead of calling the client directly —
    makes apps trivial to test and to preview without hardware.
    """

    speech: str = ""
    """Text spoken via gateway-side TTS (the ``say`` tool)."""

    face: str = "idle"
    """Avatar expression (the ``set_avatar`` tool). One of :data:`FACES`."""

    screen_lines: list[str] = field(default_factory=list)
    """Short lines summarising the state (shown in dry-run; future on-screen)."""

    head: Optional[tuple[int, int]] = None
    """Optional ``(yaw, pitch)`` head pose. ``pitch`` is clamped to 5..85."""

    def __post_init__(self) -> None:
        if self.face not in FACES:
            raise ValueError(f"face must be one of {FACES}, got {self.face!r}")


class StackchanApp(ABC):
    """Base class for a StackChan display app.

    Subclass this, set :attr:`name`/:attr:`description`, and implement
    :meth:`render`. Register the app by exporting an ``APP`` symbol from a module
    under ``stackchan_hermes.apps`` (see the bundled starter apps).
    """

    #: Short, unique app id used on the CLI (e.g. ``token_usage``).
    name: str = ""
    #: One-line human description shown by ``stackchan-hermes list``.
    description: str = ""

    def __init__(self, config: Optional[Mapping[str, Any]] = None) -> None:
        self.config: dict[str, Any] = dict(config or {})

    @abstractmethod
    def render(self) -> RenderResult:
        """Produce the speech/face/screen payload for this run."""
        raise NotImplementedError
