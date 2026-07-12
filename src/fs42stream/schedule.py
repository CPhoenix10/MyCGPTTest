from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PlayoutItem:
    path: str
    start: datetime
    end: datetime
    offset_seconds: float = 0.0
    kind: str = "content"

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment < self.end

    def offset_at(self, moment: datetime) -> float:
        return self.offset_seconds + (moment - self.start).total_seconds()


@dataclass(frozen=True)
class ScheduleBlock:
    title: str
    start: datetime
    end: datetime
    raw: dict[str, Any]

    @property
    def xmltv_start(self) -> str:
        return self.start.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000")

    @property
    def xmltv_end(self) -> str:
        return self.end.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000")


def parse_fs42_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _pick_path(entry: dict[str, Any]) -> str | None:
    for key in ("path", "file", "filename", "media", "commercial", "bumper"):
        value = entry.get(key)
        if isinstance(value, str) and value.startswith("/"):
            return value
        if isinstance(value, dict):
            nested = _pick_path(value)
            if nested:
                return nested
    return None


def _pick_title(block: dict[str, Any]) -> str:
    for key in ("title", "show", "name", "program"):
        value = block.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            nested = value.get("title") or value.get("name")
            if isinstance(nested, str) and nested:
                return nested
    return "FieldStation42 Programme"


def blocks_from_fs42(payload: Any) -> list[ScheduleBlock]:
    records = payload if isinstance(payload, list) else payload.get("schedule", payload.get("blocks", []))
    blocks: list[ScheduleBlock] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        start_value = record.get("start") or record.get("start_time") or record.get("startTime")
        end_value = record.get("end") or record.get("end_time") or record.get("endTime")
        if not isinstance(start_value, str) or not isinstance(end_value, str):
            continue
        blocks.append(ScheduleBlock(_pick_title(record), parse_fs42_datetime(start_value), parse_fs42_datetime(end_value), record))
    return sorted(blocks, key=lambda block: block.start)


def playout_from_block(block: ScheduleBlock) -> list[PlayoutItem]:
    plan = block.raw.get("plan") or block.raw.get("content") or []
    if isinstance(plan, dict):
        plan = plan.get("items", [])
    items: list[PlayoutItem] = []
    for entry in plan if isinstance(plan, list) else []:
        if not isinstance(entry, dict):
            continue
        start_value = entry.get("start") or entry.get("start_time") or entry.get("startTime")
        end_value = entry.get("end") or entry.get("end_time") or entry.get("endTime")
        path = _pick_path(entry)
        if not path or not isinstance(start_value, str) or not isinstance(end_value, str):
            continue
        offset = float(entry.get("offset") or entry.get("offset_seconds") or 0)
        kind = str(entry.get("type") or entry.get("kind") or "content")
        items.append(PlayoutItem(path, parse_fs42_datetime(start_value), parse_fs42_datetime(end_value), offset, kind))
    return sorted(items, key=lambda item: item.start)


def item_at(items: list[PlayoutItem], moment: datetime) -> tuple[PlayoutItem, float] | None:
    utc_moment = moment.astimezone(timezone.utc)
    for item in items:
        if item.contains(utc_moment):
            return item, item.offset_at(utc_moment)
    return None
