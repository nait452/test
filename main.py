import discord
from discord.ext import commands
import asyncio
import traceback
import config

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name} ({bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')
    print('------')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"❌ You don't have permission to use this command.")
    else:
        print(f'Error in command {ctx.command}: {error}')
        traceback.print_exception(type(error), error, error.__traceback__)

async def load_cogs():
    cogs = [
        'cogs.logging',
        'cogs.antinuke',
        'cogs.moderation',
        'cogs.roles',
        'cogs.voicechannel',
        'cogs.roleplay',
        'cogs.settings',
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')
            traceback.print_exception(type(e), e, e.__traceback__)

async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
