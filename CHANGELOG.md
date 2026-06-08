# Changelog

All notable changes to **TapHome Local** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [2.4.0] - 2026-06-08

Reliability improvements, several bug fixes, and modernization for Home Assistant 2025/2026.
Physical-button behaviour is unchanged.

### Added
- Energy meters & generic **Modbus variables** (`VariableState`) are now exposed as sensors —
  previously hidden. Units and device class are auto-parsed from a trailing `[unit]` in the
  device name (e.g. `[kWh]`).
- Blind **slat tilt** control (open/close/set tilt) for blinds that support it.
- Blind **movement indication** — covers show *opening* / *closing* while moving.
- **Re-authentication flow** — invalid API token (HTTP 401) now prompts for a new token
  instead of failing silently.
- **Duplicate-config protection** — adding the same Core twice is blocked (unique ID from the
  Core's location).

### Fixed
- Multi-value switches no longer appear twice (as both a switch and a selector).
- Disabled multi-value options are hidden (e.g. unused presence/alarm modes).
- Blind open/closed orientation corrected (TapHome reports the inverse of Home Assistant).
- Binary sensors report *unknown* instead of *off* before the first value arrives.

### Changed
- Lights send colour + brightness + on in a single batched command (flicker-free), with
  automatic fallback to sequential writes on Cores that don't support batching.
- Cleaner numeric value formatting sent to the Core.

### Internal
- Migrated to `entry.runtime_data` and a typed config entry; coordinator receives its config
  entry (removes deprecation warnings).
- Adopted `has_entity_name`; added re-auth translations (EN/SK), `loggers` in the manifest, and
  a small unit-test suite.

## [2.3.1] - 2026-05-10

### Added
- New **valve** platform for water valves.
- Slovak & English translations.
- Hub classification in the manifest; `iot_class` set to `local_push`.

### Changed / Fixed
- Shared HTTP session (lower memory use), 10s timeout on all requests, 503 retry on writes.
- Startup connectivity checks and device-removal protection.
- Button **press vs. hold** distinction; webhook fallback handling.

## [2.1.4] - 2026-02-20

- Maintenance release.

## [2.1.3] - 2026-02-20

### Fixed
- Binary sensor handling.

## [2.1.2] - 2026-02-20

- Bug fix.

## [2.1.1] - 2026-02-20

- Bug fixes.

## [2.1.0] - 2026-02-20

### Added
- RGBW light support with full colour-wheel control.
- Garage door / gate support via the **cover** platform.
- Configuration menu for manual device exposure (assign devices to platforms).

### Changed / Fixed
- Rewrote switch logic to eliminate duplicate entities.
- Proper cover icons and improved impulse-button handling.

## [2.0.5] - 2026-02-17

### Added
- Full RGB/RGBW light support using the Hue & Saturation colour model.

### Changed
- Switch filtering ignores colour-light attributes, preventing duplicate switch entities.

## [2.0.4] - 2026-02-16

### Added
- Full RGB/RGBW light support for colour modules with native colour-wheel control.

### Changed
- Switch filtering upgraded to ignore colour-light attributes.

## [2.0.3] - 2026-02-11

- Maintenance release.

## [2.0.2] - 2026-02-11

### Fixed
- Manifest corrections.

## [2.0.1] - 2026-02-11

### Added
- Manual device deletion through the Home Assistant UI.

### Changed
- Skip switch creation for devices with dimming attributes, lighting category, or blind
  identification (removes duplicate switch entities for lights).

## [2.0.0] - 2026-02-11

### Added
- Manual device deletion UI support.

### Changed
- System cleanup and improved device management; removed duplicate switch entities for lights.
- Note: duplicate entities become *unavailable* after the update and require manual removal.

## [1.1.0] - 2026-02-10

### Added
- Timestamp sensors for push buttons (ID 52) so every press registers.

### Fixed
- Humidity percentage scaling.
- Eliminated duplicate light/switch entities; prevented ghost switching during polling.
- Note: requires automation updates for timestamp-sensor triggers.

## [1.2.0] - 2025-12-03

### Added
- Push-button support with 0.3s impulse behaviour.
- Webhook URL display in the GUI.

### Changed
- Major architectural shift from polling to instant **Webhook push** notifications.
- Polling interval increased to 60s as a fallback; fixed button "ghosting" via polling filters.

## [1.0.2] - 2025-12-03

### Added
- Support for buttons.

## [1.0.1] - 2025-12-02

### Added
- Integration logo.

[2.4.0]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.4.0
[2.3.1]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.3.1
[2.1.4]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.1.4
[2.1.3]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.1.3
[2.1.2]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.1.2
[2.1.1]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.1.1
[2.1.0]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.1.0
[2.0.5]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.5
[2.0.4]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.4
[2.0.3]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.3
[2.0.2]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.2
[2.0.1]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.1
[2.0.0]: https://github.com/khral07/ha-taphome-lokal/releases/tag/2.0.0
[1.1.0]: https://github.com/khral07/ha-taphome-lokal/releases/tag/1.1.0
[1.2.0]: https://github.com/khral07/ha-taphome-lokal/releases/tag/1.2.0
[1.0.2]: https://github.com/khral07/ha-taphome-lokal/releases/tag/1.0.2
[1.0.1]: https://github.com/khral07/ha-taphome-lokal/releases/tag/1.0.1
