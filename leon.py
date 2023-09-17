import discord
from discord.ext import commands
import os
from Main import Main
from Council import Council
from StatCog import StatCog
from Economy import Economy
from Management import Management
import json
from exceptions import NoPrivateMessages, NoActiveBillFound, UnknownCountry, InsufficientFunds
from utils import embed_builder
import random


class Leon(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("config.json", mode="r") as f:
            self.config = json.load(f)
        with open("country_flags.json", mode="r", encoding="utf-8") as f:
            self.country_flags = json.load(f)

    async def setup_hook(self):
        await bot.add_cog(Main(bot))
        #await bot.add_cog(Council(bot))
        await bot.add_cog(StatCog(bot))
        await bot.add_cog(Economy(bot))
        await bot.add_cog(Management(bot))

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_command_error(self, ctx, exception):
        errors = ['Error! Do not panic.',
                  'Whoops, something went wrong!',
                  'Bzz, zz... Failure!']

        title = None

        if isinstance(exception, commands.MemberNotFound):
            description = f"Couldn't find the member '{exception.argument}'."
        elif isinstance(exception, NoPrivateMessages):
            description = "This command only works on servers."
        elif isinstance(exception, NoActiveBillFound):
            description = "No active bill found with this ID."
        elif isinstance(exception, commands.MissingRole):
            description = f"'{exception.missing_role}' role is necessary to execute this command."
        elif isinstance(exception, commands.MissingAnyRole):
            description = f"Any of the roles '{exception.missing_roles} is necessary to execute this command.'"
        elif isinstance(exception, UnknownCountry):
            description = f"I dont know the country: {ctx.args}!"
        elif isinstance(exception, commands.MissingPermissions):
            description = "Insufficient permissions to execute this command."
        elif isinstance(exception, InsufficientFunds):
            title = "Transfer failure!"
            description = f"Insufficient funds on the account to make the transfer."
        else:
            description = "Some unhandled exception occurred. Contact the devs immediately!"
            print(exception)

        await ctx.send(embed=embed_builder(ctx,
                                           title=random.choice(errors) if title is None else title,
                                           description=description,
                                           color=discord.Colour.from_str(self.config["color_error"])))


prefix = os.getenv('PREFIX')
bot = Leon(command_prefix=[prefix], intents=discord.Intents.all())

#bot.remove_command('help')
token = os.getenv('TOKEN')
bot.run(token)
