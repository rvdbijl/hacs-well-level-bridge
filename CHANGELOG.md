# Changelog

## v0.0.4

- Remove configurable token index parsing entirely.
- Parse only the numeric value immediately before the `Ft` unit.
- Add config-entry migration to remove legacy token-index options from existing entries.
- Average all parsed samples collected during each publish interval before updating the raw sensor and filter pipeline.

## v0.0.3

- Parse the numeric well-level value immediately before the `Ft` unit before falling back to token indexes.
- Keep token-index parsing as a compatibility fallback for alternate frame formats.

## v0.0.2

- Fix well frame parsing to match the previous Node-RED flow's literal-space token splitting.
- Prevent valid frames with repeated spaces from being rejected as `unparsable_frame`.

## v0.0.1

- Initial HACS-compatible release.
- Add a config-flow Home Assistant integration for a TCP serial-to-Ethernet well-level bridge.
- Add native raw and filtered distance sensors.
- Expose TCP, parser, moving-average, range, interval, sign inversion, and derivative rejection settings in the setup and options flows.
- Default to not connecting on start so the integration can be configured while Node-RED still owns the single-client TCP bridge.
