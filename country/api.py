from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence, Union

import aiohttp

from .iso3166 import ALPHA3_CODES


# credits to devon
def natural_size(value: int) -> str:
    if value < 1000:
        return str(value)

    units = ('', 'K', 'million', 'billion')
    power = int(math.log(max(abs(value), 1), 1000))
    return f"{value / (1000 ** power):.2f} {units[power]}"


@dataclass
class Currency:
    code: str
    name: str
    symbol: str

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


@dataclass
class Flags:
    svg: str
    png: str = ""

    def __str__(self) -> str:
        return self.png


@dataclass
class Language:
    name: str
    nativeName: str
    iso639_1: str
    iso639_2: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Translation:
    br: str
    pt: str
    nl: str
    hr: str
    fa: str
    de: str
    es: str
    fr: str
    ja: str
    it: str
    hu: str

    def __str__(self) -> str:
        return "\n".join(f":flag_{k} `[{k.upper()}]` {v}" for k, v in self.__dict__.items() if v)


@dataclass
class NotFound:
    status: int
    message: str

    def __str__(self) -> str:
        return f"{self.status} {self.message}"

    @property
    def image(self) -> str:
        return f"https://http.cat/{self.status}"


@dataclass
class RegionalBloc:
    name: str
    acronym: str
    otherAcronyms: Optional[Sequence[str]] = None
    otherNames: Sequence[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.name} ({self.acronym})"


@dataclass
class CountryData:
    name: str
    topLevelDomain: Sequence[str]
    alpha2Code: str
    alpha3Code: str
    callingCodes: Sequence[str]
    altSpellings: Sequence[str]
    subregion: str
    region: str
    population: int
    demonym: str
    timezones: Sequence[str]
    nativeName: str
    numericCode: str
    flags: Flags
    currencies: Sequence[Currency]
    languages: Sequence[Language]
    translations: Translation
    flag: str
    independent: bool
    area: Optional[float] = None
    borders: Sequence[str] = field(default_factory=list)
    capital: Optional[str] = None
    cioc: Optional[str] = None
    gini: Optional[float] = None
    latlng: Optional[Sequence[float]] = None
    regionalBlocs: Optional[Sequence[RegionalBloc]] = None

    @property
    def tld(self) -> str:
        return self.topLevelDomain[0] if self.topLevelDomain else ""

    @property
    def calling_codes(self) -> str:
        return ", ".join([f"+{c}" for c in self.callingCodes])

    @property
    def co_ords(self) -> str:
        return f"{', '.join(str(x) for x in self.latlng)}" if self.latlng else ""

    @property
    def png_flag(self) -> str:
        return str(self.flags)

    @property
    def inhabitants(self) -> str:
        return natural_size(self.population)

    @property
    def shared_borders(self) -> str:
        return ", ".join(ALPHA3_CODES.get(code, '???') for code in self.borders)

    @property
    def trade_blocs(self) -> str:
        if not self.regionalBlocs:
            return ""
        return ", ".join(str(bloc) for bloc in self.regionalBlocs)

    @classmethod
    def from_dict(cls, data: dict) -> CountryData:
        flags = data.pop("flags", {})
        currencies = data.pop("currencies", [])
        languages = data.pop("languages", [])
        translations = data.pop("translations", {})
        blocs = data.pop("regionalBlocs", [])
        return cls(
            flags=Flags(**flags),
            currencies=[Currency(**c) for c in currencies],
            languages=[Language(**l) for l in languages],
            translations=Translation(**translations),
            regionalBlocs=[RegionalBloc(**b) for b in blocs],
            **data,
        )

    @classmethod
    async def request(
        cls, session: aiohttp.ClientSession, country: str
    ) -> Union[Sequence[CountryData], NotFound]:
        try:
            async with session.get(f"https://restcountries.com/v2/name/{country}") as resp:
                if resp.status == 404:
                    err_data = await resp.json()
                    return NotFound(**err_data)
                if resp.status != 200:
                    return NotFound(status=resp.status, message="")
                data: Sequence[Dict[str, Any]] = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return NotFound(status=408, message="Request timeout!")

        return [cls.from_dict(d) for d in data]
