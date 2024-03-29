# goss_bot/src event_cog.py

import logging
from datetime import datetime
import traceback

from ..config import config, secret

import discord
import discord.ext.commands as dcmds
import discord_slash as dslash
import discord_slash.cog_ext as cog_ext

from .goss_cog_base import GossCogBase

class EventCog(GossCogBase):
    # Method called before regular command invoke
    @dcmds.Cog.listener()
    async def on_command(self, ctx: dcmds.Context):
        self.log.info(
            f"Command recieved: @{ctx.author} triggered '{ctx.command}' in #{ctx.channel} of '{ctx.guild}' with '{ctx.message.content}'")
    
    # Method called when a slash command is triggered
    @dcmds.Cog.listener()
    async def on_slash_command(self, ctx: dslash.SlashContext):
        self.log.info(f"Slash command recieved: @{ctx.author} triggered '{ctx.command}' in #{ctx.channel} of '{ctx.guild}'")

    #   Error handler for commands - See link below for original idea
    #   https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
    @dcmds.Cog.listener()
    async def on_command_error(self, ctx: dcmds.Context, error: Exception):
        #   First thing: pipe all errors to the console for logging using traceback
        self.log.info(f"Handling exception in command {ctx.command}: {error}")
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        #   Prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        #   Prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        # Errors to completely ignore without any extra processing
        ignored = (dcmds.CommandNotFound, )

        #   Check for original exceptions raised and sent to CommandInvokeError.
        #   If nothing is found, keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            self.log.info(f"Ignoring exception: {error}")
            return

        if isinstance(error, dcmds.UserInputError):        
            if isinstance(error, dcmds.MissingRequiredArgument):
                await ctx.reply(f"Missing arguments: `{error.param}`")
            else:
                await ctx.reply(f"Bad argument(s), error details: `{error}`")
                await ctx.send_help(ctx.command)

        elif isinstance(error, dcmds.CheckFailure):
            if isinstance(error, dcmds.MissingRole):
                await ctx.reply(f"You require the role `{error.missing_role.name}` to run this command.")
            elif isinstance(error, dcmds.NotOwner):
                pass # Silently fail if an ownership check fails
            else:
                await ctx.reply(f"A pre-command check failed: `{error}`")

        elif isinstance(error, dcmds.DisabledCommand):
            await ctx.reply(f'{ctx.command} has been disabled.')

        elif isinstance(error, dcmds.NoPrivateMessage):
            try:
                await ctx.author.reply(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        else:
            # All other errors not handled fall through to here, where we log the error in detail and alert the bot owner
            self.log.exception(f"Ignoring unhandled exception in {ctx.command}\n", exc_info=(type(error), error, error.__traceback__))
            # Let the bot owner know with a direct message
            await self.bot.owner.send(f"""Exception unhandled at `{datetime.now()}`:```python
{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```This was triggered by `{ctx.message.content}`""")

    # Error handler for general errors - See link below for some description
    # https://stackoverflow.com/a/43576760
    # Unfortunately this doesn't seem to be able to work from within cogs, meaning this would have to be
    # implemented in the bot class. Due to the organizational implications of this I am still deciding
    # if that is something I want to do. This may result in all event and error handling being moved into
    # the bot class instead of being it's own cog.
    @dcmds.Cog.listener()
    async def on_error(self, event: str, *args, **kwargs):
        self.log.exception(f"Error detected, event is '{event}', args is '{args}', kwargs is '{kwargs}'")
        await self.bot.owner.send(f"""Error detected at `{datetime.now()}`:```python
{''.join(traceback.format_exc())}```The event associated with this error was `{event}`""")