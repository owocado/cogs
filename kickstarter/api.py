from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

import aiohttp
from redbot.core.utils.chat_formatting import humanize_number


@dataclass
class Photo:
    key: str
    full: str
    ed: str
    med: str
    little: str
    small: str
    thumb: str
    h576: Optional[str]
    h864: Optional[str]

    def __str__(self) -> str:
        return self.h864 or self.h576 or self.full

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> Photo:
        return cls(h576=data.pop('1024x576', ''), h864=data.pop('1536x864', ''), **data)


@dataclass
class CreatorAvatar:
    thumb: str
    small: str
    medium: str


@dataclass
class URLs:
    web: Dict[str, str] = field(default_factory=dict)


@dataclass
class Creator:
    id: int
    name: str
    is_registered: Optional[bool]
    is_email_verified: Optional[bool]
    chosen_currency: Optional[str]
    is_superbacker: Optional[bool]
    avatar: CreatorAvatar
    slug: str = ""
    urls: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def __str__(self) -> str:
        if self.urls.get('web'):
            return f"[{self.name}]({self.urls['web']['user']})"
        return self.name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Creator:
        avatar = data.pop('avatar', {})
        return cls(avatar=CreatorAvatar(**avatar), **data)


@dataclass
class Location:
    id: int
    name: str
    slug: str
    short_name: str
    displayable_name: str
    localized_name: str
    country: str
    state: str
    type: str
    is_root: bool
    expanded_country: str
    urls: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class Category:
    id: int
    name: str
    analytics_name: str
    slug: str
    position: int
    color: int
    parent_id: int = 0
    parent_name: str = ""
    urls: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name or ''


@dataclass
class Profile:
    id: int
    project_id: int
    state: str
    state_changed_at: int
    show_feature_image: bool
    background_image_opacity: float
    should_show_feature_image_section: bool
    name: Optional[str] = None
    blurb: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    link_background_color: Optional[str] = None
    link_text_color: Optional[str] = None
    link_text: Optional[str] = None
    link_url: Optional[str] = None
    background_image_attributes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    feature_image_attributes: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class KickstarterProject:
    id: int
    name: str
    blurb: str
    goal: int
    pledged: int
    state: str
    slug: str
    disable_communication: bool
    country: str
    country_displayable_name: str
    currency: str
    currency_symbol: str
    currency_trailing_code: bool
    deadline: int
    state_changed_at: int
    created_at: int
    launched_at: int
    staff_pick: bool
    is_starrable: bool
    backers_count: int
    static_usd_rate: int
    usd_pledged: str
    converted_pledged_amount: int
    fx_rate: int
    usd_exchange_rate: int
    current_currency: str
    usd_type: str
    spotlight: bool
    creator: Creator
    photo: Optional[Photo]
    location: Optional[Location]
    category: Optional[Category]
    profile: Optional[Profile]
    urls: Optional[URLs] = None

    @property
    def who_created(self) -> str:
        return f"**Creator**:  {self.creator}"

    @property
    def project_goal(self) -> str:
        return f"{self.currency_symbol}{humanize_number(round(self.goal or 0))}"

    @property
    def pledged_till_now(self) -> str:
        pledged = f"{self.currency_symbol}{humanize_number(round(self.pledged))}"
        percent_funded = round((self.pledged / self.goal) * 100)
        return f"{pledged}\n({humanize_number(percent_funded)}% funded)"

    @property
    def when_created(self) -> str:
        return f"**Creation Date**: <t:{int(self.created_at)}:R>\n"

    @property
    def when_launched(self) -> str:
        return f"**Launched Date**: <t:{int(self.launched_at)}:R>\n"

    @property
    def when_deadline(self) -> str:
        deadline = datetime.now(timezone.utc).timestamp() > self.deadline
        past_or_future = "`**EXPIRED**`" if deadline else ""
        return f"**Deadline**: <t:{int(self.deadline)}:R> {past_or_future}\n"

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> KickstarterProject:
        photo=data.pop('photo', {})
        creator=data.pop('creator', {})
        location=data.pop('location', {})
        category=data.pop('category', {})
        profile=data.pop('profile', {})
        urls=data.pop('urls', {})
        return cls(
            photo=Photo.from_dict(photo) if photo else None,
            creator=Creator.from_dict(creator),
            location=Location(**location) if location else None,
            category=Category(**category) if category else None,
            profile=Profile(**profile) if profile else None,
            urls=URLs(**urls) if urls else None,
            **data
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, url: str
    ) -> NotFound | Sequence[KickstarterProject]:
        projects: Sequence[Dict[str, Any]] = []
        try:
            async with session.get(url=url) as resp:
                if resp.status != 200:
                    return NotFound(status=resp.status)
                data: Dict[str, Any] = await resp.json()
                projects = data.get('projects', [])
                if not projects:
                    return NotFound(suggestion=data['suggestion'])
        except (KeyError, asyncio.TimeoutError):
            return NotFound(status=408)

        return [cls.from_data(item) for item in projects]


@dataclass
class NotFound:
    status: int = 0
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        if match := self.suggestion:
            prompt = "If not, then either ignore or retry with correct query."
            return f"Maybe you meant...  **{match}**?\n{prompt}"
        return f"https://http.cat/{self.status}.jpg"
