# TapHome Local for Home Assistant 🏠
![Logo](custom_components/taphome_lokal/icon.png)


[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/USERNAME/REPO_NAME)

**TapHome Local** is a custom integration for Home Assistant that provides **instant, local control** of your TapHome smart home system. It communicates directly with the TapHome Core unit via the local API and uses **Webhooks** for immediate state updates.

---

## ✨ Key Features (v2.0)

### ⚡ INSTANT UPDATES VIA WEBHOOK
The integration now supports **Push notifications**. When you switch a light or press a button in your house, Home Assistant updates **instantly** (milliseconds). No more waiting for polling intervals!

### 🔘 PHYSICAL BUTTON SUPPORT
Full support for **Push Buttons** (Smart Switch inputs).
* Buttons act as impulses (automatically reset after 0.3s).
* **Zero Ghosting:** Advanced logic prevents buttons from getting "stuck" in the ON state during restarts or polling checks.

### 🔍 ZERO CONFIGURATION
* **No YAML:** Everything is configured via the Home Assistant GUI.
* **Auto-Discovery:** Automatically detects all exposed devices.
* **Dynamic Settings:** Change your Core IP or API Token anytime via the "Configure" button.

### 📱 Supported Devices
* 💡 **Lights:** On/Off, Dimming (Hue & Analog), Tunable White (CCT). Includes "Move-to-On" logic.
* 🌡️ **Climate:** Smart Room Controllers with dynamic min/max temperature limits.
* 🪟 **Covers:** Blinds and shutters with precise positioning.
* 🔌 **Switches:** Relay outputs, sockets, valves.
* 📊 **Sensors:** Temperature, Humidity (auto % conversion), CO2, Power, Energy, etc.
* 🚪 **Binary Sensors:** Reed contacts (Doors/Windows).
* 🔘 **Buttons:** Physical push buttons (mapped as binary sensors for automations).
* 🛡️ **Alarm:** Virtual Alarm control (Arm/Disarm).
* 🎛️ **Modes:** Multi-value switches (e.g., Presence: Home/Away).

---

## 🚀 Installation

### Option 1: Via HACS (Recommended)
1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations** > **Three dots (top right)** > **Custom repositories**.
3.  Add the URL of this repository.
4.  Category: **Integration**.
5.  Click **Add** and then download **"TapHome Local"**.
6.  Restart Home Assistant.

### Option 2: Manual
1.  Download the `custom_components/taphome_local` folder from this repository.
2.  Copy it to your Home Assistant's `/config/custom_components/` directory.
3.  Restart Home Assistant.

---

## ⚙️ Configuration & Webhook Setup

### Step 1: Add Integration in Home Assistant
1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **TapHome Local**.
3.  Enter your details:
    * **API URL:** `http://<YOUR_CORE_IP>/api/TapHomeApi/v1`
    * **Token:** Your local API token (TapHome-> Settings-> Expose Devices-> Token).

### Step 2: Configure Webhook (Crucial for Speed!)
To enable instant updates, you must tell TapHome where to send the data.

1.  After first inicalization of integration In Home Assistant, go to **Settings** > **Devices & Services** > **TapHome Local**.
2.  Click **Configure**.
3.  Copy the URL displayed in the **`Webhook URL`** field.
    * *Example:* `http://192.168.1.50:8123/api/webhook/taphome_local_push_xxxxx`. If its still not there click on reload button in integration.
4.  Open the **TapHome App**:
    * Go to **Settings** -> **My Location** -> **Expose Devices** -> **TapHome API**.
    * Enable **Allow Web Hook**.
    * Paste the URL into **Web Hook URL**.
    * Save

**Done!** Try pressing a physical button or toggling a light in TapHome – Home Assistant should react instantly.

---

## 🇸🇰 Slovak Description

**TapHome Local v2** je pokročilá integrácia pre Home Assistant, ktorá prináša okamžitú odozvu vďaka podpore **Webhookov**.

### ✨ Čo je nové vo verzii 2.0?

* **⚡ Okamžitá odozva (Push):** Home Assistant už nečaká, kým sa opýta na stav. TapHome posiela zmeny okamžite.
* **🔘 Podpora Tlačidiel:** Fyzické tlačidlá v dome (Push Buttons) sú v HA viditeľné ako senzory, ktoré pri stlačení prebliknú. Ideálne pre automatizácie!
* **🛠️ Jednoduché nastavenie:** IP adresu, Token aj Webhook URL nájdete a zmeníte priamo v nastaveniach integrácie.

### Inštalácia Webhooku
Pre správnu funkčnosť (okamžité reakcie) je nutné skopírovať **Webhook URL** z nastavení integrácie v Home Assistantovi a vložiť ju do aplikácie **TapHome** (Nastavenia -> Vystaviť zariadenia -> TapHome API -> Web Hook URL).

---

**Disclaimer:** This is a custom integration and is not officially affiliated with TapHome. Use at your own risk.
