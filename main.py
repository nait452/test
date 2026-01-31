import discord
from discord.ext import commands
import os
import json
from pathlib import Path

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None

if not DISCORD_TOKEN or not OWNER_ID:
    print("❌ ERROR: Missing DISCORD_TOKEN or OWNER_ID in .env")
    exit()

def init_json_files():
    files = {
        "data/config.json": {"guilds": {}},
        "data/hardbans.json": {"hardbans": {}},
        "data/fake_perms.json": {"permissions": {}},
        "data/roleplay_gifs.json": {"gifs": {}},
        "data/vc_data.json": {"voice_channels": {}},
        "data/antinuke_data.json": {"whitelisted_users": [], "whitelisted_roles": [], "thresholds": {}, "warned_users": {}},
        "data/leveling_data.json": {},
        "data/economy_data.json": {},
        "data/warns_data.json": {},
        "data/mutes_data.json": {},
        "data/boosters_data.json": {}
    }
    for path, default in files.items():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f, indent=4)

async def load_cogs():
    cogs = [
        'cogs.logging',
        'cogs.antinuke',
        'cogs.moderation',
        'cogs.roles',
        'cogs.voicechannel',
        'cogs.roleplay',
        'cogs.settings',
        'cogs.leveling',
        'cogs.economy',
        'cogs.warns',
        'cogs.boosters',
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'✅ Loaded {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')

@bot.event
async def on_ready():
    print(f'✅ Bot is ready! Logged in as {bot.user.name} ({bot.user.id})')
    print(f'✅ Connected to {len(bot.guilds)} guilds')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=".ghelp"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        print(f'Error in command {ctx.command}: {error}')

async def main():
    async with bot:
        init_json_files()
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
