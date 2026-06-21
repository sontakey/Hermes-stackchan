# Architecture

`stackchan-hermes` is a thin, opinionated layer on top of the community
[`kisaragi-mochi/stackchan-mcp`](https://github.com/kisaragi-mochi/stackchan-mcp)
gateway. It does **not** reimplement the device protocol; it speaks to the
gateway's MCP tools.

## Data flow

```
  ┌─────────────┐   WebSocket    ┌──────────────────────┐   stdio MCP   ┌──────────────────┐
  │  StackChan  │◀──────────────▶│   stackchan-mcp      │◀─────────────▶│  stackchan-hermes │
  │  ESP32-S3   │  (Opus audio,  │   gateway (Python)   │  (mcp SDK     │  client + apps    │
  │  (CoreS3)   │   servo, LCD)  │   stdio MCP server   │   stdio_client)│  (this project)  │
  └─────────────┘                └──────────────────────┘               └──────────────────┘
                                          ▲                                        │
                                          │ stdio MCP (same gateway)               │ renders
                                          ▼                                        ▼
                                 ┌──────────────────┐                    ┌──────────────────┐
                                 │  Hermes agent    │                    │  RenderResult    │
                                 │  (native MCP)    │                    │ speech/face/head │
                                 └──────────────────┘                    └──────────────────┘
```

The gateway is the single bridge to the device. Two independent consumers can use
it: the **Hermes agent** (via Hermes's native MCP client, configured in
`config.yaml`) and **this project's apps** (via our own stdio client). Only one
process should *own* the gateway/device at a time — see the README's "one owner"
note.

## Why stdio MCP (transport decision)

The gateway is a **stdio MCP server** — confirmed in the upstream source:

- `gateway/AGENTS.md`: *"The gateway runs as a stdio MCP server."*
- `gateway/stackchan_mcp/stdio_server.py`: registers the tools (`say`,
  `set_avatar`, `move_head`, `take_photo`, …) via `@server.list_tools()`.

So `StackchanClient` uses the **official `mcp` Python SDK's `stdio_client`** to
spawn the gateway's `stackchan-mcp` console script and call tools — exactly how
Hermes itself connects. We deliberately did **not** invent a WebSocket client:
the device's WebSocket is the gateway↔ESP32 hop and is not the public surface for
tool calls. Using MCP stdio means our tool names and arguments are guaranteed to
match the gateway, and we inherit its safety guards.

## Verified tool signatures (from `stdio_server.py`)

| Tool | Arguments | Notes |
|---|---|---|
| `say` | `text` (req), `voice="voicevox"`, `speaker_id?`, `reference_audio?` | gateway-side TTS → device speaker |
| `set_avatar` | `face` ∈ idle/happy/thinking/sad/surprised/embarrassed/off | visible LCD expression |
| `move_head` | `yaw` (-90..90), `pitch` (5..85), `speed?` | **MCP rejects out-of-range; we clamp client-side too** |
| `take_photo` | `question` (req) | camera capture → AI description |

## The app framework

- **`StackchanApp`** (abstract): `name`, `description`, `render() -> RenderResult`.
  `render()` is pure — it returns data, it does not touch the device. This makes
  apps testable and previewable.
- **`RenderResult`**: `speech`, `face`, `screen_lines`, optional `head` `(yaw, pitch)`.
- **`registry.discover_apps()`**: imports every module under
  `stackchan_hermes.apps` and collects each module's `APP` symbol. Zero-config
  registration.
- **`registry.run_render()`**: applies a `RenderResult` to a client in a sane
  order (face → head → speech).
- **Clients**: `StackchanClient` (real, stdio MCP) and `DryRunClient` (prints
  actions; same surface). Both enforce the pitch 5..85 / yaw -90..90 clamp.
- **`sources.load_data()`**: resolves app data from a file path, an env var
  (file path or inline JSON), or a built-in demo payload — so apps run out of
  the box and cleanly upgrade to live data.

## Adding a new app

Drop a module in `stackchan_hermes/apps/`, subclass `StackchanApp`, export `APP`.
That's the whole extension point — "essentially do anything" by composing
`say` / `set_avatar` / `move_head` / `take_photo` inside a `RenderResult` (and
richer device tools via the client as the project grows).
