"""Command-line entrypoint: ``stackchan-hermes list|run``."""

from __future__ import annotations

import argparse
import asyncio
import sys

from stackchan_hermes import __version__
from stackchan_hermes.client import DryRunClient, StackchanClient
from stackchan_hermes.registry import discover_apps, get_app, run_render


def _cmd_list(_args: argparse.Namespace) -> int:
    apps = discover_apps()
    if not apps:
        print("No apps found.")
        return 0
    width = max(len(n) for n in apps)
    print("Available StackChan apps:\n")
    for name, cls in apps.items():
        print(f"  {name.ljust(width)}  {cls.description}")
    print(f"\nRun one with:  stackchan-hermes run <app> [--dry-run]")
    return 0


async def _run_app(name: str, dry_run: bool) -> int:
    app_cls = get_app(name)
    app = app_cls()
    result = app.render()

    print(f"== {app.name} ==")
    for line in result.screen_lines:
        print(f"  {line}")
    print(f"  face: {result.face}")
    print(f"  speech: {result.speech!r}")
    if result.head:
        print(f"  head: yaw={result.head[0]} pitch={result.head[1]}")
    print()

    if dry_run:
        print("Applying to dry-run client:")
        await run_render(result, DryRunClient())
        return 0

    print("Connecting to stackchan-mcp gateway over stdio...")
    try:
        async with StackchanClient.connect() as client:
            await run_render(result, client)
    except Exception as exc:  # noqa: BLE001 - surface a clean message + fallback
        print(f"!! Could not drive the live gateway: {exc}", file=sys.stderr)
        print("   Re-run with --dry-run to preview without hardware.",
              file=sys.stderr)
        return 1
    print("Done.")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    return asyncio.run(_run_app(args.app, args.dry_run))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackchan-hermes",
        description="Drive an M5Stack StackChan robot from Hermes.",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List available display apps.")
    p_list.set_defaults(func=_cmd_list)

    p_run = sub.add_parser("run", help="Run a display app.")
    p_run.add_argument("app", help="App name (see `stackchan-hermes list`).")
    p_run.add_argument("--dry-run", action="store_true",
                       help="Print what would be spoken/shown; no gateway.")
    p_run.set_defaults(func=_cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
