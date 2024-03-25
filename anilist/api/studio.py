from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import dacite

from .base import MediaTitle, NotFound, fetch_data
from .formatters import format_anime_status

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class StudioMedia:
    episodes: int | None
    format: str | None
    isAdult: bool
    siteUrl: str
    status: str
    title: MediaTitle

    def __str__(self) -> str:
        title = self.title.english or self.title.romaji
        return f"**[{title}]({self.siteUrl})**{' 🔞' if self.isAdult else ''}"

    @property
    def episodes_count(self) -> str:
        if self.format == "MOVIE":
            return ""
        return (
            f"  »  **{self.episodes}** {'episodes' if self.episodes > 1 else 'episode'}"
            if self.episodes
            else f"  »  `{format_anime_status(self.status)}`"
        )


@dataclass(slots=True)
class MediaNode:
    nodes: list[StudioMedia] = field(default_factory=list)


@dataclass(slots=True)
class StudioData:
    name: str
    favourites: int
    isAnimationStudio: bool
    siteUrl: str
    media: MediaNode

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any
    ) -> NotFound | list[StudioData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_studios = result.get("data", {}).get("Page", {}).get("studios", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_studios]
            if all_studios
            else NotFound("Sad trombone. No results!")
        )
