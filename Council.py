import json

from discord.ext import commands
from utils import embed_builder
from exceptions import NoActiveBillFound, AlreadyVoted
import discord
import aiofiles


class Council(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_bills = {}
        self.config = self.bot.config

    @commands.group(invoke_without_command=True)
    async def bill(self, ctx, *args):
        pass

    @bill.command()
    async def schedule(self, ctx, ):
        # schedule a poll
        pass

    async def bill_preview(self, ctx, bill_id: int, votes_hidden=True):
        bill = self.active_bills[bill_id]
        options = bill["options"]

        fields = [(option, "Votes hidden" if votes_hidden else options[option], True)
                  for option in options]

        footer = f"{sum(bill['votes'])} votes counted."

        await ctx.send(embed=embed_builder(ctx,
                                           title=bill["prompt"],
                                           description=f"Bill ID: {bill_id}",
                                           footer=footer,
                                           fields=fields))

    @bill.command()
    @commands.has_any_role("J MODE", "MODE", "Chairman")
    async def initiate(self, ctx, bill_id: int, prompt: str, *options):
        """Early version, id should be generated automatically"""
        self.active_bills[bill_id] = {"prompt": prompt, "options": {}, "votes": {}}

        for option in options:
            self.active_bills[bill_id]["options"].update({option: 0})

        await self.preview(ctx, bill_id)

    @bill.command()
    @commands.has_role("Council")
    async def preview(self, ctx, bill_id: int):
        if bill_id not in self.active_bills.keys():
            raise NoActiveBillFound
        else:
            await self.bill_preview(ctx, bill_id)

    @bill.command()
    #@is_councilor
    async def vote(self, ctx, bill_id, option_text: str):
        if bill_id not in self.active_bills.keys():
            raise NoActiveBillFound

        bill = self.active_bills[bill_id]
        votes = bill["votes"]

        if ctx.author.id in votes:
            raise AlreadyVoted

        votes.update({f"{ctx.author.id}": option_text})

        options = bill["options"]
        options[option_text] += 1

        await ctx.send(embed=embed_builder(ctx,
                                           title="You have voted successfully."))

    @bill.command()
    @commands.has_any_role("J MODE", "MODE", "Chairman")
    async def close(self, ctx, bill_id: int):
        """Logs the file and deactivates it"""
        bill = self.active_bills[bill_id]

        async with aiofiles.open("bills_log.json", "w+") as bills_log:
            logged_bills = json.loads(await bills_log.read())
            logged_bills.update(bill)
            await bills_log.write(json.dumps(logged_bills))

        del self.active_bills[bill_id]

    @bill.command()
    @commands.has_any_role("J MODE", "MODE", "Chairman")
    async def results(self, ctx, bill_id: int):
        if bill_id not in self.active_bills.keys():
            raise NoActiveBillFound
        else:
            await self.bill_preview(ctx, bill_id)

