from __future__ import annotations
import asyncio

from dataclasses import dataclass, field
from typing import List, Optional

import aiohttp

from .base import API_BASE, CDN_BASE, MediaNotFound as NotFound


@dataclass
class BaseCredits:
    id: int
    media_type: str
    name: Optional[str] = None
    original_name: Optional[str] = None
    title: Optional[str] = None
    original_title: Optional[str] = None
    episode_count: Optional[int] = None
    first_air_date: Optional[str] = None
    release_date: Optional[str] = None
    origin_country: List[str] = field(default_factory=list)

    @property
    def year(self) -> str:
        date = self.first_air_date or self.release_date
        return date.split("-")[0] if date and "-" in date else ""


@dataclass
class CastCredits(BaseCredits):
    character: str = ""

    @property
    def portray_as(self) -> str:
        return f"as *{self.character}*" if self.character else ""

    @classmethod
    def from_data(cls, data: dict) -> CastCredits:
        for key in [
            "credit_id", "adult", "video", "original_language", "overview", "popularity",
            "order", "vote_average", "vote_count", "backdrop_path", "poster_path", "genre_ids"
        ]:
            data.pop(key, None)
        return cls(**data)


@dataclass
class CrewCredits(BaseCredits):
    department: str = ""
    job: str = ""

    @classmethod
    def from_data(cls, data: dict) -> CastCredits:
        for key in [
            "credit_id", "adult", "video", "original_language", "overview", "popularity",
            "order", "vote_average", "vote_count", "backdrop_path", "poster_path", "genre_ids"
        ]:
            data.pop(key, None)
        return cls(**data)


@dataclass
class PersonCredits:
    cast: List[CastCredits] = field(default_factory=list)
    crew: List[CrewCredits] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> PersonCredits:
        cast_data = data.pop("cast", [])
        crew_data = data.pop("crew", [])
        cast_data.sort(
            key=lambda x: x.get('release_date', '') or x.get('first_air_date', ''),
            reverse=True
        )
        crew_data.sort(
            key=lambda x: x.get('release_date', '') or x.get('first_air_date', ''),
            reverse=True
        )
        return cls(
            cast=[CastCredits.from_data(csc) for csc in cast_data] if cast_data else [],
            crew=[CrewCredits.from_data(crw) for crw in crew_data] if crew_data else []
        )


@dataclass
class Person:
    id: int
    name: str
    gender: int
    adult: bool
    imdb_id: str
    biography: str
    known_for_department: str
    popularity: float
    birthday: Optional[str] = None
    deathday: Optional[str] = None
    place_of_birth: Optional[str] = None
    profile_path: Optional[str] = None
    homepage: Optional[str] = None
    combined_credits: Optional[PersonCredits] = None
    also_known_as: List[str] = field(default_factory=list)

    @property
    def person_image(self) -> str:
        return f"{CDN_BASE}{self.profile_path}" if self.profile_path else ""

    @classmethod
    def from_data(cls, data: dict) -> Person:
        credits = data.pop("combined_credits", {})
        return cls(combined_credits=PersonCredits.from_data(credits), **data)

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        api_key: str,
        person_id: str
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
                person_data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientConnectionError):
            return NotFound("Operation timed out!", 408)

        return cls.from_data(person_data)
