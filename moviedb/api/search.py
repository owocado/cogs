from __future__ import annotations

from dataclasses import dataclass
from operator import itemgetter
from typing import TYPE_CHECKING

import dacite
from redbot.core.utils.chat_formatting import humanize_list

from .base import BaseSearch, MediaNotFound, multi_search

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class PersonSearch:
    adult: bool
    id: int
    name: str
    gender: int
    media_type: str
    popularity: float
    known_for_department: str | None
    original_name: str | None
    profile_path: str | None
    known_for: list[MovieSearch | TVShowSearch]

    @property
    def famous_for(self) -> str:
        if not self.known_for:
            return ""
        return f"known for {humanize_list([x.title for x in self.known_for])}"

    @classmethod
    async def request(
        cls, session: ClientSession, api_key: str, query: str
    ) -> MediaNotFound | list[PersonSearch]:
        all_data = await multi_search(session, api_key, query)
        if not all_data:
            return MediaNotFound("No celebrity persons found from your query!")
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if media.get("media_type") == "person"]
        if not filtered_data:
            return MediaNotFound("❌ No celebrities found!", 404)

        # filtered_data.sort(key=itemgetter("name"))
        return [dacite.from_dict(data_class=cls, data=p) for p in filtered_data]


@dataclass(slots=True)
class MovieSearch(BaseSearch):
    title: str
    original_title: str
    release_date: str | None
    original_language: str
    video: bool | None
    adult: bool | None

    @classmethod
    async def request(
        cls, session: ClientSession, api_key: str, query: str
    ) -> MediaNotFound | list[MovieSearch]:
        all_data = await multi_search(session, api_key, query)
        if not all_data:
            return MediaNotFound("No movies found from given query!")
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if media.get("media_type") == "movie"]
        if not filtered_data:
            return MediaNotFound("❌ No movies found!", 404)

        # filtered_data.sort(key=itemgetter("release_date"), reverse=True)
        return [dacite.from_dict(data_class=cls, data=movie) for movie in filtered_data]


@dataclass(slots=True)
class TVShowSearch(BaseSearch):
    name: str
    original_name: str
    first_air_date: str | None
    original_language: str

    @property
    def title(self) -> str:
        return self.name or self.original_name

    @classmethod
    async def request(
        cls, session: ClientSession, api_key: str, query: str
    ) -> MediaNotFound | list[TVShowSearch]:
        all_data = await multi_search(session, api_key, query)
        if not all_data:
            return MediaNotFound("No TV shows found from given query!")
        if isinstance(all_data, MediaNotFound):
            return all_data
        filtered_data = [media for media in all_data if "first_air_date" in media]
        if not filtered_data:
            return MediaNotFound("❌ No TV shows found!", 404)

        filtered_data.sort(key=itemgetter("first_air_date"), reverse=True)
        return [dacite.from_dict(data_class=cls, data=tv) for tv in filtered_data]
