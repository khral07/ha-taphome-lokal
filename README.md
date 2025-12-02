# TapHome Local for Home Assistant 🏠
![Logo](custom_components/taphome_lokal/icon.png)


[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/USERNAME/REPO_NAME)

**TapHome Local** is a custom integration for Home Assistant that allows you to control your **TapHome** smart home system locally, without relying on the cloud. It communicates directly with the TapHome Core unit via the local API.

---

## ✨ Features

* **100% Local Control:** Works even without internet connection.
* **Fast Response:** Uses local polling (default 2s interval) and direct GET requests for instant control.
* **Easy Setup:** Fully configurable via Home Assistant GUI (Config Flow).
* **Supported Devices:**
    * 💡 **Lights:** On/Off, Dimming (Hue & Analog), Tunable White (CCT). Includes "Move-to-On" logic.
    * 🌡️ **Climate:** Smart Room Controllers with dynamic min/max temperature limits.
    * 🪟 **Covers:** Blinds and shutters with precise positioning.
    * 🔌 **Switches:** Relay outputs, sockets, valves.
    * 📊 **Sensors:** Temperature, Humidity (auto % conversion), CO2, Power, Energy, etc.
    * 🚪 **Binary Sensors:** Reed contacts (Doors/Windows).
    * 🛡️ **Alarm:** Virtual Alarm control (Arm/Disarm).
    * 🔘 **Modes:** Multi-value switches (e.g., Presence: Home/Away).

## 🚀 Installation

### Option 1: Via HACS (Recommended)
1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations** > **Three dots (top right)** > **Custom repositories**.
3.  Add the URL of this repository.
4.  Category: **Integration**.
5.  Click **Add** and then download "TapHome Local".
6.  Restart Home Assistant.

### Option 2: Manual
1.  Download the `custom_components/taphome_local` folder from this repository.
2.  Copy it to your Home Assistant's `/config/custom_components/` directory.
3.  Restart Home Assistant.

## ⚙️ Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **TapHome Local**.
3.  Enter your details:
    * **API URL:** `http://<YOUR_CORE_IP>/api/TapHomeApi/v1` (e.g., `http://192.168.1.50/api/TapHomeApi/v1`)
    * **Token:** Your local API token from TapHome settings.

> **How to get the Token:**
> In the TapHome App, go to **Settings** -> **Expose Devices** -> **TapHome API** -> **Create new access token**. Ensure the token has `Read` and `Write` permissions (or simply access to devices you want to control).

## 🛠️ Advanced Settings

You can enable **Debug Logging** to troubleshoot connection issues:
1.  Go to the **TapHome Local** integration card.
2.  Click **Configure**.
3.  Enable **Debug Logging**.
4.  Check your Home Assistant logs for detailed communication data.

---

## 🇸🇰 Slovak Description

**TapHome Local** je integrácia pre Home Assistant, ktorá umožňuje plné ovládanie systému TapHome cez lokálnu sieť.

**Hlavné výhody:**
* Funguje bez cloudu (lokálne API).
* Podporuje všetky bežné zariadenia (Svetlá, Žalúzie, Kúrenie, Senzory, Alarm).
* Automaticky opravuje formát dát (napr. percentá vlhkosti).
* Inštalácia a nastavenie cez grafické rozhranie HA.
* ak niečo nepôjde, neváhajte ma kontaktovať

---

**Disclaimer:** This is a custom integration and is not officially affiliated with TapHome. Use at your own risk.
