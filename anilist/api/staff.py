from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .base import CoverImage, DateModel, MediaTitle, fetch_data
from .character import Name


@dataclass
class CharacterNode:
    siteUrl: str
    name: Name

    @classmethod
    def from_data(cls, data: dict) -> StaffNode:
        return cls(name=Name(**data.pop("name", {})), **data)


@dataclass
class StaffNode:
    format: str
    siteUrl: str
    status: str
    title: MediaTitle

    @classmethod
    def from_data(cls, data: dict) -> StaffNode:
        return cls(title=MediaTitle(**data.pop("title", {})), **data)


@dataclass
class StaffData:
    name: Name
    age: Optional[int]
    description: Optional[str]
    gender: Optional[str]
    homeTown: Optional[str]
    primaryOccupations: Sequence[str]
    siteUrl: str
    yearsActive: Sequence[int]
    dateOfBirth: DateModel
    dateOfDeath: DateModel
    image: CoverImage
    staff_media_nodes: Sequence[StaffNode] = field(default_factory=list)
    character_nodes: Sequence[CharacterNode] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> StaffData:
        characters = data.pop("characters", {}).get("nodes", [])
        staff_media = data.pop("staffMedia", {}).get("nodes", [])
        return cls(
            name=Name(**data.pop("name", {})),
            dateOfBirth=DateModel(**data.pop("dateOfBirth", {})),
            dateOfDeath=DateModel(**data.pop("dateOfDeath", {})),
            image=CoverImage(**data.pop("image", {})),
            character_nodes=[CharacterNode.from_data(char) for char in characters],
            staff_media_nodes=[StaffNode.from_data(media) for media in staff_media],
            **data,
        )

    @classmethod
    async def request(cls, session, query: str, **kwargs) -> str | Sequence[StaffData]:
        result = await fetch_data(session, query, **kwargs)
        if type(result) is str:
            return result

        all_items = result.get("data", {}).get("Page", {}).get("staff", [])
        if not all_items:
            return f"Sad trombone. No results!"

        return [cls.from_data(item) for item in all_items]
