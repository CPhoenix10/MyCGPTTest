from datetime import datetime, timezone

from fs42stream.config import AppConfig
from fs42stream.ffmpeg import FfmpegCommandBuilder
from fs42stream.playlist import render_m3u, render_xmltv
from fs42stream.schedule import blocks_from_fs42, item_at, parse_fs42_datetime, playout_from_block


def test_defaults_match_requested_installation():
    config = AppConfig()
    assert config.fs42_base_url == "http://192.168.10.252:4242"
    assert config.channel.station_name == "SkyOne"
    assert config.channel.display_name == "Sky One"
    assert config.timezone == "Europe/London"
    assert config.media_root == "/mnt/media"
    assert config.brb_media == "/runtime/brb.jpg"
    assert config.hwaccel.enabled is True
    assert config.hwaccel.device == "/dev/dri/renderD128"


def test_playlist_contains_jellyfin_channel_and_xmltv_url():
    playlist = render_m3u(AppConfig())
    assert "url-tvg=\"http://fs42stream.local:8099/guide.xml\"" in playlist
    assert "tvg-name=\"Sky One\"" in playlist
    assert "http://fs42stream.local:8099/live/SkyOne.ts" in playlist


def test_schedule_playout_uses_utc_offsets():
    payload = [{
        "title": "Example Show",
        "start": "2026-07-11T09:00:00Z",
        "end": "2026-07-11T09:30:00Z",
        "plan": [
            {
                "type": "show",
                "path": "/mnt/media/show.mkv",
                "start": "2026-07-11T09:00:00Z",
                "end": "2026-07-11T09:10:00Z",
                "offset_seconds": 0,
            },
            {
                "type": "commercial",
                "path": "/mnt/media/ad.mp4",
                "start": "2026-07-11T09:10:00Z",
                "end": "2026-07-11T09:11:00Z",
            },
        ],
    }]
    block = blocks_from_fs42(payload)[0]
    items = playout_from_block(block)
    current = item_at(items, parse_fs42_datetime("2026-07-11T09:05:30Z"))
    assert current is not None
    item, offset = current
    assert item.path == "/mnt/media/show.mkv"
    assert offset == 330


def test_xmltv_renders_programme_times():
    block = blocks_from_fs42([{
        "title": "Sky One Programme",
        "start": "2026-07-11T09:00:00Z",
        "end": "2026-07-11T10:00:00Z",
    }])[0]
    guide = render_xmltv(AppConfig(), [block])
    assert 'channel id="SkyOne"' in guide
    assert 'start="20260711090000 +0000"' in guide
    assert "Sky One Programme" in guide


def test_ffmpeg_vaapi_and_brb_commands():
    config = AppConfig()
    item = playout_from_block(blocks_from_fs42([{
        "start": "2026-07-11T09:00:00Z",
        "end": "2026-07-11T10:00:00Z",
        "plan": [{
            "path": "/mnt/media/show.mkv",
            "start": "2026-07-11T09:00:00Z",
            "end": "2026-07-11T10:00:00Z",
        }],
    }])[0])[0]
    builder = FfmpegCommandBuilder(config)
    command = builder.for_item(item, 25.0)
    assert command[:6] == ["ffmpeg", "-hide_banner", "-nostdin", "-hwaccel", "vaapi", "-vaapi_device"]
    assert "/dev/dri/renderD128" in command
    assert "h264_vaapi" in command
    assert "25.000" in command
    assert "/mnt/media/show.mkv" in command
    brb = builder.brb_loop()
    assert "/runtime/brb.jpg" in brb
