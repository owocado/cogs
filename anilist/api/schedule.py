from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .base import CoverImage, ExternalSite, MediaTitle, MediaTrailer, fetch_data


@dataclass
class MediaNode:
    idMal: Optional[int]
    siteUrl: str
    title: MediaTitle
    coverImage: CoverImage
    duration: Optional[int]
    format: str
    isAdult: bool
    trailer: Optional[MediaTrailer]
    externalLinks: Sequence[ExternalSite] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        trailer = data.pop("trailer", None)
        ext_links = data.pop("externalLinks", [])
        return cls(
            title=MediaTitle(**data.pop("title", {})),
            coverImage=CoverImage(**data.pop("coverImage", {})),
            trailer=MediaTrailer(**trailer) if trailer else None,
            externalLinks=[ExternalSite(**site) for site in ext_links],
            **data,
        )


@dataclass
class ScheduleData:
    airingAt: int
    episode: int
    media: MediaNode

    @property
    def external_links(self) -> str:
        sites = " • ".join(map(str, self.media.externalLinks))
        if self.media.trailer and self.media.trailer.site == "youtube":
            sites += f" • [YouTube Trailer](https://youtu.be/{self.media.trailer.id})"
        if self.media.idMal:
            sites += f" • [MyAnimeList](https://myanimelist.net/anime/{self.media.idMal})"
        return sites

    @classmethod
    def from_data(cls, data: dict) -> MediaNode:
        return cls(media=MediaNode.from_data(data.pop("media", {})), **data)

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> str | Sequence[ScheduleData]:
        result = await fetch_data(session, query, **kwargs)
        if type(result) is str:
            return result

        all_items = result.get("data", {}).get("Page", {}).get("airingSchedules", [])
        if not all_items:
            return f"Sad trombone. No results!"

        return [cls.from_data(item) for item in all_items]
