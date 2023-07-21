from __future__ import annotations
import asyncio

from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

import aiohttp
import dacite
from discord.utils import escape_markdown

from .base import MediaNotFound as NotFound
from ..constants import API_BASE, CDN_BASE

_MAP: Mapping[str, str] = {"tv": "TV", "movie": "Movie"}


@dataclass(slots=True)
class BaseCredits:
    adult: bool
    id: int
    origin_country: Optional[List[str]]
    name: Optional[str]
    original_name: Optional[str]
    title: Optional[str]
    original_title: Optional[str]
    episode_count: Optional[int]
    first_air_date: Optional[str]
    release_date: Optional[str]
    media_type: str

    @property
    def clean_title(self) -> str:
        return escape_markdown(self.title or self.name or "")

    @property
    def year(self) -> int:
        date = self.first_air_date or self.release_date
        return int(date.split("-")[0]) if date and "-" in date else 0

    @property
    def tmdb_url(self) -> str:
        return f"https://themoviedb.org/{self.media_type}/{self.id}"


@dataclass(slots=True)
class CastCredits(BaseCredits):
    character: Optional[str]

    @property
    def portray_as(self) -> str:
        if not self.character:
            return f"[{self.clean_title}]({self.tmdb_url})"
        return f"as {self.character} in [{self.clean_title}]({self.tmdb_url})"

    @property
    def pretty_format(self) -> str:
        return f"`{self.year or  ' ???'}`  ·  {self.portray_as} ({_MAP[self.media_type]})"


@dataclass(slots=True)
class CrewCredits(BaseCredits):
    department: Optional[str]
    job: Optional[str]

    @property
    def portray_as(self) -> str:
        if not self.job:
            return f"[{self.clean_title}]({self.tmdb_url})"
        return f"as {self.job} in [{self.clean_title}]({self.tmdb_url})"

    @property
    def pretty_format(self) -> str:
        return f"`{self.year or ' ???'}`  ·  {self.portray_as} ({_MAP[self.media_type]})"


@dataclass(slots=True)
class PersonCredits:
    cast: Optional[List[CastCredits]]
    crew: Optional[List[CrewCredits]]


@dataclass(slots=True)
class Person:
    id: int
    name: str
    gender: int
    adult: bool
    imdb_id: str
    biography: str
    known_for_department: str
    popularity: float
    birthday: Optional[str]
    deathday: Optional[str]
    place_of_birth: Optional[str]
    profile_path: Optional[str]
    homepage: Optional[str]
    combined_credits: Optional[PersonCredits]
    also_known_as: Optional[List[str]]

    @property
    def person_image(self) -> str:
        return f"{CDN_BASE}{self.profile_path}" if self.profile_path else ""

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        person_id: Any
    ) -> Person | NotFound:
        try:
            async with session.get(
                f"{API_BASE}/person/{person_id}",
                params={"api_key": api_key, "append_to_response": "combined_credits"}
            ) as resp:
                if resp.status in [401, 404]:
                    data = await resp.json()
                    return NotFound(**data)
                if resp.status != 200:
                    return NotFound("No results found.", resp.status)
                person_data: dict = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientConnectionError):
            return NotFound("Operation timed out!", 408)

        return dacite.from_dict(data_class=cls, data=person_data)
