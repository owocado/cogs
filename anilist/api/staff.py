from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import dacite

from .base import CoverImage, DateModel, NotFound, fetch_data
from .character import MiniMediaNode, Name, PageInfo

if TYPE_CHECKING:
    from aiohttp import ClientSession


@dataclass(slots=True)
class Character:
    name: Name
    siteUrl: str


@dataclass(slots=True)
class Edge:
    characterRole: Literal["MAIN", "SUPPORTING", "BACKGROUND"]
    node: MiniMediaNode
    characters: list[Character] = field(default_factory=list)

    @property
    def character(self) -> Character | None:
        return self.characters[0] if self.characters else None


@dataclass(slots=True)
class CharacterEdge:
    pageInfo: PageInfo
    edges: list[Edge] = field(default_factory=list)


@dataclass(slots=True)
class StaffData:
    name: Name
    image: CoverImage
    description: str | None
    siteUrl: str
    age: int | None
    gender: str | None
    yearsActive: list[int]
    homeTown: str | None
    primaryOccupations: list[str]
    dateOfBirth: DateModel
    dateOfDeath: DateModel
    language: str | None
    characterMedia: CharacterEdge | None

    @classmethod
    async def request(
        cls, session: ClientSession, query: str, **kwargs: Any
    ) -> NotFound | list[StaffData]:
        result = await fetch_data(session, query, **kwargs)
        if result.get("message"):
            return NotFound(**result)

        all_items = result.get("data", {}).get("Page", {}).get("staff", [])
        return (
            [dacite.from_dict(data=item, data_class=cls) for item in all_items]
            if all_items
            else NotFound("Sad trombone. No results!")
        )

