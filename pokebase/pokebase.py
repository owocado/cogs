import aiohttp
import asyncio

from aiocache import cached, SimpleMemoryCache
from math import floor
from random import choice

import discord
from redbot.core import commands
from redbot.core.commands import Context

cache = SimpleMemoryCache()

API_URL = "https://pokeapi.co/api/v2"


class Pokebase(commands.Cog):
    """Search for various info about a Pokémon and related data."""

    __author__ = ["phalt", "siu3334 (<@306810730055729152>)"]
    __version__ = "0.1.4"

    def format_help_for_context(self, ctx: Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.intro_gen = ["na", "rb", "gs", "rs", "dp", "bw", "xy", "sm", "ss"]
        self.intro_games = {
            "na": "Unknown",
            "rb": "Red/Blue\n(Gen. 1)",
            "gs": "Gold/Silver\n(Gen. 2)",
            "rs": "Ruby/Sapphire\n(Gen. 3)",
            "dp": "Diamond/Pearl\n(Gen. 4)",
            "bw": "Black/White\n(Gen. 5)",
            "xy": "X/Y\n(Gen. 6)",
            "sm": "Sun/Moon\n(Gen. 7)",
            "ss": "Sword/Shield\n(Gen. 8)",
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

    @cached(ttl=86400, cache=SimpleMemoryCache)
    async def get_evolution_chain(self, evo_url: str):
        try:
            async with self.session.get(evo_url) as response:
                if response.status != 200:
                    return None
                evolution_data = await response.json()
        except asyncio.TimeoutError:
            return None

        return evolution_data

    @commands.command()
    @cached(ttl=86400, cache=SimpleMemoryCache)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def pokemon(self, ctx: Context, pokemon: str):
        """Search for various info about a Pokémon.

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
                url=f"https://www.pokemon.com/us/pokedex/{data.get('name')}",
            )
            embed.set_thumbnail(
                url=f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{str(data.get('id')).zfill(3)}.png",
            )
            introduced_in = str(
                self.intro_games[self.intro_gen[self.get_generation(data.get("id", 0))]]
            )
            embed.add_field(name="Introduced In", value=introduced_in)
            humanize_height = (
                f"{floor(data.get('height', 0) * 3.94 // 12)} ft."
                f"{floor(data.get('height', 0) * 3.94 % 12)} in."
                f"\n({data.get('height') / 10} m.)"
            )
            embed.add_field(name="Height", value=humanize_height)
            humanize_weight = (
                f"{round(data.get('weight', 0) * 0.2205, 2)} lbs."
                f"\n({data.get('weight') / 10} kgs.)"
            )
            embed.add_field(name="Weight", value=humanize_weight)
            embed.add_field(
                name="Types",
                value="/".join(
                    x.get("type").get("name").title() for x in data.get("types")
                ),
            )

            species_data = await self.get_species_data(data.get("id"))
            if species_data:
                gender_rate = species_data.get("gender_rate")
                male_ratio = 100 - ((gender_rate / 8) * 100)
                female_ratio = (gender_rate / 8) * 100
                genders = {
                    "male": 0.0 if gender_rate == -1 else male_ratio,
                    "female": 0.0 if gender_rate == -1 else female_ratio,
                    "genderless": True if gender_rate == -1 else False,
                }
                final_gender_rate = ""
                if genders["genderless"]:
                    final_gender_rate += "Genderless"
                if genders["male"] != 0.0:
                    final_gender_rate += f"♂️ {genders['male']}%\n"
                if genders["female"] != 0.0:
                    final_gender_rate += f"♀️ {genders['female']}%"
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
                embed.description = f"**{genus_text}**\n\n{flavor_text}"

            if data.get("held_items"):
                held_items = ""
                for item in data.get("held_items"):
                    held_items += "{} ({}%)\n".format(
                        item.get("item").get("name").replace("-", " ").title(),
                        item.get("version_details")[0].get("rarity"),
                    )
                embed.add_field(name="Held Items", value=held_items)
            else:
                embed.add_field(name="Held Items", value="None")

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

            embed.add_field(name="Abilities", value=abilities)

            base_stats = {}
            for stat in data.get("stats"):
                base_stats[stat.get("stat").get("name")] = stat.get("base_stat")
            total_base_stats = sum(base_stats.values())

            pretty_base_stats = (
                f"`HP         : |{'█' * round((base_stats['hp'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['hp'] / 255) * 10) * 2)}|` **{base_stats['hp']}**\n"
                f"`Attack     : |{'█' * round((base_stats['attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['attack'] / 255) * 10) * 2)}|` **{base_stats['attack']}**\n"
                f"`Defense    : |{'█' * round((base_stats['defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['defense'] / 255) * 10) * 2)}|` **{base_stats['defense']}**\n"
                f"`Sp. Attack : |{'█' * round((base_stats['special-attack'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-attack'] / 255) * 10) * 2)}|` **{base_stats['special-attack']}**\n"
                f"`Sp. Defense: |{'█' * round((base_stats['special-defense'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['special-defense'] / 255) * 10) * 2)}|` **{base_stats['special-defense']}**\n"
                f"`Speed      : |{'█' * round((base_stats['speed'] / 255) * 10) * 2}"
                f"{' ' * (20 - round((base_stats['speed'] / 255) * 10) * 2)}|` **{base_stats['speed']}**\n"
                "`-----------------------------------`\n"
                f"`Total      : |{'█' * round((total_base_stats / 1125) * 10) * 2}"
                f"{' ' * (20 - round((total_base_stats / 1125) * 10) * 2)}|` **{total_base_stats}**\n"
            )
            embed.add_field(
                name="Base Stats (Base Form)", value=pretty_base_stats, inline=False
            )

            evolves_to = ""
            if species_data.get("evolution_chain"):
                evo_url = species_data.get("evolution_chain").get("url")
                evo_data = (
                    (await self.get_evolution_chain(evo_url))
                    .get("chain")
                    .get("evolves_to")
                )
                if evo_data:
                    evolves_to += " -> " + "/".join(
                        x.get("species").get("name").title() for x in evo_data
                    )
                if evo_data and evo_data[0].get("evolves_to"):
                    evolves_to += " -> " + "/".join(
                        x.get("species").get("name").title()
                        for x in evo_data[0].get("evolves_to")
                    )

            evolves_from = ""
            if species_data.get("evolves_from_species"):
                evolves_from += (
                    species_data.get("evolves_from_species").get("name").title()
                    + " -> "
                )
            embed.add_field(
                name="Evolution Chain",
                value=f"{evolves_from}**{data.get('name').title()}**{evolves_to}",
                inline=False,
            )

            await ctx.send(embed=embed)
