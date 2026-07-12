from __future__ import annotations

from datetime import datetime, timezone
import json
from urllib.parse import urlencode
from urllib.request import urlopen

from .config import AppConfig
from .schedule import ScheduleBlock, blocks_from_fs42


class FS42Client:
    def __init__(self, config: AppConfig):
        self.config = config

    def schedule(self, start: datetime, end: datetime) -> list[ScheduleBlock]:
        query = urlencode({
            "start": start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        })
        url = f"{self.config.fs42_base_url}/schedules/{self.config.channel.station_name}?{query}"
        with urlopen(url, timeout=self.config.request_timeout_seconds) as response:  # noqa: S310 - configured LAN service URL
            return blocks_from_fs42(json.loads(response.read().decode("utf-8")))
