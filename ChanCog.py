from discord.ext import commands
import discord


class ChanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config

    @commands.command(name="4thread")
    async def fourthread(self, ctx, board, request="top"):
        # displays either 10 random or top threads from a given board
        pass

    @commands.command(name="4chan")
    async def fourchan(self, ctx, board, request="top"):
        # displays either 10 random or top posts from a given board
        pass

    @commands.command(name="4pic")
    async def fourpic(self, ctx, board, request="top"):
        # displays either 10 random or top pics from a given board
        pass

