import asyncio
from typing import Any, Dict, Optional

import discord
from aiohttp import ClientError, ClientSession

from .models import IPData, IPInfoIO


def make_embed(
    color: discord.Colour, data: IPData, ipinfo_data: Optional[IPInfoIO] = None
) -> discord.Embed:
    embed = discord.Embed(color=color)
    # embed.description = f"__**Threat Info:**__\n\n{data.threat}" if data.threat else ""
    embed.set_author(name=f"Info for IP: {data.ip}", icon_url=data.flag or "")
    if ipinfo_data and ipinfo_data.asn:
        embed.add_field(name="Carrier (ASN)", value=str(ipinfo_data.asn))
        if ipinfo_data.asn.route:
            embed.add_field(
                name="ASN Route",
                value=f"{ipinfo_data.asn.route}\n{ipinfo_data.asn.domain or ''}"
            )
    elif data.asn:
        embed.add_field(name="ASN Carrier", value=str(data.asn))
        embed.add_field(name="ASN Route", value=f"{data.asn.route}\n{data.asn.domain or ''}")
    if ipinfo_data and ipinfo_data.city:
        embed.add_field(name="City & Region", value=f"{ipinfo_data.city}\n{ipinfo_data.region or ''}")
    elif data.city:
        embed.add_field(name="City & Region", value=f"{data.city}\n{data.region or ''}")
    if data.country_name:
        embed.add_field(name="Country / Continent", value=data.country)
    if data.calling_code:
        embed.add_field(name="Calling Code", value=f"+{data.calling_code}")
    if ipinfo_data and (loc := ipinfo_data.loc):
        lat, long = loc.split(",")
        maps_link = f"[{loc}](https://www.google.com/maps?q={lat},{long})"
        embed.add_field(name="Geolocation", value=maps_link)
    elif (lat := data.latitude) and (long := data.longitude):
        maps_link = f"[{data.co_ordinates}](https://www.google.com/maps?q={lat},{long})"
        embed.add_field(name="Geolocation", value=maps_link)
    if ipinfo_data.company:
        embed.add_field(name="Company Info", value=str(ipinfo_data.company), inline=False)
    if ipinfo_data.abuse:
        embed.add_field(name="Abuse Contact", value=str(ipinfo_data.abuse), inline=False)
    if data.threat.blocklists:
        embed.add_field(
            name=f"In {len(data.threat.blocklists)} Blocklists",
            value=", ".join(str(b) for b in data.threat.blocklists),
            inline=False,
        )
    return embed


async def query_ipinfo(session: ClientSession, ip_address: str) -> Dict[str, Dict[str, Any]]:
    url = f"https://ipinfo.io/widget/demo/{ip_address}"
    h = {
        'content-type': 'application/json',
        'referer': 'https://ipinfo.io/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; M2101K6P) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
    }
    try:
        async with session.get(url, headers=h) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
    except (asyncio.TimeoutError, ClientError):
        return {}
    else:
        return data
