import datetime
from aiofiles import os

from discord.ext import commands
import discord
from exceptions import UnknownCountry
from utils import embed_builder
import aiofiles
import json


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.country_flags = self.bot.country_flags

    @commands.hybrid_group()
    @commands.guild_only()
    async def config(self, ctx):
        pass

    @config.command(enabled=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def save(self, ctx):
        """Writes the current config object onto the file"""
        async with aiofiles.open("config.json", "w") as f:
            await f.write(json.dumps(self.config))

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_any_role("MODE", "J MODE", "Janitor", "Helper")
    async def flag(self, ctx, member: discord.Member, country: str):
        key_found = ""

        flags = self.country_flags
        country = country.lower()

        for key in flags.keys():
            if country in key.lower() or country == flags[key]["code"].lower() or country in flags[key]["aliases"]:
                key_found = key

        if not key_found:
            raise UnknownCountry
        
        role_name = key_found + " " + str(flags[key_found]["flag"])

        try:
            role = await commands.RoleConverter().convert(ctx, role_name)
        except commands.RoleNotFound:
            role = await ctx.guild.create_role(name=role_name)

        await member.add_roles(role)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Flag assignment successful",
                                           description=f"Member {member.display_name} assigned with the flag: {role.name}."))

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_any_role("MODE", "J MODE", "Janitor", "Helper")
    async def verify(self, ctx, member: discord.Member):
        verified_role = str(self.config["verified_role"])

        role = await commands.RoleConverter().convert(ctx, verified_role)

        await member.add_roles(role)

        await ctx.send(embed=embed_builder(ctx,
                                           title="Verification successful",
                                           description=f"Member {member.display_name} verified with the role: {role.name}."))

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx):
        await self.bot.tree.sync()

        await ctx.send(embed=embed_builder(ctx,
                                           title="Commands synchronized globally"))

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_role("MODE")
    async def clean_roles(self, ctx):
        to_remove = []

        for role in ctx.guild.roles:
            if role.id == 1061696622192509108:
                break
            if len(role.members) == 0:
                to_remove.append(role)

        role_list = ""

        for role in to_remove:
            role_list += " " + role.name
            if role != to_remove[-1]:
                role_list += ","

        await ctx.send(embed=embed_builder(ctx,
                                           title="Roles to remove",
                                           description=role_list))

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_role("MODE")
    async def clean_history(self, ctx):
        now = datetime.datetime.now()
        after = datetime.datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        guild_id = self.config["server_id"]

        guild = await self.bot.fetch_guild(guild_id)
        channels = await guild.fetch_channels()

        text_channels = []

        for channel in channels:
            if type(channel) is discord.TextChannel:
                text_channels.append(channel)

        total_count = 0

        log_string = ""
        deleted_count = 0

        banned_words = self.config["banned_words"].split(",")

        for channel in text_channels:
            count = 0
            print(f"Cleaning up the channel: {channel.name}...")
            async for message in channel.history(limit=None, after=after, before=now):

                content = message.content
                words = content.split()

                for word in words:
                    if word.lower() in banned_words or word.lower() + "s" in banned_words:
                        try:
                            msg_string = f"***************\nAuthor: {message.author.display_name} {message.author.id}" \
                                         f"\nChannel: {message.channel.name} {message.channel.id}\nDate: " \
                                         f"{message.created_at} Message ID: {message.id}\nBanned word: {word}" \
                                         f"\n---------------\n{message.content}\n"
                            if len(message.attachments) > 0:
                                msg_string += f"---------------\nAttachments: {str(message.attachments)}\n"

                            log_string += msg_string
                            deleted_count += 1

                            await message.delete()
                            print(f"Deleting message: {message.content}\nBanned word: {word}")

                        except Exception as e:
                            print(str(e))

                count += 1
                total_count += 1
                if count % 1000 == 0:
                    print(f"{count}")


        info_string = f"Number of deleted messages: {deleted_count}\n"

        print(f"{total_count} messages analyzed.")
        print(info_string)

        report_string = info_string + log_string
        report_filename = f"cleanup_{datetime.date.today()}.txt"

        # print(report_string)
        # print(type(report_string))

        async with aiofiles.open(file=report_filename, mode="w+", encoding="utf-8") as f:
            await f.write(report_string)
            print("!!")

        await ctx.send(file=discord.File(report_filename))
        await os.remove(report_filename)
