import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import aiohttp

from .formatters import format_birth_date, format_date


@dataclass
class BaseStats:
    count: int
    meanScore: float


@dataclass
class CoverImage:
    large: Optional[str]
    color: Optional[str] = None


@dataclass
class DateModel:
    year: int = 0
    month: int = 0
    day: int = 0

    def __eq__(self, other) -> bool:
        return self.day == other.day and self.month == other.month and self.year == other.year

    def __str__(self) -> str:
        if not self.day:
            return str(self.year or "TBD?")
        return (
            format_date(self.day, self.month, self.year)
            if self.year
            else format_birth_date(self.day, self.month)
        )

    @property
    def humanize_date(self) -> str:
        if not (self.day and self.month):
            return str(self.year) if self.year else ""

        return f"{format_birth_date(self.day, self.month)} {self.year or ''}"


@dataclass
class ExternalSite:
    site: str
    url: str

    def __str__(self) -> str:
        return f"[{self.site}]({self.url})"


@dataclass
class MediaTitle:
    romaji: Optional[str]
    english: Optional[str]

    def __str__(self) -> str:
        return self.romaji or self.english or "Title ???"


@dataclass
class MediaTrailer:
    id: Optional[str]
    site: Optional[str]


@dataclass
class NotFound:
    message: str
    status: Optional[int] = None

    def __str__(self) -> str:
        return f"https://http.cat/{self.status}.jpg" if self.status else self.message


async def fetch_data(session: aiohttp.ClientSession, query: str, **kwargs) -> Dict[str, Any]:
    kwargs["page"] = 1
    if not kwargs.get("perPage"):
        kwargs["perPage"] = 15
    try:
        async with session.post(
            "https://graphql.anilist.co", json={"query": query, "variables": kwargs}
        ) as response:
            if response.status != 200:
                return {"status": response.status, "message": "An error occurred."}
            result: dict = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return {"status": 408, "message": "Operation timed out."}

    if err := result.get("errors"):
        return {"message": f"{err[0]['message']} (Status: {err[0]['status']})"}
    return result


GenreCollection: Sequence[str] = [
    "Action",
    "Adventure",
    "Comedy",
    "Drama",
    "Ecchi",
    "Fantasy",
    "Hentai",
    "Horror",
    "Mahou Shoujo",
    "Mecha",
    "Music",
    "Mystery",
    "Psychological",
    "Romance",
    "Sci-Fi",
    "Slice of Life",
    "Sports",
    "Supernatural",
    "Thriller",
]
