from __future__ import annotations

from html import escape
from .config import AppConfig
from .schedule import ScheduleBlock


def render_m3u(config: AppConfig) -> str:
    stream_url = f"{config.public_base_url}/live/{config.channel.station_name}.ts"
    guide_url = f"{config.public_base_url}/guide.xml"
    return "\n".join([
        "#EXTM3U",
        f"#EXTM3U url-tvg=\"{guide_url}\"",
        (
            f"#EXTINF:-1 tvg-id=\"{config.channel.station_name}\" "
            f"tvg-name=\"{config.channel.display_name}\" "
            f"tvg-chno=\"{config.channel.channel_number}\",{config.channel.display_name}"
        ),
        stream_url,
        "",
    ])


def render_xmltv(config: AppConfig, blocks: list[ScheduleBlock]) -> str:
    channel_id = escape(config.channel.station_name)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tv generator-info-name="fs42stream">',
        f'  <channel id="{channel_id}">',
        f'    <display-name>{escape(config.channel.display_name)}</display-name>',
        f'    <display-name>{escape(config.channel.channel_number)}</display-name>',
        '  </channel>',
    ]
    for block in blocks:
        lines.extend([
            f'  <programme start="{block.xmltv_start}" stop="{block.xmltv_end}" channel="{channel_id}">',
            f'    <title>{escape(block.title)}</title>',
            '  </programme>',
        ])
    lines.append('</tv>')
    return "\n".join(lines) + "\n"
