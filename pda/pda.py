from random import choice

import discord
from redbot.core import Config, commands
from redbot.core.commands import Context

from .constants import *


class PDA(commands.Cog):
    """Do roleplay with your Discord friends or virtual strangers."""

    __author__ = "siu3334"
    __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 123456789987654321, force_registration=True)
        default_user = {
            "BAKA_TO": 0,
            "BAKA_FROM": 0,
            "BULLY_TO": 0,
            "BULLY_FROM": 0,
            "CUDDLE_TO": 0,
            "CUDDLE_FROM": 0,
            "FEED_TO": 0,
            "FEED_FROM": 0,
            "HIGHFIVE_TO": 0,
            "HIGHFIVE_FROM": 0,
            "HUG_TO": 0,
            "HUG_FROM": 0,
            "KILL_TO": 0,
            "KILL_FROM": 0,
            "KISS_TO": 0,
            "KISS_FROM": 0,
            "LICK_TO": 0,
            "LICK_FROM": 0,
            "NOM_TO": 0,
            "NOM_FROM": 0,
            "PAT_TO": 0,
            "PAT_FROM": 0,
            "POKE_TO": 0,
            "POKE_FROM": 0,
            "PUNCH_TO": 0,
            "PUNCH_FROM": 0,
            "SLAP_TO": 0,
            "SLAP_FROM": 0,
            "SMUG_TO": 0,
            "SMUG_FROM": 0,
            "TICKLE_TO": 0,
            "TICKLE_FROM": 0
        }
        self.config.register_member(**default_user)
        self.config.register_user(**default_user)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def hugs(self, ctx: Context, user: discord.Member):
        """Hug a user virtually on Discord!"""

        if user.id == ctx.me.id:
            message = f"Awwww thanks! So nice of you! *hugs {ctx.author.mention} back* 🤗"
            return await ctx.send(message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} hugs {user.mention}* 🤗"
            embed.set_image(url=str(choice(HUG)))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} One dOEs NOt SiMplY hUg THeIR oWn sELF!"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cuddle(self, ctx: Context, user: discord.Member):
        """Cuddles a user!"""

        if user.id == ctx.me.id:
            return await ctx.send(f"{ctx.author.name}, Awww thanks! Very kind of you. 😳")
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} cuddles {user.mention}*"
            embed.set_image(url=str(choice(CUDDLE)))
            return await ctx.send(content=message, embed=embed)
        else:
            message = (
                f"{ctx.author.mention} According to all known laws of roleplay, there is no way you "
                + "can cuddle yourself! Go cuddle with someone... or a pillow, if you're lonely like me. 😔"
            )
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def kiss(self, ctx: Context, user: discord.Member):
        """[NSFW] Kiss a user! Only allowed in NSFW channel."""

        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if user.id == ctx.me.id:
            message = f"Awwww! *kisses {ctx.author.mention} back!* 😘 🥰"
            return await ctx.send(message)

        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} kisses {user.mention}* 😘 🥰"
            embed.set_image(url=str(choice(KISS)))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} Congratulations, you just kissed yourself! LOL!!! 💋"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def lick(self, ctx: Context, user: discord.Member):
        """[NSFW] Licks a user! Only allowed in NSFW channel."""

        if not ctx.channel.is_nsfw():
            return await ctx.send("NSFW command blocked in non NSFW channel.")

        if user.id == ctx.me.id:
            message = f"{ctx.author.mention} You wanna lick a bot? Very horny!"
            return await ctx.send(message)

        embed = discord.Embed(colour=user.colour)
        if user.id != ctx.author.id:
            user = user
            message = f"> *{ctx.author.mention} licks {user.mention}* 😳"
        else:
            message = f"> {ctx.author.mention} Bravo, you just licked yourself. 👏"
        embed.set_image(url=choice(LICK))
        await ctx.send(content=message, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def slap(self, ctx: Context, user: discord.Member):
        """Slaps a user!"""

        if user.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} slaps {user.mention}*"
            embed.set_image(url=choice(SLAP))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"Don't slap yourself, you're precious! {ctx.author.mention}"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def pat(self, ctx: Context, user: discord.Member):
        """Pats a user!"""

        embed = discord.Embed(colour=user.colour)
        if user.id == ctx.me.id:
            message = f"> *{ctx.author.mention} pats {user.mention}*"
        else:
            message = f"> *{ctx.author.mention} pats themselves, I guess?*"
        embed.set_image(url=choice(PAT))
        await ctx.send(content=message, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def highfive(self, ctx: Context, user: discord.Member):
        """High-fives a user!"""

        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} high fives {user.mention}*"
            embed.set_image(url=choice(HIGHFIVE))
            await ctx.send(content=message, embed=embed)
        else:
            message = f"*{ctx.author.mention} high-fives themselves in mirror, I guess?"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def feed(self, ctx: Context, user: discord.Member):
        """Feeds a user!"""

        if user.id == ctx.me.id:
            message = f"OWO! Yummy food! Thanks {ctx.author.mention} :heart:"
            return await ctx.send(message)
        else:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} feeds {user.mention}*"
            embed.set_image(url=choice(FEED))
            await ctx.send(content=message, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def tickle(self, ctx: Context, user: discord.Member):
        """Tickles a user!"""

        if user.id == ctx.me.id:
            message = F"LOL. Tickling a bot now, are we? {ctx.author.mention} 🤣 🤡"
            return await ctx.send(message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} tickles {user.mention}*"
            embed.set_image(url=choice(TICKLE))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} tickling yourself is boring!"
            message += " Tickling others is more fun though. 😏"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def poke(self, ctx: Context, user: discord.Member):
        """Pokes a user!"""

        if user.id == ctx.me.id:
            message = f"Awwww! Hey there. *pokes {ctx.author.mention} back! touchy touchy*"
            return await ctx.send(message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} casually pokes {user.mention}*"
            embed.set_image(url=choice(POKE))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} self-poking is widely regarded as a bad move!"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def smug(self, ctx: Context, user: discord.Member = None):
        """Be smug towards someone!"""

        embed = discord.Embed(colour=ctx.author.colour)
        if not user:
            message = f"> *{ctx.author.mention} smugs at **@\u200bsomeone*** 😏"
        else:
            message = f"> *{ctx.author.mention} smugs at {user.mention}* 😏"
        embed.set_image(url=choice(SMUG))
        await ctx.send(content=message, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def bully(self, ctx: Context, user: discord.Member):
        """Bully a user!"""

        if user.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} bullies {user.mention}* 🤡"
            embed.set_image(url=choice(BULLY))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} Stop it. Get some help."
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def nom(self, ctx: Context, user: discord.Member):
        """Bite a user!"""

        if user.id == ctx.me.id:
            message = f"**OH NO!** _runs away_"
            return await ctx.send(message)
        embed = discord.Embed(colour=user.colour)
        if user.id != ctx.author:
            message = f"> *{ctx.author.mention} casually noms {user.mention}* :smiling_imp:"
        else:
            message = f"{ctx.author.mention} Waaaaaa! You bit yourself! Whyyyy?? 😭"
        embed.set_image(url=choice(BITE))
        await ctx.send(content=message, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def baka(self, ctx: Context, user: discord.Member):
        """Call a user BAKA with a GIF reaction!"""

        if user.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(message)
        if user.id != ctx.author:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} calls {user.mention} a BAKA bahahahahaha*"
            embed.set_image(url=choice(BAKA))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} You really are BAKA, stupid. 💩"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def kill(self, ctx: Context, user: discord.Member):
        """Kill a user with a GIF reaction!"""

        if user.id == ctx.me.id:
            message = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(content=message)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} tries to kill {user.mention}* 🇫"
            embed.set_image(url=choice(KILL))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"{ctx.author.mention} Seppukku is not allowed on my watch. 💀"
            await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def punch(self, ctx: Context, user: discord.Member):
        """Punch a user with a GIF reaction!"""

        if user.id == ctx.me.id:
            message = (
                ctx.author.mention
                + " tried to punch a bot but failed miserably"
                + " and they actually punched themselves instead."
                + " How disappointing LMFAO! 😂"
            )
            em = discord.Embed(colour=await ctx.embed_colour())
            em.set_image(url="https://media1.tenor.com/images/c20ffecdd8cca7f0ce9c4a670d5f7ff0/tenor.gif")
            return await ctx.send(content=message, embed=em)
        if user.id != ctx.author.id:
            embed = discord.Embed(colour=user.colour)
            message = f"> *{ctx.author.mention} {choice(PUNCH_MSG)} {user.mention}*"
            embed.set_image(url=choice(PUNCH))
            return await ctx.send(content=message, embed=embed)
        else:
            message = f"I uh ..... **{ctx.author.name}**, self harm doesn't sound so fun. Stop it, get some help."
            await ctx.send(message)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def cry(self, ctx: Context):
        """Let others know you feel like crying or just wanna cry."""
        embed = discord.Embed(colour=ctx.author.colour)
        embed.description = f"{ctx.author.mention} {choice(CRY_STRINGS)}"
        embed.set_image(url=choice(CRY))
        await ctx.send(embed=embed)
