from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import aiohttp


@dataclass
class ASN:
    asn: str
    name: str
    route: str
    type: str
    domain: Optional[str]

    def __str__(self) -> str:
        return f"{self.name}\n(Type: {self.type.upper()})\n"


@dataclass
class Carrier:
    name: str
    mcc: str
    mnc: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Currency:
    code: str
    name: str
    symbol: str
    native: str
    plural: str

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


@dataclass
class Language:
    name: str
    code: str
    native: str

    def __str__(self) -> str:
        return f"{self.name} ({self.code.upper()})"


@dataclass
class TimeZone:
    name: Optional[str]
    abbr: Optional[str]
    offset: Optional[str]
    is_dst: Optional[bool]
    current_time: Optional[str]

    def __str__(self) -> str:
        if self.name and self.abbr:
            return f"{self.name} ({self.abbr})"
        return "N/A"


@dataclass
class Threat:
    is_tor: bool
    is_icloud_relay: bool
    is_proxy: bool
    is_datacenter: bool
    is_anonymous: bool
    is_known_attacker: bool
    is_known_abuser: bool
    is_threat: bool
    is_bogon: bool
    is_vpn: Optional[bool] = None
    blocklists: List[Blocklist] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(
            f"✅  IP {key.replace('_', ' ').title()}"
            for key, value in self.__dict__.items()
            if value and type(value) is bool
        ).replace("Tor", "TOR").replace("Icloud", "iCloud").replace('Is', 'is')

    @classmethod
    def from_dict(cls, data: dict) -> Threat:
        blocklists = data.pop("blocklists", [])
        return cls(blocklists=[Blocklist(**i) for i in blocklists], **data)


@dataclass
class Blocklist:
    name: str
    site: str
    type: str

    def __str__(self) -> str:
        return f"[{self.name}]({self.site})"


@dataclass
class ErrorMessage:
    message: str
    count: Optional[str] = None

    def __str__(self) -> str:
        return self.message


@dataclass
class IPData:
    ip: str
    is_eu: bool
    city: Optional[str]
    region: Optional[str]
    region_code: Optional[str]
    region_type: Optional[str]
    country_name: str
    country_code: str
    continent_name: str
    continent_code: str
    latitude: float
    longitude: float
    postal: Optional[str]
    calling_code: str
    flag: str
    emoji_flag: str
    emoji_unicode: str
    asn: Optional[ASN]
    carrier: Optional[Carrier]
    currency: Optional[Currency]
    time_zone: Optional[TimeZone]
    threat: Optional[Threat]
    count: str
    message: Optional[ErrorMessage] = None
    languages: List[Language] = field(default_factory=list)

    @property
    def country(self):
        return f"{self.emoji_flag} {self.country_name}\n({self.continent_name})"

    @property
    def co_ordinates(self):
        return f"{self.latitude:.6f}, {self.longitude:.6f}"

    @classmethod
    def from_json(cls, json: dict) -> IPData:
        asn = json.pop("asn", None)
        carrier = json.pop("carrier", None)
        currency = json.pop("currency", None)
        languages = json.pop("languages", [])
        timezone = json.pop("time_zone", None)
        threat = json.pop("threat", None)
        return cls(
            asn=ASN(**asn) if asn else None,
            carrier=Carrier(**carrier) if carrier else None,
            currency=Currency(**currency) if currency else None,
            languages=[Language(**i) for i in languages],
            time_zone=TimeZone(**timezone) if timezone else None,
            threat=Threat.from_dict(threat) if threat else None,
            **json,
        )

    @classmethod
    async def request(
        cls,
        session: aiohttp.ClientSession,
        ip: str,
        api_key: Optional[str] = None,
    ) -> Union[ErrorMessage, IPData]:
        image, bait, flakes, come = ("9cac2b3", "7b9ada7", "ba746e3", "c7c6179")
        snow, AKx7UEj, some, take = ("bd74cc8", "415cd36", "99182d1", "69af730")
        key = api_key or f"{come}{snow}{flakes}{take}{some}{bait}{image}{AKx7UEj}"

        url = f"https://api.ipdata.co/v1/{ip}?api-key={key}"
        try:
            async with session.get(url) as resp:
                cat = f"https://http.cat/{resp.status}.png"
                if resp.status in [400, 401, 403]:
                    err_data: Dict[str, str] = await resp.json()
                    cls.message = ErrorMessage(err_data['message'])
                    return cls.message
                elif resp.status != 200:
                    cls.message = ErrorMessage(message=cat)
                    return cls.message

                data: Dict[str, Any] = await resp.json()
        except asyncio.TimeoutError:
            return ErrorMessage(message="https://http.cat/408.png")

        return cls.from_json(data)
