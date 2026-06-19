# Changelog

## v0.0.1

- Initial HACS-compatible release.
- Add a config-flow Home Assistant integration for a TCP serial-to-Ethernet well-level bridge.
- Add native raw and filtered distance sensors.
- Expose TCP, parser, moving-average, range, interval, sign inversion, and derivative rejection settings in the setup and options flows.
- Default to not connecting on start so the integration can be configured while Node-RED still owns the single-client TCP bridge.
