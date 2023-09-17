from discord.ext import commands


class NoPrivateMessages(commands.CheckFailure):
    pass


class NoActiveBillFound(commands.CommandError):
    pass


class VotingError(commands.CommandError):
    pass


class AlreadyVoted(VotingError):
    pass

class ColorParsingFailure(commands.CommandError):
    pass


class UnknownCountry(commands.CommandError):
    pass


class InsufficientFunds(commands.CommandError):
    pass