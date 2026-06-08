# TapHome Local for Home Assistant

![Logo](custom_components/taphome_local/icon.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-2.4.0-blue)](https://github.com/khral07/ha-taphome-lokal)

**TapHome Local** is a custom integration for Home Assistant that provides **instant, local control** of your TapHome smart home system. It communicates directly with the TapHome Core unit via the local API and uses **Webhooks** for immediate state updates.

---

## Features

### Instant updates via Webhook
The integration supports **Push notifications**. When you switch a light or press a button in your house, Home Assistant updates **instantly** (milliseconds). No more waiting for polling intervals.

### Physical button support
Full support for **Push Buttons** (Smart Switch inputs).
- Buttons act as impulses (automatically reset after 0.3s).
- Advanced logic prevents buttons from getting stuck in the ON state during restarts or polling checks.

### Zero configuration
- **No YAML:** Everything is configured via the Home Assistant GUI.
- **Auto-Discovery:** Automatically detects all exposed devices.
- **Dynamic Settings:** Change your Core IP or API Token anytime via the Configure button.
- **Re-authentication:** If the API token becomes invalid, Home Assistant prompts you to enter a new one — no need to delete and re-add the integration.

### Supported devices
- **Lights:** On/Off, Dimming (Hue & Analog), Tunable White (CCT). Colour + brightness are sent in a single command for flicker-free changes.
- **Climate:** Smart Room Controllers with dynamic min/max temperature limits (heating)
- **Covers:** Blinds and shutters with precise positioning, **slat tilt** and **opening/closing movement** indication
- **Switches:** Relay outputs, sockets, valves
- **Sensors:** Temperature, Humidity, CO2, Power, Energy, Illuminance, Wind — plus **generic Modbus variables / energy meters** (auto-detected, with units parsed from the device name e.g. `[kWh]`)
- **Binary Sensors:** Reed contacts (Doors/Windows/Motion/Gates)
- **Buttons:** Physical push buttons
- **Alarm:** Virtual Alarm control (Arm/Disarm)
- **Modes:** Multi-value switches as selectors (e.g. Presence: Home/Away); disabled options are hidden automatically

---

## Installation

### Via HACS (Recommended)
1. Open **HACS** in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add this repository URL, category **Integration**
4. Find **TapHome Local** and install
5. Restart Home Assistant

### Manual
1. Download the `custom_components/taphome_local` folder
2. Copy it to your HA `/config/custom_components/` directory
3. Restart Home Assistant

---

## Configuration

### Step 1: Add the integration
1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **TapHome Local**
3. Enter:
   - **API URL:** `http://<YOUR_CORE_IP>/api/TapHomeApi/v1`
   - **Token:** Your local API token (TapHome → Settings → Expose Devices → Token)

### Step 2: Configure Webhook (required for instant updates)
1. After setup go to **Settings → Devices & Services → TapHome Local → Configure**
2. Copy the **Webhook URL** shown there
3. In the **TapHome app:** Settings → My Location → Expose Devices → TapHome API → enable **Allow Web Hook** → paste the URL → Save

---

## Slovak description / Slovenský popis

**TapHome Local** je integrácia pre Home Assistant s okamžitou odozvou vďaka podpore Webhookov. Komunikuje priamo s TapHome Core jednotkou cez lokálne API — žiadny cloud, žiadne oneskorenie.

### Inštalácia Webhooku
Skopírujte **Webhook URL** z nastavení integrácie (Settings → TapHome Local → Configure) a vložte ju do aplikácie TapHome (Nastavenia → Vystaviť zariadenia → TapHome API → Web Hook URL).

---

## What's new in 2.4.0

- **Energy meters & Modbus variables now appear** as sensors (previously hidden), with units auto-parsed from the device name.
- **Blinds**: slat **tilt** control and **opening/closing** movement indication; corrected open/closed orientation.
- **Multi-value switches** no longer show up twice (as both a switch and a selector); disabled mode options are hidden.
- **Re-authentication flow** when the API token expires.
- **Batched light commands** (colour + brightness + on in one request) with automatic fallback for older Cores.
- Reliability/modernization under the hood (HA 2025/2026 patterns). Physical-button behaviour is unchanged.

See full release notes in the [GitHub release](https://github.com/khral07/ha-taphome-lokal/releases).

---

## Contact

Questions or issues: **adrianmucska@gmail.com** or open a [GitHub issue](https://github.com/khral07/ha-taphome-lokal/issues).

**Disclaimer:** This is a community integration, not officially affiliated with TapHome. Use at your own risk.
