import aiohttp
import asyncio

from aiocache import cached, SimpleMemoryCache
from itertools import repeat
from math import floor
from random import choice

import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

cache = SimpleMemoryCache()

API_URL = "https://pokeapi.co/api/v2"
SEREBII = "https://www.serebii.net/pokedex-swsh"


class Pokebase(commands.Cog):
    """Search for various info about a Pokémon and related data."""

    __author__ = ["phalt", "siu3334 (<@306810730055729152>)"]
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.intro_gen = ["na", "rb", "gs", "rs", "dp", "bw", "xy", "sm", "ss"]
        self.intro_games = {
            "na": "None (Unknown)",
            "rb": "Red/Blue",
            "gs": "Gold/Silver",
            "rs": "Ruby/Sapphire",
            "dp": "Diamond/Pearl",
            "bw": "Black/White",
            "xy": "X/Y",
            "sm": "Sun/Moon",
            "ss": "Sword/Shield",
        }

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    def get_generation(self, pkmn_id: int):
        if pkmn_id > 898:
            return 0
        elif pkmn_id >= 810:
            return 8
        elif pkmn_id >= 722:
            return 7
        elif pkmn_id >= 650:
            return 6
        elif pkmn_id >= 494:
            return 5
        elif pkmn_id >= 387:
            return 4
        elif pkmn_id >= 252:
            return 3
        elif pkmn_id >= 152:
            return 2
        elif pkmn_id >= 1:
            return 1
        else:
            return 0

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_species_data(self, pkmn_id: int):
        try:
            async with self.session.get(
                API_URL + f"/pokemon-species/{pkmn_id}"
            ) as response:
                if response.status != 200:
                    return None
                species_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return species_data

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pokemon(self, ctx: Context, pokemon: str):
        """Search for various info for a Pokémon.

        You can search by name or ID of a Pokémon.
        ID refers to National Pokédex number.
        https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number
        """
        async with ctx.typing():
            try:
                async with self.session.get(
                    API_URL + f"/pokemon/{pokemon}"
                ) as response:
                    if response.status != 200:
                        await ctx.send(f"https://http.cat/{response.status}")
                        return
                    data = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            # pages = []
            embed = discord.Embed(colour=await ctx.embed_colour())
            embed.set_author(
                name=f"#{str(data.get('id')).zfill(3)} - {data.get('name').title()}",
                url=SEREBII + f"/{str(data.get('id')).zfill(3)}.shtml",
                icon_url=SEREBII + f"/icon/{str(data.get('id')).zfill(3)}.png",
            )
            embed.set_thumbnail(
                url=f"https://serebii.net/pokemon/art/{str(data.get('id')).zfill(3)}.png",
            )
            introduced_in = str(
                self.intro_games[self.intro_gen[self.get_generation(data.get("id", 0))]]
            )
            embed.add_field(name="Introduced In", value=introduced_in)
            humanize_height = (
                f"{floor(data.get('height', 0) * 3.94 // 12)}'"
                f"{floor(data.get('height', 0) * 3.94 // 12)}\""
                f" ({data.get('height') / 10} m.)"
            )
            embed.add_field(name="Height", value=humanize_height)
            humanize_weight = (
                f"{round(data.get('weight', 0) * 0.2205, 2)} lbs."
                f" ({data.get('weight') / 10} kgs.)"
            )
            embed.add_field(name="Weight", value=humanize_weight)
            embed.add_field(
                name="Types",
                value="\n".join(
                    x.get("type").get("name").title() for x in data.get("types")
                ),
            )

            species_data = await self.get_species_data(data.get("id"))
            if species_data:
                gender_rate = species_data.get("gender_rate")
                male_ratio = 100 - ((gender_rate / 8) * 100)
                female_ratio = (gender_rate / 8) * 100
                genders = {
                    "male": 0 if gender_rate == -1 else male_ratio,
                    "female": 0 if gender_rate == -1 else female_ratio,
                    "genderless": True if gender_rate == -1 else False,
                }
                final_gender_rate = (
                    "Genderless"
                    if genders["genderless"]
                    else f"♂️ {genders['male']}%  ♀️ {genders['female']}%"
                )
                embed.add_field(name="Gender Rate", value=final_gender_rate)
                embed.add_field(
                    name="Base Happiness",
                    value=f"{species_data.get('base_happiness', 0)} / 255",
                )
                embed.add_field(
                    name="Capture Rate",
                    value=f"{species_data.get('capture_rate', 0)} / 255",
                )

                genus = [
                    x.get("genus")
                    for x in species_data.get("genera")
                    if x.get("language").get("name") == "en"
                ]
                genus_text = "The " + genus[0]
                flavor_text = [
                    x.get("flavor_text")
                    for x in species_data.get("flavor_text_entries")
                    if x.get("language").get("name") == "en"
                ]
                flavor_text = (
                    choice(flavor_text)
                    .replace("\n", " ")
                    .replace("\f", " ")
                    .replace("\r", " ")
                )
                flavor_text = flavor_text
                embed.description = f"**{genus_text}**\n{flavor_text}"

            base_stats = {}
            for stat in data.get("stats"):
                base_stats[stat.get("stat").get("name")] = stat.get("base_stat")
            total_base_stats = sum(base_stats.values())

            pretty_base_stats = (
                f"`HP         : |{'█' * round((base_stats['hp'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['hp'] / 255) * 10) * 2)}|` **{base_stats['hp']}**"
                f"`Attack     : |{'█' * round((base_stats['attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['attack'] / 255) * 10) * 2)}|` **{base_stats['attack']}**"
                f"`Defense    : |{'█' * round((base_stats['defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['defense'] / 255) * 10) * 2)}|` **{base_stats['defense']}**"
                f"`Sp. Attack : |{'█' * round((base_stats['special-attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-attack'] / 255) * 10) * 2)}|` **{base_stats['special-attack']}**"
                f"`Sp. Defense: |{'█' * round((base_stats['special-defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-defense'] / 255) * 10) * 2)}|` **{base_stats['special-defense']}**"
                f"`Speed      : |{'█' * round((base_stats['speed'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['speed'] / 255) * 10) * 2)}|` **{base_stats['speed']}**"
                "`-----------------------------------`"
                f"Total      : |{'█' * round((total_base_stats / 1125) * 10) * 2}"
                f"{' ' * (20 - round((total_base_stats / 1125) * 10) * 2)}| **{total_base_stats}**"
            )
            embed.add_field(
                name="Base Stats (Base Form)", value=pretty_base_stats, inline=False
            )
            abilities = ""
            for ability in data.get("abilities"):
                abilities += "[{}](https://bulbapedia.bulbagarden.net/wiki/{}_(Ability)){}\n".format(
                    ability.get("ability").get("name").replace("-", " ").title(),
                    ability.get("ability")
                    .get("name")
                    .replace("-", " ")
                    .title()
                    .replace(" ", "_"),
                    " (Hidden Ability)" if ability.get("is_hidden") else "",
                )

            embed.add_field(name="Abilities", value=abilities, inline=False)
            await ctx.send(embed=embed)
