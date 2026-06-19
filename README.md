# Well Level Bridge

Home Assistant custom integration for reading a serial well-level sensor through a TCP serial-to-Ethernet bridge.

This integration is designed to replace a Node-RED flow that connects to a serial bridge, parses the well-level text stream, filters it, and exposes the result in Home Assistant.

## Important Cutover Note

The serial-to-Ethernet bridge supports only one TCP client at a time. Do not run Node-RED and this integration connected to the bridge simultaneously.

The integration defaults to **Connect on start: off** so it can be installed and configured safely while Node-RED is still running. During cutover, disable the Node-RED flow first, then enable **Connect on start** in this integration's options.

## Entities

The integration creates native Home Assistant sensors:

- `sensor.well_level_bridge_raw`
- `sensor.well_level_bridge_filtered`

Both sensors use:

- device class: `distance`
- state class: `measurement`
- unit: `ft`

The filtered sensor is the production-quality value. The raw sensor shows the parsed, sign-adjusted value before range and delta filtering.

## Filtering Behavior

The default settings mirror the existing Node-RED flow:

| Setting | Default |
| --- | --- |
| TCP host | `192.168.10.4` |
| TCP port | `9001` |
| Frame delimiter | `>>` |
| Primary token index | `6` |
| Fallback token index | `7` |
| Invert parsed value | `true` |
| Filtered update interval | `5` seconds |
| Moving average window | `200` samples |
| Minimum accepted filtered value | `-250 ft` |
| Maximum accepted filtered value | `-60 ft` |
| Maximum filtered delta | `5 ft` |

These settings are available in the initial setup flow and can be changed later from the integration's Options menu.

## Preserving Existing Well History

If your existing history is stored under `sensor.well_level`, do not immediately delete that entity or create a competing entity with the same name.

Recommended cutover:

1. Install this integration through HACS.
2. Add the integration with **Connect on start** disabled.
3. Confirm the entities are created as bridge-specific sensors.
4. Disable the Node-RED well-level flow.
5. Enable **Connect on start** in this integration's options.
6. Confirm `sensor.well_level_bridge_filtered` is updating correctly.
7. Remove or disable the old MQTT/YAML well-level sensor.
8. Rename `sensor.well_level_bridge_filtered` to `sensor.well_level` in Home Assistant's entity settings if you want future readings to continue under the existing visible entity ID.

Home Assistant recorder history and long-term statistics are tied to entity/statistic identity. The safest production endpoint remains the same visible entity ID: `sensor.well_level`.

## HACS Installation

1. Open HACS.
2. Go to **Integrations**.
3. Open the three-dot menu and choose **Custom repositories**.
4. Add:

   ```text
   https://github.com/rvdbijl/hacs-well-level-bridge
   ```

5. Select category **Integration**.
6. Install **Well Level Bridge**.
7. Restart Home Assistant when HACS prompts you.
8. Add the integration from **Settings -> Devices & services -> Add integration**.

## Updating

HACS tracks GitHub releases. New versions are published as tagged releases such as `v0.0.1`, with release notes in `release-notes/`.

## Troubleshooting

- If the integration cannot connect, confirm Node-RED is disconnected from the serial bridge.
- If values are unavailable, check that the frame delimiter and token indexes match the serial device output.
- If filtered values do not update but raw values do, inspect sensor attributes for `last_reject_reason`.
- Use **Connect on start: off** as a safe rollback position, then re-enable the Node-RED flow.
