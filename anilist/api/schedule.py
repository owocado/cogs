from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from typing import TYPE_CHECKING, Any

import dacite

from .base import CoverImage, ExternalSite, MediaTitle, MediaTrailer, NotFound, fetch_data

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class MediaNode:
    idMal: int | None
    siteUrl: str
    title: MediaTitle
    coverImage: CoverImage
    duration: int | None
    format: str
    isAdult: bool
    trailer: MediaTrailer | None
    externalLinks: list[ExternalSite] = field(default_factory=list)


@dataclass(slots=True)
class ScheduleData:
    airingAt: int
    episode: int
    media: MediaNode

    @property
    def external_links(self) -> str:
        sites = StringIO()
        sites.write(" · ".join(map(str, self.media.externalLinks)))
        if self.media.trailer and self.media.trailer.site == "youtube":
            sites.write(f" · [YouTube Trailer](https://youtu.be/{self.media.trailer.id})")
        if self.media.idMal:
            sites.write(f" · [MyAnimeList](https://myanimelist.net/anime/{self.media.idMal})")
        output = sites.getvalue()
        sites.close()
        return output

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any,
    ) -> NotFound | list[ScheduleData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("airingSchedules", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_items]
            if all_items
            else NotFound("Sad trombone. No results!")
        )

