from __future__ import annotations

from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class ChannelConfig:
    station_name: str = "SkyOne"
    display_name: str = "Sky One"
    channel_number: str = "101"


@dataclass(frozen=True)
class HwAccelConfig:
    enabled: bool = True
    type: str = "vaapi"
    device: str = "/dev/dri/renderD128"
    encoder: str = "h264_vaapi"


@dataclass(frozen=True)
class StreamProfile:
    container: str = "mpegts"
    video_codec: str = "h264"
    audio_codec: str = "aac"
    target_resolution: str = "1920x1080"
    target_fps: int = 25
    video_bitrate: str = "5000k"
    audio_bitrate: str = "160k"
    startup_buffer_seconds: int = 3


@dataclass(frozen=True)
class AppConfig:
    fs42_base_url: str = "http://192.168.10.252:4242"
    timezone: str = "Europe/London"
    schedule_timestamps: str = "UTC"
    bind_host: str = "0.0.0.0"
    bind_port: int = 8099
    public_base_url: str = "http://fs42stream.local:8099"
    media_root: str = "/mnt/media"
    brb_media: str = "/runtime/brb.jpg"
    schedule_refresh_seconds: int = 60
    request_timeout_seconds: int = 10
    channel: ChannelConfig = field(default_factory=ChannelConfig)
    profile: StreamProfile = field(default_factory=StreamProfile)
    hwaccel: HwAccelConfig = field(default_factory=HwAccelConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        channel = ChannelConfig(
            station_name=os.getenv("FS42STREAM_STATION", "SkyOne"),
            display_name=os.getenv("FS42STREAM_DISPLAY_NAME", "Sky One"),
            channel_number=os.getenv("FS42STREAM_CHANNEL_NUMBER", "101"),
        )
        profile = StreamProfile(
            target_resolution=os.getenv("FS42STREAM_TARGET_RESOLUTION", "1920x1080"),
            target_fps=int(os.getenv("FS42STREAM_TARGET_FPS", "25")),
            video_bitrate=os.getenv("FS42STREAM_VIDEO_BITRATE", "5000k"),
            audio_bitrate=os.getenv("FS42STREAM_AUDIO_BITRATE", "160k"),
            startup_buffer_seconds=int(os.getenv("FS42STREAM_STARTUP_BUFFER_SECONDS", "3")),
        )
        hwaccel = HwAccelConfig(
            enabled=os.getenv("FS42STREAM_HWACCEL", "true").lower() in {"1", "true", "yes", "on"},
            device=os.getenv("FS42STREAM_HWACCEL_DEVICE", "/dev/dri/renderD128"),
            encoder=os.getenv("FS42STREAM_HWACCEL_ENCODER", "h264_vaapi"),
        )
        return cls(
            fs42_base_url=os.getenv("FS42STREAM_FS42_URL", "http://192.168.10.252:4242").rstrip("/"),
            timezone=os.getenv("TZ", os.getenv("FS42STREAM_TIMEZONE", "Europe/London")),
            schedule_timestamps=os.getenv("FS42STREAM_SCHEDULE_TIMESTAMPS", "UTC"),
            bind_host=os.getenv("FS42STREAM_BIND_HOST", "0.0.0.0"),
            bind_port=int(os.getenv("FS42STREAM_BIND_PORT", "8099")),
            public_base_url=os.getenv("FS42STREAM_PUBLIC_BASE_URL", "http://fs42stream.local:8099").rstrip("/"),
            media_root=os.getenv("FS42STREAM_MEDIA_ROOT", "/mnt/media"),
            brb_media=os.getenv("FS42STREAM_BRB_MEDIA", "/runtime/brb.jpg"),
            channel=channel,
            profile=profile,
            hwaccel=hwaccel,
        )
