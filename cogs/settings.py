import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.checks import is_owner, is_admin

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
    
    @commands.group(name='jail', invoke_without_command=True)
    @is_owner()
    async def jail(self, ctx):
        await ctx.send("Use `.jail role <role>` or `.jail channel <channel>`")
    
    @jail.command(name='role')
    @is_owner()
    async def jail_role(self, ctx, role: discord.Role = None):
        if not role:
            await ctx.send("❌ Usage: `.jail role <role>`")
            return
        
        await self.config_manager.set_guild_config(ctx.guild.id, 'jail_role', role.id)
        await ctx.send(f"✅ Set jail role to {role.mention}")
    
    @jail.command(name='channel')
    @is_owner()
    async def jail_channel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            await ctx.send("❌ Usage: `.jail channel <channel>`")
            return
        
        await self.config_manager.set_guild_config(ctx.guild.id, 'jail_channel', channel.id)
        await ctx.send(f"✅ Set jail channel to {channel.mention}")
    
    @commands.group(name='antinuke', invoke_without_command=True)
    @is_owner()
    async def antinuke(self, ctx):
        await ctx.send("Use `.antinuke threshold <action> <count> <hours>`")
    
    @antinuke.command(name='threshold')
    @is_owner()
    async def antinuke_threshold(self, ctx, action: str = None, count: int = None, hours: int = None):
        if not action or count is None or hours is None:
            await ctx.send("❌ Usage: `.antinuke threshold <action> <count> <hours>`\n"
                          "Actions: ban, kick, role_delete, channel_delete, webhook_create")
            return
        
        valid_actions = ['ban', 'kick', 'role_delete', 'channel_delete', 'webhook_create']
        if action not in valid_actions:
            await ctx.send(f"❌ Invalid action. Choose from: {', '.join(valid_actions)}")
            return
        
        await self.config_manager.set_antinuke_threshold(ctx.guild.id, action, count, hours)
        await ctx.send(f"✅ Set anti-nuke threshold for {action}: {count} actions per {hours} hours")
    
    @commands.command(name='logperms')
    @is_admin()
    async def log_perms(self, ctx, log_type: str = None, role: discord.Role = None):
        if not log_type or not role:
            await ctx.send("❌ Usage: `.logperms <logtype> <role>`\n"
                          "Log types: messages, voice, roles, antinuke")
            return
        
        if log_type not in ['messages', 'voice', 'roles', 'antinuke']:
            await ctx.send("❌ Invalid log type. Choose from: messages, voice, roles, antinuke")
            return
        
        channel_id = await self.config_manager.get_log_channel(ctx.guild.id, log_type)
        if not channel_id:
            await ctx.send(f"❌ No log channel set for {log_type}")
            return
        
        log_channel = ctx.guild.get_channel(channel_id)
        if not log_channel:
            await ctx.send(f"❌ Log channel not found")
            return
        
        try:
            overwrites = log_channel.overwrites
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)
            await log_channel.edit(overwrites=overwrites)
            await ctx.send(f"✅ Granted {role.mention} access to {log_channel.mention}")
        except:
            await ctx.send("❌ Failed to update permissions")

async def setup(bot):
    await bot.add_cog(Settings(bot))
