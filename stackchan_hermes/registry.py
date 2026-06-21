"""App discovery + the runner that applies a RenderResult to a client."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Optional

from stackchan_hermes import apps as _apps_pkg
from stackchan_hermes.app import RenderResult, StackchanApp
from stackchan_hermes.client import StackchanLike


def discover_apps() -> dict[str, type[StackchanApp]]:
    """Find every app exported as ``APP`` by a module in ``stackchan_hermes.apps``."""
    found: dict[str, type[StackchanApp]] = {}
    for mod in pkgutil.iter_modules(_apps_pkg.__path__):
        module = importlib.import_module(f"{_apps_pkg.__name__}.{mod.name}")
        app_cls = getattr(module, "APP", None)
        if isinstance(app_cls, type) and issubclass(app_cls, StackchanApp):
            found[app_cls.name] = app_cls
    return dict(sorted(found.items()))


def get_app(name: str) -> type[StackchanApp]:
    apps = discover_apps()
    if name not in apps:
        available = ", ".join(apps) or "(none)"
        raise KeyError(f"unknown app {name!r}; available: {available}")
    return apps[name]


async def run_render(result: RenderResult, client: StackchanLike) -> None:
    """Apply a render result to a (real or dry-run) client, in a sane order."""
    await client.set_avatar(result.face)
    if result.head is not None:
        yaw, pitch = result.head
        await client.move_head(yaw, pitch)
    if result.speech:
        await client.say(result.speech)
