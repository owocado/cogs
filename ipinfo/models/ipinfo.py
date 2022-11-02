from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .ipdata import ASN


@dataclass
class Company:
    name: str
    domain: Optional[str] = None
    type: Optional[str] = None

    def __str__(self) -> str:
        msg = self.name
        if self.domain:
            msg += f"\n(domain: {self.domain})"
        if self.type:
            msg += f"\n(Type: `{self.type.upper()}`)"
        return msg


@dataclass
class Privacy:
    vpn: bool
    proxy: bool
    tor: bool
    relay: bool
    hosting: bool
    service: Optional[str] = None


@dataclass
class Abuse:
    address: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    network: Optional[str] = None
    phone: Optional[str] = None

    def __str__(self) -> str:
        # return json.dumps(self.__dict__, indent=4)
        msg = f'{self.address or ""}\n'
        if self.name:
            msg += f"{self.name} ({self.email or 'E-mail: N/A'})\n"
        if self.network:
            msg += f"CIDR: {self.network}\n"
        if self.phone:
            msg += f"Phone: {self.phone}"
        return msg


@dataclass
class IPInfoIO:
    ip: str
    hostname: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    loc: Optional[str]
    org: Optional[str]
    postal: Optional[str]
    timezone: Optional[str]
    asn: Optional[ASN]
    company: Optional[Company]
    privacy: Optional[Privacy]
    abuse: Optional[Abuse]

    @classmethod
    def from_data(cls, data: dict) -> IPInfoIO:
        _ = data.pop("domains", {})
        asn = data.pop("asn", {})
        company = data.pop("company", {})
        privacy = data.pop("privacy", {})
        abuse = data.pop("abuse", {})
        return cls(
            ip=data["ip"],
            hostname=data.pop("hostname", None),
            city=data.pop("city", None),
            region=data.pop("region", None),
            country=data.pop("country", None),
            loc=data.pop("loc", None),
            org=data.pop("org", None),
            postal=data.pop("postal", None),
            timezone=data.pop("timezone", None),
            asn=ASN(**asn) if asn else None,
            company=Company(**company) if company else None,
            privacy=Privacy(**privacy) if privacy else None,
            abuse=Abuse(**abuse) if abuse else None,
        )
