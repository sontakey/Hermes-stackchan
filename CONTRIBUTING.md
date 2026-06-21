# Contributing to stackchan-hermes

Thanks for your interest! This is a small, friendly hobby project — first-time
and hobbyist contributors are very welcome.

## Ground rules

- **User-first, not infra-first.** This drives one robot on a home LAN. Optimise
  for "does it work for the person sitting next to the robot," not 10k-RPS SaaS
  concerns.
- **Keep it small and extensible.** Prefer a clean seam over a big feature. New
  capabilities usually mean a new *app*, not changes to the core.
- **No fabricated device behaviour.** Tool names and signatures must match the
  upstream [`kisaragi-mochi/stackchan-mcp`](https://github.com/kisaragi-mochi/stackchan-mcp)
  gateway source. Verify before you wire.

## Dev setup

```bash
git clone <your-fork>
cd stackchan-hermes
uv venv && uv pip install -e ".[dev]"
.venv/bin/stackchan-hermes list
.venv/bin/stackchan-hermes run token_usage --dry-run
```

## Adding an app

1. Create `stackchan_hermes/apps/<your_app>.py`.
2. Subclass `StackchanApp`, set `name` + `description`, implement `render()`.
3. Export it: `APP = YourApp`. It's auto-discovered — no registry edits.
4. Use `stackchan_hermes.sources.load_data(...)` for any external data so your
   app runs in demo mode out of the box.
5. Verify: `stackchan-hermes run <your_app> --dry-run`.

## Before opening a PR

```bash
.venv/bin/ruff check .
.venv/bin/pytest        # if/when tests are added
```

Keep commits focused and write a clear message. Be kind in reviews — explain
*why*, mark stylistic notes as non-blocking.

## License

By contributing you agree your work is licensed under the project's
[MIT License](LICENSE).
