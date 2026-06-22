<div align="center">

# 🤖 stackchan-hermes

### Give your AI agent a face, a voice, and a little robot body.

**Drive an [M5Stack StackChan](https://github.com/stack-chan/stack-chan) desktop robot from [Hermes](https://claude-code.nousresearch.com) — speech, expressions, head motion, photos — plus a tiny framework for building "display apps" that surface live info on the robot.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Built on stackchan-mcp](https://img.shields.io/badge/built%20on-stackchan--mcp-ff69b4.svg)](https://github.com/kisaragi-mochi/stackchan-mcp)
[![MCP](https://img.shields.io/badge/protocol-MCP-000000.svg)](https://modelcontextprotocol.io)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#roadmap)

</div>

---

## ✨ What is this?

**StackChan** is a super-kawaii palm-sized communication robot — an M5Stack screen
with a cartoon face that blinks, two servos for a moving head, a speaker, and a
camera. **stackchan-hermes** turns it into a friendly physical avatar for your
self-hosted AI agent.

It does two things:

1. **Bridge** — a clean Python client that lets you (or Hermes) make the robot
   **speak**, **change its expression**, **move its head**, and **take photos**.
2. **App framework** — a tiny, extensible way to write *display apps*: little
   programs that compute something and have the robot announce it out loud and
   show it on its face. Two ship in the box: **token usage** and **task status**.

> **Demo (out of the box, no hardware needed):**
> `stackchan-hermes run token_usage --dry-run` →
> the robot would set an `idle` face and say *"You've used 1.2 million tokens
> today. That's 62% of your budget."*

It is built **on top of** the excellent community gateway
[`kisaragi-mochi/stackchan-mcp`](https://github.com/kisaragi-mochi/stackchan-mcp),
which handles the firmware, the WebSocket link to the ESP32, and TTS. We don't
reinvent any of that — we speak to its MCP tools.

---

## 🧭 Architecture

```
 ┌─────────────┐    WebSocket     ┌────────────────────────┐    stdio MCP    ┌────────────────────┐
 │  StackChan  │◀────────────────▶│   stackchan-mcp        │◀───────────────▶│   stackchan-hermes  │
 │  ESP32-S3   │  Opus audio,     │   gateway (Python)     │   (mcp SDK      │   client + apps     │
 │  (CoreS3)   │  servos, LCD,    │   stdio MCP server     │    stdio_client) │   ← THIS PROJECT    │
 │   👀  👄    │  camera          │   say / set_avatar …   │                  │   say/face/head/📷  │
 └─────────────┘                  └────────────────────────┘                 └────────────────────┘
                                            ▲
                                            │ stdio MCP (native MCP client, config.yaml)
                                            ▼
                                   ┌────────────────────┐
                                   │   Hermes agent     │  ← can ALSO call the robot in chat
                                   └────────────────────┘
```

The gateway is the **single bridge** to the device. Two consumers can use it: the
Hermes agent (via its native MCP client) and this project's apps (via our own
stdio client). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full story
and the transport rationale.

---

## 🔩 Hardware

| Spec | Value |
|---|---|
| Kit | M5Stack **StackChan K151** |
| Core | **CoreS3** — ESP32-S3, dual-core Xtensa LX7 @ 240 MHz, 16 MB flash, 8 MB PSRAM |
| Display | 2.0" 320×240 IPS, capacitive touch |
| Camera | GC0308 (front) — used by `take_photo` |
| Audio | Built-in mic + speaker (gateway streams Opus to it) |
| Servos | 2× for head **yaw** (pan) and **pitch** (tilt) |
| Link | Wi-Fi → WebSocket to the gateway on your Mac/PC |

> ⚠️ **Tilt-servo safety.** The pitch (tilt) servo's safe operating range is
> **5°–85°** (the M5Stack-recommended band). Driving outside it risks the head
> binding against the chassis. Both `move_head` in this client **and** the gateway
> clamp/reject out-of-range pitch — we keep the client-side clamp as defense in
> depth. Yaw is clamped to **-90°…90°**.

---

## 📋 Prerequisites

- A flashed StackChan (K151 / CoreS3) running the `stackchan-mcp` firmware.
- The **stackchan-mcp gateway** installed and reachable
  (`pipx install stackchan-mcp`, or a source checkout with its own venv).
- **Python 3.10+** and [`uv`](https://github.com/astral-sh/uv) (or `venv`).
- *(For speech)* a **VOICEVOX** engine running (default TTS) — e.g.
  `docker run --rm -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest`.
  Every non-audio tool (face, head, photo) works without it.

> Never flashed a StackChan before? The full walkthrough lives right here in the
> repo — see **[🔌 Flash your StackChan](#-flash-your-stackchan)** below and
> [docs/SETUP.md](docs/SETUP.md). No need to leave for upstream docs.

---

## 🔌 Flash your StackChan

Got a fresh K151 / CoreS3? Four steps get the community firmware on it. Use a
USB-C **data** cable (not charge-only), then **hold RST ~3 s** to enter download
mode.

```bash
# 1) Find the serial port (note the exact name, e.g. /dev/cu.usbmodem1101)
ls /dev/cu.usbmodem*

# 2) Download the latest prebuilt merged firmware
curl -L -o merged-binary.bin \
  https://github.com/kisaragi-mochi/stackchan-mcp/releases/latest/download/merged-binary.bin

# 3) Flash the full image to 0x0 (replace the port with yours)
esptool --chip esp32s3 --port /dev/cu.usbmodem1101 -b 460800 \
  write_flash 0x0 merged-binary.bin

# 4) Find your computer's LAN IP — you'll point the device at it next
ipconfig getifaddr en0
```

On first boot the device starts a Wi-Fi setup AP: join it, open the captive
portal at `http://192.168.4.1`, configure Wi-Fi, then on the **Advanced** tab set
**WebSocket Gateway URL** → `ws://<YOUR_MAC_LAN_IP>:8765/` and a **Gateway
Token** of your choice — it just has to match `STACKCHAN_TOKEN` on the gateway.

> 📖 **[See docs/SETUP.md](docs/SETUP.md) for the full walkthrough & troubleshooting** —
> including the esptool 5.x note, optional VOICEVOX speech, and what to do if you
> previously flashed the wrong fork (`migratorywhale/stackchan-mcp`).

---

## 🚀 Quick start

```bash
# 1) Clone + install (editable) into an isolated venv
git clone https://github.com/sontakey/Hermes-stackchan
cd Hermes-stackchan
uv venv
uv pip install -e .

# 2) See what's available
.venv/bin/stackchan-hermes list

# 3) Run an app in DRY-RUN — no gateway, no hardware needed
.venv/bin/stackchan-hermes run token_usage --dry-run
.venv/bin/stackchan-hermes run task_status --dry-run

# 4) Drive the REAL robot (gateway auto-spawned over stdio)
#    Point STACKCHAN_GATEWAY_CMD at your gateway's console script if needed.
.venv/bin/stackchan-hermes run token_usage
```

The full flash → gateway → wire → run flow:

| Step | What | Where |
|---|---|---|
| 1 | Flash firmware to the CoreS3 | [docs/SETUP.md](docs/SETUP.md) |
| 2 | Run / install the gateway (stdio MCP server) | upstream `stackchan-mcp` |
| 3 | (Optional) Wire the gateway into the **Hermes agent** | [below](#-how-hermes-connects) |
| 4 | Run a display app | `stackchan-hermes run <app>` |

---

## 🔌 How Hermes connects

Hermes has a native MCP client. To let the **Hermes agent itself** drive the robot
in conversation, add the gateway to `~/.hermes/config.yaml`
(see [`examples/hermes-config.snippet.yaml`](examples/hermes-config.snippet.yaml)):

```yaml
mcp_servers:
  stackchan:
    command: "/path/to/stackchan-mcp/.venv/bin/stackchan-mcp"  # zero subcommand = stdio MCP server
    args: []
    env:
      VISION_HOST: "<YOUR_MAC_LAN_IP>"         # this host's LAN IP (for take_photo)
      # STACKCHAN_TOKEN: "<YOUR_TOKEN>"        # ONLY if the device has a token — else it gets REJECTED
      # WS_PORT: "8865"                        # ONLY if 8765 is taken; device URL must match this port
    enabled: true
    timeout: 120
    connect_timeout: 60
```

Hermes registers the tools as `mcp_stackchan_say`, `mcp_stackchan_set_avatar`,
`mcp_stackchan_move_head`, `mcp_stackchan_take_photo`, … Restart Hermes (MCP
servers are discovered at startup), then verify with `hermes mcp list`
(should show `stackchan ✓ enabled`). The token/port lines are commented for a
reason — getting them wrong silently rejects the device; see
[docs/SETUP.md](docs/SETUP.md#troubleshooting).

> **One owner at a time.** The gateway owns the single WebSocket to the device.
> Don't run a standalone gateway *and* let Hermes spawn one *and* run our client
> simultaneously against the same robot — pick one owner per run.

---

## 🧱 The app framework

Writing a display app means answering one question: **"what should the robot say
and show?"** You return that as a `RenderResult`; the runner applies it (or prints
it in dry-run).

```python
from stackchan_hermes import StackchanApp, RenderResult

class HelloApp(StackchanApp):
    name = "hello"
    description = "Wave and say hi."

    def render(self) -> RenderResult:
        return RenderResult(
            speech="Hello! I'm StackChan.",
            face="happy",                 # idle/happy/thinking/sad/surprised/embarrassed/off
            screen_lines=["Hello world"],
            head=(0, 60),                 # optional (yaw, pitch); pitch auto-clamped 5..85
        )

APP = HelloApp   # <- export `APP`; it's auto-discovered, no registry edits
```

`render()` is **pure** — it returns data, it doesn't touch the device. That makes
apps trivially testable and previewable. Under the hood:

- **`StackchanClient`** — real client; spawns the gateway and calls its MCP tools
  over stdio (official `mcp` SDK).
- **`DryRunClient`** — same methods, just prints what *would* happen.
- **`run_render()`** — applies a result in order: face → head → speech.
- **`sources.load_data()`** — resolve app data from a file, an env var (path or
  inline JSON), or a built-in demo payload.

---

## 📦 The two starter apps

### `token_usage`
Speaks and shows how many tokens you've used, and picks a face by how close you
are to budget.

| Data source (priority) | |
|---|---|
| `STACKCHAN_TOKEN_USAGE` env var | JSON file path **or** inline JSON |
| built-in demo | 1.24M / 2M today |

```jsonc
// schema
{ "used": 1240000, "limit": 2000000, "window": "today" }  // limit optional
```
Face threshold (fraction of `limit`): `<0.5` → **happy**, `0.5–0.85` → **idle**,
`>0.85` → **sad** (concerned).

### `task_status`
Speaks and shows recently completed tasks.

| Data source (priority) | |
|---|---|
| `STACKCHAN_TASK_STATUS` env var | JSON file path **or** inline JSON |
| built-in demo | a few sample tasks |

```jsonc
// schema
{ "window": "today",
  "tasks": [ {"title": "Shipped X", "status": "done"},
             {"title": "WIP Y", "status": "in_progress"} ] }
```
Counts only `status == "done"` (a bare string is treated as done). Any completed
→ **happy** + a small nod; none → **thinking**.

Try them with real data:

```bash
STACKCHAN_TOKEN_USAGE=examples/token_usage.sample.json \
  .venv/bin/stackchan-hermes run token_usage --dry-run
```

---

## ✍️ Write your own app

1. Create `stackchan_hermes/apps/my_app.py`.
2. Subclass `StackchanApp`; set `name` + `description`; implement `render()`.
3. `APP = MyApp` at module level — auto-discovered.
4. Use `stackchan_hermes.sources.load_data(...)` for any external data so it runs
   in demo mode out of the box.
5. `stackchan-hermes run my_app --dry-run` to preview.

Ideas: reminders, calendar next-event, build/CI status, weather, "pomodoro over",
inbox count, a random encouragement. The four primitives (`say`, `set_avatar`,
`move_head`, `take_photo`) compose into essentially anything.

---

## 🗺️ Roadmap

- [ ] On-screen text rendering (push `screen_lines` to the LCD, not just speech)
- [ ] Lip-sync via `set_mouth_sequence` during `say`
- [ ] Richer client surface (LEDs, blink, brightness, `listen`/STT)
- [ ] A scheduler so apps can run on a timer / via Hermes cron
- [ ] Pull live token/task data straight from a Hermes data source
- [ ] Unit tests + CI

---

## 🤝 Contributing

PRs welcome — especially new apps. See [CONTRIBUTING.md](CONTRIBUTING.md). This is
a friendly hobby project; be kind, keep it small, verify device behaviour against
the upstream gateway source.

---

## 🙏 Credits & license

This project stands entirely on the shoulders of:

- **[stack-chan](https://github.com/stack-chan/stack-chan)** — the original
  super-kawaii robot by **Shinya Ishikawa** (2021). MIT.
- **[kisaragi-mochi/stackchan-mcp](https://github.com/kisaragi-mochi/stackchan-mcp)**
  — the firmware + MCP gateway this toolkit drives. MIT (with a small GPL-3.0
  island in the firmware servo lib; the Python gateway is a separate process).

Please support and credit them. **stackchan-hermes** is licensed under the
[MIT License](LICENSE) — © 2026 **Sameer Sontakey**.

<div align="center">

*Made with ☕ and a tiny robot.*

</div>
