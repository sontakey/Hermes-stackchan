"""task_status app — speak/show recently completed tasks.

Data schema (JSON)
------------------
::

    {
      "window": "today",         # optional human label (str), default "today"
      "tasks": [                 # required list
        {"title": "Shipped the landing page", "status": "done"},
        {"title": "Reviewed PR #42",          "status": "done"},
        {"title": "Drafting the changelog",   "status": "in_progress"}
      ]
    }

Only tasks with ``status == "done"`` are counted as completed. A task may be a
bare string, treated as a completed task title.

Source resolution (see stackchan_hermes.sources.load_data):
  1. ``STACKCHAN_TASK_STATUS`` env var -> JSON file path *or* inline JSON
  2. built-in demo payload

Expression: any completed -> happy; none completed -> thinking.
"""

from __future__ import annotations

from stackchan_hermes.app import RenderResult, StackchanApp
from stackchan_hermes.sources import load_data

ENV_VAR = "STACKCHAN_TASK_STATUS"
DEMO = {
    "window": "today",
    "tasks": [
        {"title": "Shipped the StackChan bridge", "status": "done"},
        {"title": "Reviewed the firmware PR", "status": "done"},
        {"title": "Wrote the README", "status": "done"},
        {"title": "Drafting the roadmap", "status": "in_progress"},
    ],
}


def _title(task: object) -> str:
    if isinstance(task, str):
        return task
    if isinstance(task, dict):
        return str(task.get("title", "untitled"))
    return str(task)


def _is_done(task: object) -> bool:
    if isinstance(task, str):
        return True
    return isinstance(task, dict) and task.get("status", "done") == "done"


class TaskStatusApp(StackchanApp):
    name = "task_status"
    description = "Speak and show recently completed tasks."

    def render(self) -> RenderResult:
        data, source = load_data(
            path=self.config.get("path"),
            env_var=ENV_VAR,
            demo=DEMO,
        )
        window = data.get("window", "today")
        tasks = data.get("tasks", [])
        done = [_title(t) for t in tasks if _is_done(t)]

        if done:
            face = "happy"
            head = (0, 70)  # a small upward nod of approval (pitch clamped 5..85)
            preview = "; ".join(done[:3])
            speech = (
                f"{len(done)} "
                f"{'task' if len(done) == 1 else 'tasks'} completed {window}: "
                f"{preview}."
            )
        else:
            face = "thinking"
            head = None
            speech = f"No tasks completed {window} yet. Let's get started."

        screen = [f"Completed {window}: {len(done)}"]
        screen += [f"  - {t}" for t in done[:5]]
        screen.append(f"source: {source}")

        return RenderResult(speech=speech, face=face, screen_lines=screen,
                            head=head)


APP = TaskStatusApp
