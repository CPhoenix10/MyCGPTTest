from __future__ import annotations

from dataclasses import dataclass
from .config import AppConfig
from .schedule import PlayoutItem


@dataclass(frozen=True)
class FfmpegCommandBuilder:
    config: AppConfig

    def for_item(self, item: PlayoutItem, offset_seconds: float) -> list[str]:
        base = ["ffmpeg", "-hide_banner", "-nostdin"]
        if self.config.hwaccel.enabled and self.config.hwaccel.type == "vaapi":
            base += ["-hwaccel", "vaapi", "-vaapi_device", self.config.hwaccel.device]
        base += ["-re", "-ss", f"{offset_seconds:.3f}", "-i", item.path]
        return base + self._output_args()

    def brb_loop(self) -> list[str]:
        base = [
            "ffmpeg", "-hide_banner", "-nostdin", "-loop", "1", "-re", "-i", self.config.brb_media,
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-shortest",
        ]
        return base + self._output_args()

    def _output_args(self) -> list[str]:
        width, height = self.config.profile.target_resolution.split("x", 1)
        if self.config.hwaccel.enabled and self.config.hwaccel.type == "vaapi":
            video = [
                "-vf", f"format=nv12,hwupload,scale_vaapi=w={width}:h={height}",
                "-c:v", self.config.hwaccel.encoder,
            ]
        else:
            video = [
                "-vf", (
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                    f"fps={self.config.profile.target_fps},format=yuv420p"
                ),
                "-c:v", "libx264", "-preset", "veryfast",
            ]
        return [
            "-map", "0:v:0", "-map", "0:a:0?",
            *video,
            "-b:v", self.config.profile.video_bitrate,
            "-maxrate", self.config.profile.video_bitrate,
            "-bufsize", "10000k",
            "-c:a", self.config.profile.audio_codec,
            "-ac", "2", "-ar", "48000", "-b:a", self.config.profile.audio_bitrate,
            "-f", self.config.profile.container,
            "pipe:1",
        ]
