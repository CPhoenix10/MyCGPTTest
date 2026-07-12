# fs42stream architecture notes

## Goal

Mirror the existing FieldStation42 station schedule as a stable live stream that
Jellyfin can consume from an M3U tuner playlist. FS42 remains the schedule source
of truth; fs42stream translates the schedule into a wall-clock-correct network
stream.

## Confirmed deployment assumptions

* FS42 API base URL: `http://192.168.10.252:4242`.
* Initial Jellyfin channel: FS42 station/network `SkyOne`, displayed as `Sky One`.
* FS42 schedule timestamps are treated as UTC; operator timezone is
  `Europe/London`.
* FS42 and fs42stream see the same NAS paths at `/mnt/media`, so no path rewrite
  is required initially.
* Jellyfin should receive one channel per FS42 station.
* Target profile favors compatibility with near-broadcast latency: H.264/AAC,
  MPEG-TS, 1080p output frame, and a small startup buffer.
* Source material is mostly SD, with some HD shows, and clients are expected to
  be 1080p capable.
* FS42 schedule plans should be trusted for programme, bump, commercial, and
  resume timings.
* XMLTV guide generation is required, even if it can mature after the first live
  streaming implementation.
* VAAPI is available inside the LXC at `/dev/dri/renderD128`.
* Any FS42, media, or playout failure should fall back to `/runtime/brb.jpg`.

## FS42 integration facts

The FS42 API is documented as a JSON REST API. Its default server settings are
`0.0.0.0:4242`, and detailed schedule blocks are expected from
`GET /schedules/{network_name}?start=YYYY-MM-DDTHH:MM:SS&end=YYYY-MM-DDTHH:MM:SS`.
Station discovery can use `GET /summary/stations`, while schedule summaries can
use `GET /summary/schedules` or `GET /summary/schedules/{network_name}`.

## Time model

1. Poll FS42 for the selected station schedule over a rolling lookahead window.
2. Convert all timestamps to UTC internally.
3. Locate the schedule block containing the current wall-clock instant.
4. Trust the block's FS42 `content` / `plan` entries as the exact linear playout
   timeline: main programme segments, bumpers, commercials, and resume offsets.
5. Seek FFmpeg to the segment offset that corresponds to the current wall-clock
   instant.
6. Emit live output at real time, not as fast as FFmpeg can transcode.
7. At every segment boundary, re-evaluate wall-clock time and the FS42 schedule
   before starting the next FFmpeg input. This prevents accumulated drift.

The stream should never depend on an unbounded ffconcat file for correctness.
Concat-like plans are fragile with tens of thousands of heterogeneous files and
can fail when codecs, containers, time bases, or stream layouts differ.

## Streaming strategy

### Recommended first target: MPEG-TS over HTTP

Jellyfin live TV tuners commonly accept M3U entries that point at MPEG-TS HTTP
streams. fs42stream exposes stable URLs such as:

```m3u
#EXTM3U
#EXTM3U url-tvg="http://fs42stream.local:8099/guide.xml"
#EXTINF:-1 tvg-id="SkyOne" tvg-name="Sky One" tvg-chno="101",Sky One
http://fs42stream.local:8099/live/SkyOne.ts
```

The server process owns FFmpeg and keeps the HTTP response open. If an input file
or FS42 call fails, the process should insert the `/runtime/brb.jpg` fallback and
immediately recalculate the correct wall-clock segment rather than stopping the
tuner.

### Output normalization

Because the source library has mixed containers, codecs, resolutions, audio
layouts, and timestamp behavior, fs42stream normalizes output:

* Video: H.264, 1920x1080 output frame, fixed frame rate, yuv420p-compatible
  software output or VAAPI-compatible hardware frames.
* Audio: AAC stereo, fixed 48 kHz sample rate.
* Container: MPEG-TS initially; HLS can be added later if Jellyfin behavior is
  better in the target installation.
* Timestamps: generated from wall clock, with monotonic PTS/DTS in the output.

This deliberately trades CPU/GPU work for player compatibility and predictable
transitions.

## Current implementation scaffold

The repository now includes these implementation pieces:

* `src/fs42stream/config.py`: environment-backed defaults for FS42, Sky One,
  UTC/London time handling, `/mnt/media`, `/runtime/brb.jpg`, and VAAPI.
* `src/fs42stream/fs42.py`: FS42 schedule client using the confirmed station.
* `src/fs42stream/schedule.py`: UTC datetime parsing, schedule block parsing,
  playout item extraction, and wall-clock offset lookup.
* `src/fs42stream/playlist.py`: Jellyfin M3U and XMLTV rendering.
* `src/fs42stream/ffmpeg.py`: software/VAAPI FFmpeg command construction and BRB
  fallback command construction.
* `src/fs42stream/server.py`: minimal HTTP server with health, M3U, XMLTV, and
  live endpoint placeholders.

## FFmpeg supervision

The production FFmpeg layer should be a supervisor, not one giant command:

* Probe every file before playback with `ffprobe` and cache stream metadata.
* Start each input with explicit seek offset and real-time pacing.
* Transcode each source into the normalized live profile.
* Detect EOF, non-zero exits, and stalls.
* Use `/runtime/brb.jpg` plus generated silent audio as a bridge while resolving
  failures or very short timing gaps.
* Recompute the next segment from schedule time after every transition.

Potential VAAPI profile for the Proxmox LXC render device:

```bash
ffmpeg -hide_banner -nostdin -hwaccel vaapi -vaapi_device /dev/dri/renderD128 \
  -re -ss <offset> -i <file> \
  -vf "format=nv12,hwupload,scale_vaapi=w=1920:h=1080" \
  -c:v h264_vaapi -b:v 5000k -maxrate 5000k -bufsize 10000k \
  -c:a aac -ac 2 -ar 48000 -b:a 160k \
  -f mpegts pipe:1
```

VAAPI remains configurable because LXC permissions, host drivers, and source
codec support can vary. A software fallback remains available.

## Remaining implementation work

1. Replace the placeholder live endpoint with a supervised FFmpeg process that
   streams bytes to the HTTP response.
2. Add schedule caching so FS42 outages can immediately trigger BRB fallback and
   then recover without restarting Jellyfin.
3. Expand multi-station support from the current single configured Sky One
   channel to one endpoint per FS42 station.
4. Harden plan parsing against the exact FS42 JSON shape observed from the live
   server.
5. Add integration tests with captured FS42 schedule JSON and synthetic media.
