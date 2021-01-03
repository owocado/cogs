from random import choice
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .constants import (
    BAKA,
    BITE,
    BULLY,
    CRY,
    CRY_STRINGS,
    CUDDLE,
    FEED,
    HIGHFIVE,
    HUG,
    KILL,
    KISS,
    LICK,
    PAT,
    POKE,
    PUNCH,
    PUNCH_MSG,
    SLAP,
    SMUG,
    TICKLE
)


class Roleplay(commands.Cog):
    """Interact with other users through public display of affection!"""

    def __init__(self, bot: Red):
        self.bot = bot

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data about users
        return {}

    # credits to jack1142
    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data about users
        pass

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def hugs(self, ctx: commands.Context, user: discord.Member):
        """hug a user!"""

        author = ctx.author
        if user == self.bot.user:
            msg = f"Awwww thanks! So nice of you! *hugs {author.mention} back* :hugging:"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} hugs {user.mention}* :hugging:"
            embed.set_image(url=str(choice(HUG)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} One dOEs NOt SiMplY hUg THeIR oWn sELF!"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def cuddle(self, ctx: commands.Context, user: discord.Member):
        """Cuddles a user!"""

        author = ctx.author

        if user == self.bot.user:
            return await ctx.send("Come come. We'll cuddle all day and night! :joy:")
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} cuddles {user.mention}*"
            embed.set_image(url=str(choice(CUDDLE)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} cuddling yourself sounds like a gay move LMFAO!"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def kiss(self, ctx: commands.Context, user: discord.Member):
        """Kiss a user!"""

        author = ctx.author

        if not ctx.message.channel.is_nsfw():
            await ctx.send(embed=await self._nsfw_check(ctx))
            return

        if user == self.bot.user:
            msg = f"*OwO! kisses {author.mention} back!* :kissing_heart: :smiling_face_with_3_hearts:"
            return await ctx.send(msg)

        if user is not ctx.author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} kisses {user.mention}* :kissing_heart: :smiling_face_with_3_hearts:"
            embed.set_image(url=str(choice(KISS)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} Congratulations, you kissed yourself! LOL!!! :kiss:"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def lick(self, ctx: commands.Context, user: discord.Member):
        """Licks a user!"""

        author = ctx.author

        if not ctx.message.channel.is_nsfw():
            await ctx.send(embed=await self._nsfw_check(ctx))
            return

        if user == self.bot.user:
            msg = f"{author.mention} You wanna lick a bot? Very horny!"
            return await ctx.send(msg)

        embed = discord.Embed(colour=user.colour)
        if user is not author:
            user = user
            msg = f"> *{author.mention} licks {user.mention}* :flushed:"
        else:
            user = author
            msg = f"> {author.mention} Bravo, you just licked yourself. \N{CLAPPING HANDS SIGN}\N{EMOJI MODIFIER FITZPATRICK TYPE-4}"
        embed.set_image(url=str(choice(LICK)))
        await ctx.send(content=msg, embed=embed)

    @commands.command(aliases=['spank'])
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def slap(self, ctx: commands.Context, user: discord.Member):
        """Slaps a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} slaps {user.mention}*"
            embed.set_image(url=str(choice(SLAP)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f":hugging: Don't slap yourself, you're precious! {author.mention}"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def pat(self, ctx: commands.Context, user: discord.Member):
        """Pats a user!"""

        author = ctx.author

        embed = discord.Embed(colour=user.colour)
        if user is not author:
            msg = f"> *{author.mention} pats {user.mention}*"
        else:
            msg = f"> *{author.mention} pats themselves, I guess?*"
        embed.set_image(url=str(choice(PAT)))
        await ctx.send(content=msg, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 120, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def highfive(self, ctx: commands.Context, user: discord.Member):
        """High-fives a user!"""

        author = ctx.author

        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} high-fives {user.mention}*"
            embed.set_image(url=str(choice(HIGHFIVE)))
            await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} please high-five someone other than you! Thanks."
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def feed(self, ctx: commands.Context, user: discord.Member):
        """Feeds a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = f"OWO! Yummy food! Thanks {author.mention} :heart:"
            return await ctx.send(msg)
        else:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} feeds {user.mention}*"
            embed.set_image(url=str(choice(FEED)))
            await ctx.send(content=msg, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def tickle(self, ctx: commands.Context, user: discord.Member):
        """Tickles a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = F"LMAO. Tickling a bot now, are we? {author.mention} :rofl: :clown:"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} tickles {user.mention}*"
            embed.set_image(url=str(choice(TICKLE)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} tickling yourself is boring!"
            msg += " Tickling others is more fun though. :smirk:"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def poke(self, ctx: commands.Context, user: discord.Member):
        """Pokes a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = f"Awwww! Hey there. *pokes {author.mention} back! touchy touchy*"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} casually pokes {user.mention}*"
            embed.set_image(url=str(choice(POKE)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} self-poking is widely regarded as a bad move!"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def smug(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """Be smug towards someone!"""

        author = ctx.author

        embed = discord.Embed(colour=author.colour)
        if not user:
            msg = f"> *{author.mention} smugs at @\u200bsomeone* :smirk:"
        else:
            msg = f"> *{author.mention} smugs at {user.mention}* :smirk:"
        embed.set_image(url=str(choice(SMUG)))
        await ctx.send(content=msg, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 120, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def bully(self, ctx: commands.Context, user: discord.Member):
        """Bully a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} bullies {user.mention}* :clown:"
            embed.set_image(url=str(choice(BULLY)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} Bullying yourself? What are you? Some emo kid?"
            await ctx.send(msg)

    @commands.guild_only()
    @commands.command(aliases=["bite"])
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def nom(self, ctx: commands.Context, user: discord.Member):
        """Bite a user!"""

        author = ctx.author

        if user == self.bot.user:
            msg = f"**OH NO!** _runs away_"
            return await ctx.send(msg)
        embed = discord.Embed(colour=user.colour)
        if user is not author:
            msg = f"> *{author.mention} casually noms {user.mention}* :smiling_imp:"
        else:
            msg = f"{author.mention} Waaaaaa! You bit yourself! Whyyyy?? :sob:"
        embed.set_image(url=str(choice(BITE)))
        await ctx.send(content=msg, embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def baka(self, ctx: commands.Context, user: discord.Member):
        """Call a user BAKA with a GIF reaction!"""

        author = ctx.author

        if user == self.bot.user:
            msg = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} calls {user.mention} a BAKA bahahahahaha*"
            embed.set_image(url=str(choice(BAKA)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} You really are BAKA, stupid. :poop:"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def kill(self, ctx: commands.Context, user: discord.Member):
        """Kill a user with a GIF reaction!"""

        author = ctx.author

        if user == self.bot.user:
            msg = "**Ｎ Ｏ   Ｕ**"
            return await ctx.send(content=msg)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} tries to kill {user.mention}* :regional_indicator_f:"
            embed.set_image(url=str(choice(KILL)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"{author.mention} Seppukku is not allowed on my watch. :skeleton:"
            await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def punch(self, ctx: commands.Context, user: discord.Member):
        """Punch a user with a GIF reaction!"""

        author = ctx.author

        if user == self.bot.user:
            msg = (
                author.mention
                + " tried to punch a bot but failed miserably"
                " and they actually punched themselves instead."
                " How disappointing LMFAO! :joy:"
            )
            em = discord.Embed(colour=await ctx.embed_colour())
            em.set_image(url="https://media1.tenor.com/images/c20ffecdd8cca7f0ce9c4a670d5f7ff0/tenor.gif")
            return await ctx.send(content=msg, embed=em)
        if user is not author:
            embed = discord.Embed(colour=user.colour)
            msg = f"> *{author.mention} {str(choice(PUNCH_MSG))} {user.mention}*"
            embed.set_image(url=str(choice(PUNCH)))
            return await ctx.send(content=msg, embed=embed)
        else:
            msg = f"I uh ..... **{author.display_name}**, self harm doesn't sound so fun. Stop it, get some help."
            await ctx.send(msg)

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.member)
    @commands.bot_has_permissions(embed_links=True)
    async def cry(self, ctx: commands.Context):
        """Let others know you feel like crying or just wanna cry."""

        author = ctx.author
        embed = discord.Embed(colour=author.colour)
        embed.description = f"{author.mention} {str(choice(CRY_STRINGS))}"
        embed.set_image(url=str(choice(CRY)))
        await ctx.send(embed=embed)

    # Credits to Predä. for this snippet
    async def _nsfw_check(self, ctx: commands.Context):
        """Message for Safe For Work (SFW) channels."""
        if not ctx.message.channel.is_nsfw():
            em = discord.Embed(
                title="\N{LOCK} NSFW command blocked in SFW channel.",
                color=0xAA0000,
            )
        return em
