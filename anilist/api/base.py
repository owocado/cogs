import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from .formatters import format_birth_date, format_date

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass
class BaseStats:
    count: int
    meanScore: float | None


@dataclass(slots=True)
class CoverImage:
    large: str | None
    color: str | None


@dataclass(slots=True)
class DateModel:
    year: int | None
    month: int | None
    day: int | None

    def __eq__(self, other: Self) -> bool:
        return self.day == other.day and self.month == other.month and self.year == other.year

    def __str__(self) -> str:
        if not self.day:
            return str(self.year) if self.year else "TBD?"
        if self.day and self.month and self.year:
            return format_date(self.day, self.month, self.year)
        return format_birth_date(self.day, self.month)

    def is_null(self) -> bool:
        return self.year is None and self.month is None and self.day is None

    @property
    def humanize_date(self) -> str | None:
        """This gets relative timestamp and year if present; contrary to above"""
        if not self.day:
            return ""
        if not self.day and not self.month:
            return str(self.year) if self.year else None
        if self.day and self.month and self.year:
            return format_date(self.day, self.month, self.year, style="R")
        return f"{format_birth_date(self.day, self.month)} {self.year or ''}"


@dataclass(slots=True)
class ExternalSite:
    site: str
    url: str

    def __str__(self) -> str:
        return f"[{self.site}]({self.url})"


@dataclass(slots=True)
class MediaTitle:
    english: str | None
    romaji: str | None
    native: str | None
    userPreferred: str | None

    def __str__(self) -> str:
        if self.userPreferred:
            return self.userPreferred
        return self.english or self.romaji or "TITLE MISSING ???"


@dataclass(slots=True)
class MediaTrailer:
    id: str | None
    site: str | None


@dataclass(slots=True)
class NotFound:
    message: str
    status: int | None = None

    def __str__(self) -> str:
        return f"https://http.cat/{self.status}.jpg" if self.status else self.message


async def fetch_data(session: ClientSession, query: str, **kwargs: Any) -> dict[str, Any]:
    kwargs["page"] = 1
    if not kwargs.get("perPage"):
        kwargs["perPage"] = 20
    try:
        async with session.post(
            "https://graphql.anilist.co", json={"query": query, "variables": kwargs}
        ) as response:
            if response.status != 200:
                return {"status": response.status, "message": "An error occurred."}
            result: dict = await response.json()
    except Exception as exc:
        return {"status": 408, "message": str(exc)}

    if err := result.get("errors"):
        return {"message": f"{err[0]['message']} (Status: {err[0]['status']})"}
    return result
