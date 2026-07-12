# fs42stream

`fs42stream` is a design and implementation starter for mirroring a
FieldStation42 (FS42) wall-clock schedule into a Jellyfin-compatible live TV
stream.

The central constraint is **time correctness**: if FS42 schedules a programme at
09:00, a viewer who joins at 09:25 must land 25 minutes into the scheduled output
including bumps, commercials, and resume points. The stream must follow the FS42
schedule as the source of truth rather than drifting behind or running ahead.

## Proposed approach

* Query FS42's REST API for station summaries and detailed schedule blocks.
* Convert the current wall-clock time into the exact scheduled media segment and
  offset.
* Run a supervised FFmpeg process that emits a constant live stream clocked with
  `-re`, restarts at planned segment boundaries, and recovers from incompatible
  source files.
* Normalize output to a Jellyfin-friendly live MPEG-TS/HLS profile instead of
  exposing raw mixed-format media directly.
* Serve a stable `.m3u` tuner playlist for Jellyfin that points at fs42stream's
  live channel endpoints.

See [`docs/architecture.md`](docs/architecture.md) for the detailed design,
configuration model, and open questions.

## Initial defaults

The example configuration assumes the FS42 server is reachable at
`http://192.168.10.252:4242`, exposes a `SkyOne` / `Sky One` channel to
Jellyfin, treats FS42 schedule timestamps as UTC while the operator timezone is
`Europe/London`, reads shared NAS media directly at `/mnt/media`, and enables
VAAPI with `/dev/dri/renderD128` on the Proxmox LXC host. If FS42 or media
playout fails, the planned fallback is `/runtime/brb.jpg`.

## Status

This repository now includes a Python implementation scaffold for the service,
including environment-backed configuration, FS42 schedule parsing, wall-clock
playout lookup, Jellyfin M3U/XMLTV rendering, FFmpeg command construction, and a
minimal HTTP server. The remaining production step is wiring the supervised
FFmpeg byte stream into the live `.ts` response.
