from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .base import MediaTitle, fetch_data
from .formatters import format_anime_status


@dataclass
class MediaNode:
    episodes: int
    format: str
    siteUrl: str
    status: str
    title: MediaTitle

    def __str__(self) -> str:
        return f"**[{self.title.english or self.title.romaji}]({self.siteUrl})**"

    @property
    def episodes_count(self) -> str:
        if self.format == "MOVIE":
            return ""
        if not self.episodes:
            return f"  »  `{format_anime_status(self.status)}`"

        return f"  »  **{self.episodes}** {'episodes' if self.episodes > 1 else 'episode'}"

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(title=MediaTitle(**data.pop("title", {})), **data)


@dataclass
class StudioData:
    name: str
    favourites: int
    isAnimationStudio: bool
    siteUrl: str
    media_nodes: Sequence[MediaNode] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> StudioData:
        nodes = data.pop("media", {}).get("nodes", [])
        return cls(media_nodes=[MediaNode.from_data(node) for node in nodes], **data)

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> str | Sequence[StudioData]:
        result = await fetch_data(session, query, **kwargs)
        if type(result) is str:
            return result

        all_studios = result.get("data", {}).get("Page", {}).get("studios", [])
        if not all_studios:
            return f"Sad trombone. No results!"

        return [cls.from_data(item) for item in all_studios]
