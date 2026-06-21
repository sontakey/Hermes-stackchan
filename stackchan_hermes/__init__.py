"""stackchan-hermes: drive an M5Stack StackChan robot from Hermes.

A small, extensible app framework that surfaces live information on a StackChan
desktop robot (speech via TTS, avatar expressions, head motion) by talking to the
community ``kisaragi-mochi/stackchan-mcp`` gateway over stdio MCP.
"""

from stackchan_hermes.app import RenderResult, StackchanApp
from stackchan_hermes.client import DryRunClient, StackchanClient
from stackchan_hermes.registry import discover_apps, get_app

__version__ = "0.1.0"

__all__ = [
    "RenderResult",
    "StackchanApp",
    "StackchanClient",
    "DryRunClient",
    "discover_apps",
    "get_app",
    "__version__",
]
