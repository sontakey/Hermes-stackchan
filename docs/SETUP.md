# 🛠️ StackChan Setup — Flash & First Run

A self-contained, start-to-finish guide for taking a fresh **M5Stack StackChan
(K151 / CoreS3)** from the box to a robot that talks to your gateway. It covers
the cable you need, putting the device in download mode, flashing the prebuilt
community firmware, the first-boot Wi-Fi setup, pointing the device at your
gateway, and (optionally) enabling speech.

The firmware is **[`kisaragi-mochi/stackchan-mcp`](https://github.com/kisaragi-mochi/stackchan-mcp)** —
a community firmware that **replaces** the cloud-locked M5Stack factory image.
The ESP32 connects *outbound* over WebSocket to the Python gateway on your
Mac/PC; the gateway re-exposes everything as an MCP server. See the upstream repo
for the canonical, deep-dive reference; this page is the practical quickstart.

> **Already flashed the *wrong* fork?** There is a separate project with the
> *identical* name — `migratorywhale/stackchan-mcp` (build-from-source
> PlatformIO firmware, HTTP architecture, Fish Audio / edge-tts). It is **not**
> what this project uses. If you flashed that by mistake, there's nothing to
> uninstall: just **re-flash with the steps below**. `esptool write_flash 0x0`
> overwrites the entire image (bootloader + partition table + app) cleanly.

---

## What you need

| Item | Notes |
|---|---|
| M5Stack StackChan **K151 / CoreS3** | ESP32-S3 based |
| A **USB-C DATA cable** | ⚠️ Must carry data, not charge-only. Many bundled cables are power-only — if the device never enumerates as a serial port, suspect the cable first. |
| `esptool` | `pip install esptool` (or use the one in your gateway's venv). esptool **5.x** works fine. |
| The **stackchan-mcp gateway** | Cloned/installed somewhere on your machine. Wherever you cloned `kisaragi-mochi/stackchan-mcp` is referred to below as your **gateway dir**. |

You will flash the **prebuilt merged binary** — no ESP-IDF / Docker build needed.

---

## 1. Put the CoreS3 in download mode

1. Connect the CoreS3 to your computer with a USB-C **data** cable.
2. Enter download/boot mode: **hold the RST button ~3 seconds** (until the green
   LED confirms download mode), then release.

---

## 2. Find the serial port

macOS enumerates the CoreS3 CDC port as `/dev/cu.usbmodem*`:

```bash
ls /dev/cu.usbmodem*
```

Note the exact name (e.g. `/dev/cu.usbmodem1101`) — you'll pass it as `--port`
below. If nothing shows up, see [Troubleshooting](#troubleshooting).

---

## 3. Download the prebuilt firmware

Grab the latest **merged** binary (full image incl. bootloader + partition
table) straight from the Releases "latest" alias — no version pinning needed:

```bash
# Run this from your gateway dir (or anywhere you like)
curl -L -o merged-binary.bin \
  https://github.com/kisaragi-mochi/stackchan-mcp/releases/latest/download/merged-binary.bin
```

> For later **app-only** updates (that preserve Wi-Fi/NVS), upstream also ships
> an `xiaozhi.bin` you flash to `0x20000`. For a first flash, use the merged
> binary above.

---

## 4. Flash to `0x0`

A clean install writes the full image to offset `0x0`. This resets NVS, so
Wi-Fi + the saved gateway URL/token will need re-entering on first boot — exactly
what you want for a first flash over the factory firmware. **Replace the port**
with the one from step 2:

```bash
esptool --chip esp32s3 --port /dev/cu.usbmodem1101 -b 460800 \
  write_flash 0x0 merged-binary.bin
```

> **esptool 5.x note:** newer esptool prints a deprecation warning that the
> `esptool.py` command is being renamed to `esptool` — it's harmless. Both
> `esptool ...` and `esptool.py ...` work identically; use whichever is on your
> PATH.

After flashing, the device reboots automatically.

---

## 5. First boot — Wi-Fi captive portal

On first boot the firmware comes up as a Wi-Fi setup access point (standard
xiaozhi-esp32 flow):

1. From your phone or laptop, join the device's setup AP.
2. Open the captive portal at **`http://192.168.4.1`**.
3. Configure your home/office Wi-Fi so the device can reach your gateway's LAN.

---

## 6. Point the device at your gateway

First, find **your computer's LAN IP** (the address the ESP32 will dial). On
macOS:

```bash
ipconfig getifaddr en0   # prints something like 192.168.x.y
```

Then, on the captive portal (`http://192.168.4.1`), open the **Advanced** tab and set:

- **WebSocket Gateway URL** → `ws://<YOUR_MAC_LAN_IP>:8765/`
  (substitute the IP from `ipconfig getifaddr en0`)
- **Gateway Token** → any secret you choose, e.g. `<YOUR_TOKEN>`. The exact
  value doesn't matter — it just has to **match** the token you set on the
  gateway side (`STACKCHAN_TOKEN`, see step 7). Leave both blank to disable, or
  set the same string on both sides.

Save → the device reboots and dials your gateway.

> **Tip:** the gateway also advertises mDNS (`_stackchan-mcp._tcp.local.`), so
> leaving the URL blank lets the firmware auto-discover the gateway on the LAN.
> The token must still be set manually. A hardcoded URL is the reliable path;
> mDNS is the convenience path.

---

## 7. Start the gateway

For a manual smoke test you can run the gateway directly. (In normal use, Hermes
spawns it for you as a stdio MCP server — see the main
[README](../README.md#-how-hermes-connects).)

```bash
cd <your-gateway-dir>          # wherever you cloned kisaragi-mochi/stackchan-mcp
source .venv/bin/activate
export STACKCHAN_TOKEN="<YOUR_TOKEN>"        # must match the device's Gateway Token
export VISION_HOST="<YOUR_MAC_LAN_IP>"       # your computer's LAN IP (enables take_photo)
stackchan-mcp                                 # zero-subcommand = stdio MCP server
```

Default listeners:

- WebSocket (ESP32 → gateway): `0.0.0.0:8765`
- HTTP capture (ESP32 → gateway): `0.0.0.0:8766`

Once the device connects and a TTS engine is up (next section), every tool works
— `move_head`, `set_avatar`, `take_photo`, `get_status`, and `say`.

---

## 8. (Optional) Speech — VOICEVOX

The gateway's default TTS engine is **VOICEVOX**, an external HTTP service you
run yourself (LGPL-3.0, runs in its own process; the gateway just makes HTTP
calls to it). The easiest way is Docker:

```bash
docker run --rm -p '127.0.0.1:50021:50021' \
  voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

- Listens on `127.0.0.1:50021` (the gateway default).
- Override with `STACKCHAN_VOICEVOX_URL` if needed.

**Without VOICEVOX running, `say` fails**, but every non-audio tool (`move_head`,
`set_avatar`, `take_photo`, `get_status`, …) works fine — so you can flash and
verify motion/avatar first, then add speech later. With VOICEVOX up and the
device connected, calling `say(text="hello")` streams audio to the device
speaker (no firmware change needed for audio).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| **Port `8765` already in use** | Something else is bound to the gateway port. Find it with `lsof -i :8765`, confirm what it is, then free the port (stop or kill that process) so the gateway can bind. |
| **No `/dev/cu.usbmodem*` device appears** | Re-seat the USB-C cable (or try a different, known-**data** cable / port), then redo the **RST hold ~3 s** to re-enter download mode and check `ls /dev/cu.usbmodem*` again. |
| **`say` fails / no audio** | VOICEVOX isn't running. Start the engine (step 8) and retry. Non-audio tools are unaffected. |
| **You flashed `migratorywhale/stackchan-mcp` by mistake** | Just re-flash from step 1. `esptool write_flash 0x0` overwrites everything — nothing to uninstall. |

---

## Credits

Firmware: **[kisaragi-mochi/stackchan-mcp](https://github.com/kisaragi-mochi/stackchan-mcp)**
— the prebuilt merged binary, the WebSocket-out architecture, and the TTS
gateway all come from there. Refer to its README as the canonical source for
deeper detail. Please support and credit the upstream project.
