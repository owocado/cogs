import discord
from redbot.core import Config, commands


class PDA(commands.Cog):
    """Do roleplay with your Discord friends or virtual strangers."""

    __author__ = "siu3334"
    __version__ = "0.0.1"

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
            "TICKLE_FROM": 0,
        }
        self.config.register_member(**default_user)
        self.config.register_user(**default_user)
