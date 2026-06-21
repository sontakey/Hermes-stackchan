"""Clients that drive the StackChan robot.

Transport decision
------------------
The ``kisaragi-mochi/stackchan-mcp`` gateway is a **stdio MCP server** — verified
against the upstream source (``gateway/AGENTS.md``: "The gateway runs as a stdio
MCP server"; ``gateway/stackchan_mcp/stdio_server.py`` registers the tools). The
gateway, in turn, bridges to the ESP32 over WebSocket. So the correct, non-
fabricated way to call its tools is to spawn the gateway's console script
(``stackchan-mcp``) and speak MCP over stdio using the official ``mcp`` Python
SDK — exactly the way Hermes's own native MCP client connects to it.

``StackchanClient`` wraps the four primary tools (``say``, ``set_avatar``,
``move_head``, ``take_photo``) as clean async methods, enforcing the M5Stack
tilt-servo safety range (pitch 5..85, yaw -90..90) at the boundary.

``DryRunClient`` implements the same surface but only records/prints actions, so
apps run with no gateway and no hardware.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional, Protocol

# M5Stack-recommended tilt-servo operating range. Driving the pitch servo outside
# this band risks the head binding against the chassis — clamp it, always.
PITCH_MIN, PITCH_MAX = 5, 85
YAW_MIN, YAW_MAX = -90, 90


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


class StackchanLike(Protocol):
    """The minimal device surface apps and the runner rely on."""

    async def say(self, text: str, *, voice: str = "voicevox",
                  speaker_id: Optional[int] = None) -> Any: ...
    async def set_avatar(self, face: str) -> Any: ...
    async def move_head(self, yaw: int, pitch: int,
                        speed: Optional[int] = None) -> Any: ...
    async def take_photo(self, question: str) -> Any: ...


@dataclass
class GatewayConfig:
    """How to launch / reach the stackchan-mcp gateway over stdio.

    Defaults match the verified local install. ``command`` should point at the
    gateway's ``stackchan-mcp`` console script (zero subcommand = stdio server).
    """

    command: str = os.environ.get(
        "STACKCHAN_GATEWAY_CMD",
        "/Users/anton/stackchan-mcp/.venv/bin/stackchan-mcp",
    )
    args: tuple[str, ...] = ()
    env: Optional[dict[str, str]] = None

    def merged_env(self) -> dict[str, str]:
        env = dict(os.environ)
        # Token + vision host the gateway needs; overridable from the real env.
        env.setdefault("STACKCHAN_TOKEN",
                       os.environ.get("STACKCHAN_TOKEN", "stackchan-dev-token"))
        if self.env:
            env.update(self.env)
        return env


class StackchanClient:
    """Async client that spawns the gateway and calls its MCP tools over stdio.

    Use as an async context manager::

        async with StackchanClient.connect() as sc:
            await sc.set_avatar("happy")
            await sc.say("hello")
    """

    def __init__(self, session: "Any") -> None:
        self._session = session

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, config: Optional[GatewayConfig] = None
    ) -> AsyncIterator["StackchanClient"]:
        # Imported lazily so the package (and dry-run mode) works without the
        # mcp SDK installed.
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        cfg = config or GatewayConfig()
        params = StdioServerParameters(
            command=cfg.command,
            args=list(cfg.args),
            env=cfg.merged_env(),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield cls(session)

    async def _call(self, tool: str, arguments: dict[str, Any]) -> Any:
        result = await self._session.call_tool(tool, arguments)
        if getattr(result, "isError", False):
            raise RuntimeError(f"gateway tool {tool!r} failed: {result.content}")
        return result

    async def say(self, text: str, *, voice: str = "voicevox",
                  speaker_id: Optional[int] = None) -> Any:
        if not text:
            raise ValueError("say(text=...) must be non-empty")
        args: dict[str, Any] = {"text": text, "voice": voice}
        if speaker_id is not None:
            args["speaker_id"] = speaker_id
        return await self._call("say", args)

    async def set_avatar(self, face: str) -> Any:
        return await self._call("set_avatar", {"face": face})

    async def move_head(self, yaw: int, pitch: int,
                        speed: Optional[int] = None) -> Any:
        args: dict[str, Any] = {
            "yaw": clamp(int(yaw), YAW_MIN, YAW_MAX),
            "pitch": clamp(int(pitch), PITCH_MIN, PITCH_MAX),
        }
        if speed is not None:
            args["speed"] = speed
        return await self._call("move_head", args)

    async def take_photo(self, question: str) -> Any:
        return await self._call("take_photo", {"question": question})


class DryRunClient:
    """Same surface as :class:`StackchanClient`, but prints instead of acting.

    Lets every app run with no gateway and no physical device.
    """

    def __init__(self, *, echo: bool = True) -> None:
        self.echo = echo
        self.actions: list[tuple[str, dict[str, Any]]] = []

    def _record(self, tool: str, args: dict[str, Any]) -> None:
        self.actions.append((tool, args))
        if self.echo:
            pretty = ", ".join(f"{k}={v!r}" for k, v in args.items())
            print(f"  [dry-run] {tool}({pretty})")

    async def say(self, text: str, *, voice: str = "voicevox",
                  speaker_id: Optional[int] = None) -> None:
        self._record("say", {"text": text, "voice": voice})

    async def set_avatar(self, face: str) -> None:
        self._record("set_avatar", {"face": face})

    async def move_head(self, yaw: int, pitch: int,
                        speed: Optional[int] = None) -> None:
        self._record(
            "move_head",
            {"yaw": clamp(int(yaw), YAW_MIN, YAW_MAX),
             "pitch": clamp(int(pitch), PITCH_MIN, PITCH_MAX)},
        )

    async def take_photo(self, question: str) -> None:
        self._record("take_photo", {"question": question})
