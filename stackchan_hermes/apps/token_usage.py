"""token_usage app — speak/show how many tokens have been used.

Data schema (JSON)
------------------
::

    {
      "used": 1240000,           # tokens used in the window (int, required)
      "limit": 2000000,          # optional budget for the window (int)
      "window": "today"          # optional human label (str), default "today"
    }

Source resolution (see stackchan_hermes.sources.load_data):
  1. ``STACKCHAN_TOKEN_USAGE`` env var -> JSON file path *or* inline JSON
  2. built-in demo payload (1.24M / 2M today)

Expression threshold (fraction of limit used):
  < 0.5 -> happy    0.5..0.85 -> idle    > 0.85 -> sad (concerned)
If no ``limit`` is given, the face is always ``idle``.
"""

from __future__ import annotations

from typing import Optional

from stackchan_hermes.app import RenderResult, StackchanApp
from stackchan_hermes.sources import load_data

ENV_VAR = "STACKCHAN_TOKEN_USAGE"
DEMO = {"used": 1_240_000, "limit": 2_000_000, "window": "today"}


def _humanize(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} million"
    if n >= 1_000:
        return f"{n / 1_000:.0f} thousand"
    return str(n)


class TokenUsageApp(StackchanApp):
    name = "token_usage"
    description = "Speak and show how many tokens have been used in a window."

    def render(self) -> RenderResult:
        data, source = load_data(
            path=self.config.get("path"),
            env_var=ENV_VAR,
            demo=DEMO,
        )
        used = int(data["used"])
        limit: Optional[int] = data.get("limit")
        window = data.get("window", "today")

        if limit:
            frac = used / limit
            face = "happy" if frac < 0.5 else "sad" if frac > 0.85 else "idle"
            pct = f"{frac * 100:.0f}%"
            speech = (
                f"You've used {_humanize(used)} tokens {window}. "
                f"That's {pct} of your budget."
            )
            screen = [
                f"Tokens {window}: {_humanize(used)} / {_humanize(limit)} ({pct})",
                f"source: {source}",
            ]
        else:
            face = "idle"
            speech = f"You've used {_humanize(used)} tokens {window}."
            screen = [f"Tokens {window}: {_humanize(used)}", f"source: {source}"]

        return RenderResult(speech=speech, face=face, screen_lines=screen)


APP = TokenUsageApp
