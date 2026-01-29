import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed
from utils.checks import is_owner
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.action_tracker = defaultdict(lambda: defaultdict(list))
    
    async def is_whitelisted(self, guild_id: int, user_id: int, user_roles: list) -> bool:
        whitelist = await self.config_manager.get_antinuke_whitelist(guild_id)
        
        if user_id in whitelist.get('users', []):
            return True
        
        for role in user_roles:
            if role.id in whitelist.get('roles', []):
                return True
        
        return False
    
    async def check_threshold(self, guild_id: int, user_id: int, action: str) -> bool:
        thresholds = await self.config_manager.get_antinuke_thresholds(guild_id)
        
        if action not in thresholds:
            return False
        
        threshold_config = thresholds[action]
        count_limit = threshold_config['count']
        time_window = timedelta(hours=threshold_config['hours'])
        
        now = datetime.utcnow()
        self.action_tracker[guild_id][f"{user_id}_{action}"] = [
            t for t in self.action_tracker[guild_id][f"{user_id}_{action}"]
            if now - t < time_window
        ]
        
        self.action_tracker[guild_id][f"{user_id}_{action}"].append(now)
        
        action_count = len(self.action_tracker[guild_id][f"{user_id}_{action}"])
        
        return action_count >= count_limit
    
    async def jail_user(self, guild: discord.Guild, member: discord.Member, reason: str):
        guild_config = await self.config_manager.get_guild_config(guild.id)
        jail_role_id = guild_config.get('jail_role')
        
        if not jail_role_id:
            return False
        
        jail_role = guild.get_role(jail_role_id)
        if not jail_role:
            return False
        
        try:
            roles_to_remove = [r for r in member.roles if r != guild.default_role and r != jail_role]
            await member.remove_roles(*roles_to_remove, reason=f"Anti-nuke jail: {reason}")
            await member.add_roles(jail_role, reason=f"Anti-nuke jail: {reason}")
            
            channel_id = await self.config_manager.get_log_channel(guild.id, 'antinuke')
            if channel_id:
                log_channel = guild.get_channel(channel_id)
                if log_channel:
                    embed = create_log_embed(
                        "🔒 Anti-Nuke Jail",
                        f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                        f"**Reason:** {reason}\n"
                        f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                        discord.Color.dark_red()
                    )
                    await log_channel.send(embed=embed)
            
            return True
        except Exception as e:
            print(f"Error jailing user: {e}")
            return False
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        try:
            await asyncio.sleep(1)
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    member = guild.get_member(executor.id)
                    if not member:
                        return
                    
                    if await self.is_whitelisted(guild.id, executor.id, member.roles):
                        return
                    
                    if await self.check_threshold(guild.id, executor.id, 'ban'):
                        await self.jail_user(guild, member, f"Mass ban detected ({entry.reason or 'No reason'})")
                    
                    break
        except Exception as e:
            print(f"Error in on_member_ban: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            await asyncio.sleep(1)
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    executor_member = member.guild.get_member(executor.id)
                    if not executor_member:
                        return
                    
                    if await self.is_whitelisted(member.guild.id, executor.id, executor_member.roles):
                        return
                    
                    if await self.check_threshold(member.guild.id, executor.id, 'kick'):
                        await self.jail_user(member.guild, executor_member, f"Mass kick detected ({entry.reason or 'No reason'})")
                    
                    break
        except Exception as e:
            print(f"Error in on_member_remove: {e}")
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        try:
            await asyncio.sleep(1)
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    executor_member = role.guild.get_member(executor.id)
                    if not executor_member:
                        return
                    
                    if await self.is_whitelisted(role.guild.id, executor.id, executor_member.roles):
                        return
                    
                    if await self.check_threshold(role.guild.id, executor.id, 'role_delete'):
                        await self.jail_user(role.guild, executor_member, f"Mass role deletion detected")
                    
                    break
        except Exception as e:
            print(f"Error in on_guild_role_delete: {e}")
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            await asyncio.sleep(1)
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    executor_member = channel.guild.get_member(executor.id)
                    if not executor_member:
                        return
                    
                    if await self.is_whitelisted(channel.guild.id, executor.id, executor_member.roles):
                        return
                    
                    if await self.check_threshold(channel.guild.id, executor.id, 'channel_delete'):
                        await self.jail_user(channel.guild, executor_member, f"Mass channel deletion detected")
                    
                    break
        except Exception as e:
            print(f"Error in on_guild_channel_delete: {e}")
    
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        try:
            await asyncio.sleep(1)
            webhooks = await channel.webhooks()
            
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_create):
                executor = entry.user
                
                if executor.bot:
                    continue
                
                executor_member = channel.guild.get_member(executor.id)
                if not executor_member:
                    continue
                
                if await self.is_whitelisted(channel.guild.id, executor.id, executor_member.roles):
                    continue
                
                if await self.check_threshold(channel.guild.id, executor.id, 'webhook_create'):
                    await self.jail_user(channel.guild, executor_member, f"Webhook spam detected")
                
                break
        except Exception as e:
            print(f"Error in on_webhooks_update: {e}")
    
    @commands.group(name='whitelist', invoke_without_command=True)
    @is_owner()
    async def whitelist(self, ctx):
        await ctx.send("Use `.whitelist add <@user/@role>` or `.whitelist remove <@user/@role>`")
    
    @whitelist.command(name='add')
    @is_owner()
    async def whitelist_add(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.add_antinuke_whitelist(ctx.guild.id, target.id, 'users')
            await ctx.send(f"✅ Added {target.mention} to anti-nuke whitelist")
        elif role:
            await self.config_manager.add_antinuke_whitelist(ctx.guild.id, role.id, 'roles')
            await ctx.send(f"✅ Added {role.mention} to anti-nuke whitelist")
        else:
            await ctx.send("❌ Please mention a user or role")
    
    @whitelist.command(name='remove')
    @is_owner()
    async def whitelist_remove(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.remove_antinuke_whitelist(ctx.guild.id, target.id, 'users')
            await ctx.send(f"✅ Removed {target.mention} from anti-nuke whitelist")
        elif role:
            await self.config_manager.remove_antinuke_whitelist(ctx.guild.id, role.id, 'roles')
            await ctx.send(f"✅ Removed {role.mention} from anti-nuke whitelist")
        else:
            await ctx.send("❌ Please mention a user or role")

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
