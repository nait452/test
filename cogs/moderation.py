import discord
from discord.ext import commands, tasks
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_owner, is_admin, has_fake_permission, hardban_permission
import config
from datetime import datetime, timedelta
import asyncio
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.unban_warnings = {}
        self.unmute_task.start()
    
    def cog_unload(self):
        self.unmute_task.cancel()
    
    def parse_duration(self, duration_str: str) -> int:
        if not duration_str:
            return None
        
        match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
        if not match:
            return None
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        return amount * multipliers.get(unit, 0)
    
    def format_duration(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"
    
    async def get_mutes_data(self, guild_id: int) -> dict:
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.MUTES_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'mutes': {}, 'config': {}}
            return data.get(str(guild_id), {'mutes': {}, 'config': {}})
    
    async def save_mutes_data(self, guild_id: int, guild_data: dict):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.MUTES_DATA_FILE)
            data[str(guild_id)] = guild_data
            await self.config_manager._write_json(config.MUTES_DATA_FILE, data)
    
    async def get_mute_role(self, guild: discord.Guild) -> discord.Role:
        guild_data = await self.get_mutes_data(guild.id)
        role_id = guild_data.get('config', {}).get('mute_role')
        
        if role_id:
            role = guild.get_role(role_id)
            if role:
                return role
        
        role = discord.utils.get(guild.roles, name="Muted")
        if role:
            return role
        
        return None
    
    async def create_mute_role(self, guild: discord.Guild) -> discord.Role:
        try:
            role = await guild.create_role(
                name="Muted",
                color=discord.Color.dark_grey(),
                reason="Auto-created mute role"
            )
            
            for channel in guild.channels:
                try:
                    if isinstance(channel, discord.TextChannel):
                        await channel.set_permissions(role, send_messages=False, add_reactions=False)
                    elif isinstance(channel, discord.VoiceChannel):
                        await channel.set_permissions(role, speak=False)
                except:
                    pass
            
            return role
        except Exception as e:
            print(f"Error creating mute role: {e}")
            return None
    
    async def add_mute(self, guild_id: int, user_id: int, muted_by: int, reason: str, expires: float = None):
        guild_data = await self.get_mutes_data(guild_id)
        
        if 'mutes' not in guild_data:
            guild_data['mutes'] = {}
        
        guild_data['mutes'][str(user_id)] = {
            'muted_by': muted_by,
            'reason': reason,
            'muted_at': datetime.utcnow().isoformat(),
            'expires': expires
        }
        
        await self.save_mutes_data(guild_id, guild_data)
    
    async def remove_mute(self, guild_id: int, user_id: int) -> bool:
        guild_data = await self.get_mutes_data(guild_id)
        
        if str(user_id) in guild_data.get('mutes', {}):
            del guild_data['mutes'][str(user_id)]
            await self.save_mutes_data(guild_id, guild_data)
            return True
        return False
    
    async def is_muted(self, guild_id: int, user_id: int) -> bool:
        guild_data = await self.get_mutes_data(guild_id)
        return str(user_id) in guild_data.get('mutes', {})
    
    @tasks.loop(minutes=1)
    async def unmute_task(self):
        current_time = datetime.utcnow().timestamp()
        
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.MUTES_DATA_FILE)
            
            for guild_id, guild_data in list(data.items()):
                mutes = guild_data.get('mutes', {})
                expired = []
                
                for user_id, mute_data in list(mutes.items()):
                    expires = mute_data.get('expires')
                    if expires and expires <= current_time:
                        expired.append(user_id)
                
                for user_id in expired:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        member = guild.get_member(int(user_id))
                        if member:
                            mute_role = await self.get_mute_role(guild)
                            if mute_role and mute_role in member.roles:
                                try:
                                    await member.remove_roles(mute_role, reason="Mute duration expired")
                                except:
                                    pass
                    
                    del mutes[user_id]
                
            await self.config_manager._write_json(config.MUTES_DATA_FILE, data)
    
    @unmute_task.before_loop
    async def before_unmute_task(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='ban')
    async def ban_user(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        if not member:
            await ctx.send("❌ Usage: `.ban <user> [reason]`")
            return
        
        if not ctx.author.guild_permissions.ban_members:
            if not await has_fake_permission(ctx, 'ban'):
                await ctx.send("❌ You don't have permission to ban members")
                return
        
        try:
            await member.ban(reason=f"Banned by {ctx.author}: {reason}")
            await ctx.send(f"✅ Banned {member.mention} | Reason: {reason}")
            
            channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
            if channel_id:
                log_channel = ctx.guild.get_channel(channel_id)
                if log_channel:
                    embed = create_log_embed(
                        "Member Banned",
                        f"**Moderator:** {ctx.author.mention}\n"
                        f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                        f"**Reason:** {reason}",
                        discord.Color.red()
                    )
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that user")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='kick')
    async def kick_user(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        if not member:
            await ctx.send("❌ Usage: `.kick <user> [reason]`")
            return
        
        if not ctx.author.guild_permissions.kick_members:
            if not await has_fake_permission(ctx, 'kick'):
                await ctx.send("❌ You don't have permission to kick members")
                return
        
        try:
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            await ctx.send(f"✅ Kicked {member.mention} | Reason: {reason}")
            
            channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
            if channel_id:
                log_channel = ctx.guild.get_channel(channel_id)
                if log_channel:
                    embed = create_log_embed(
                        "Member Kicked",
                        f"**Moderator:** {ctx.author.mention}\n"
                        f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                        f"**Reason:** {reason}",
                        discord.Color.orange()
                    )
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick that user")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='mute')
    async def mute_user(self, ctx, member: discord.Member = None, duration: str = None, *, reason: str = "No reason provided"):
        if not ctx.author.guild_permissions.moderate_members:
            if not await has_fake_permission(ctx, 'mute'):
                await ctx.send("❌ You don't have permission to mute members")
                return
        
        if not member:
            await ctx.send("❌ Usage: `.mute @user [duration] [reason]`\nDuration format: `1h`, `30m`, `2d`, or leave empty for indefinite")
            return
        
        if member.bot:
            await ctx.send("❌ You cannot mute bots")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ You cannot mute yourself")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You cannot mute someone with a higher or equal role")
            return
        
        mute_role = await self.get_mute_role(ctx.guild)
        
        if not mute_role:
            await ctx.send("⏳ Creating mute role...")
            mute_role = await self.create_mute_role(ctx.guild)
            if not mute_role:
                await ctx.send("❌ Failed to create mute role. Please create one manually or set one using `.mute role @role`")
                return
        
        if mute_role in member.roles:
            await ctx.send(f"❌ {member.mention} is already muted")
            return
        
        duration_seconds = self.parse_duration(duration) if duration else None
        expires = None
        duration_str = "indefinite"
        
        if duration_seconds:
            expires = datetime.utcnow().timestamp() + duration_seconds
            duration_str = self.format_duration(duration_seconds)
        elif duration and not duration_seconds:
            reason = f"{duration} {reason}".strip()
        
        try:
            await member.add_roles(mute_role, reason=f"Muted by {ctx.author}: {reason}")
            await self.add_mute(ctx.guild.id, member.id, ctx.author.id, reason, expires)
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                color=discord.Color.dark_grey()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Duration", value=f"`{duration_str}`", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
            
            channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
            if channel_id:
                log_channel = ctx.guild.get_channel(channel_id)
                if log_channel:
                    log_embed = create_log_embed(
                        "🔇 Member Muted",
                        f"**Moderator:** {ctx.author.mention}\n"
                        f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                        f"**Duration:** {duration_str}\n"
                        f"**Reason:** {reason}",
                        discord.Color.dark_grey()
                    )
                    await log_channel.send(embed=log_embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute that user")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='timeout')
    async def timeout_user(self, ctx, member: discord.Member = None, duration: str = None, *, reason: str = "No reason provided"):
        await self.mute_user(ctx, member, duration, reason=reason)
    
    @commands.command(name='unmute')
    async def unmute_user(self, ctx, member: discord.Member = None):
        if not ctx.author.guild_permissions.moderate_members:
            if not await has_fake_permission(ctx, 'mute'):
                await ctx.send("❌ You don't have permission to unmute members")
                return
        
        if not member:
            await ctx.send("❌ Usage: `.unmute @user`")
            return
        
        mute_role = await self.get_mute_role(ctx.guild)
        
        if not mute_role:
            await ctx.send("❌ No mute role configured")
            return
        
        if mute_role not in member.roles:
            await ctx.send(f"❌ {member.mention} is not muted")
            return
        
        try:
            await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
            await self.remove_mute(ctx.guild.id, member.id)
            
            await ctx.send(f"✅ Unmuted {member.mention}")
            
            channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
            if channel_id:
                log_channel = ctx.guild.get_channel(channel_id)
                if log_channel:
                    embed = create_log_embed(
                        "🔊 Member Unmuted",
                        f"**Moderator:** {ctx.author.mention}\n"
                        f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})",
                        discord.Color.green()
                    )
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute that user")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.group(name='muterole', invoke_without_command=True)
    @is_admin()
    async def muterole(self, ctx):
        mute_role = await self.get_mute_role(ctx.guild)
        if mute_role:
            await ctx.send(f"Current mute role: {mute_role.mention}\nUse `.muterole set @role` to change it")
        else:
            await ctx.send("No mute role configured. Use `.muterole set @role` to set one")
    
    @muterole.command(name='set')
    @is_admin()
    async def muterole_set(self, ctx, role: discord.Role = None):
        if not role:
            await ctx.send("❌ Usage: `.muterole set @role`")
            return
        
        guild_data = await self.get_mutes_data(ctx.guild.id)
        if 'config' not in guild_data:
            guild_data['config'] = {}
        guild_data['config']['mute_role'] = role.id
        await self.save_mutes_data(ctx.guild.id, guild_data)
        
        await ctx.send(f"✅ Set mute role to {role.mention}")
    
    @commands.command(name='hb')
    @hardban_permission()
    async def hardban(self, ctx, user: discord.User = None, *, reason: str = "No reason provided"):
        if not user:
            await ctx.send("❌ Usage: `.hb <user> <reason>`")
            return
        
        try:
            member = ctx.guild.get_member(user.id)
            if member:
                await member.ban(reason=f"Hardbanned by {ctx.author}: {reason}")
            else:
                await ctx.guild.ban(discord.Object(id=user.id), reason=f"Hardbanned by {ctx.author}: {reason}")
            
            await self.config_manager.add_hardban(ctx.guild.id, user.id, reason, ctx.author.id)
            await ctx.send(f"✅ Hardbanned {user.mention} | Reason: {reason}")
            
            channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
            if channel_id:
                log_channel = ctx.guild.get_channel(channel_id)
                if log_channel:
                    embed = create_log_embed(
                        "🔨 Member Hardbanned",
                        f"**Moderator:** {ctx.author.mention}\n"
                        f"**User:** {user.mention} ({user.name}#{user.discriminator} - {user.id})\n"
                        f"**Reason:** {reason}",
                        discord.Color.dark_red()
                    )
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban that user")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='unhb')
    @hardban_permission()
    async def unhardban(self, ctx, user: discord.User = None):
        if not user:
            await ctx.send("❌ Usage: `.unhb <user>`")
            return
        
        hardbans = await self.config_manager.get_hardbans(ctx.guild.id)
        
        if str(user.id) not in hardbans:
            await ctx.send(f"❌ {user.mention} is not hardbanned")
            return
        
        hardban_data = hardbans[str(user.id)]
        if hardban_data['banned_by'] != ctx.author.id and ctx.author.id != config.OWNER_ID and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You can only unhardban users you've hardbanned yourself")
            return
        
        try:
            await ctx.guild.unban(user, reason=f"Unhardbanned by {ctx.author}")
            await self.config_manager.remove_hardban(ctx.guild.id, user.id)
            await ctx.send(f"✅ Unhardbanned {user.mention}")
        except discord.NotFound:
            await self.config_manager.remove_hardban(ctx.guild.id, user.id)
            await ctx.send(f"✅ Removed {user.mention} from hardban list (they weren't banned)")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name='hblist')
    @hardban_permission()
    async def hardban_list(self, ctx, page: int = 1):
        hardbans = await self.config_manager.get_hardbans(ctx.guild.id)
        
        if not hardbans:
            await ctx.send("❌ No hardbanned users")
            return
        
        hardban_list = []
        for user_id, data in hardbans.items():
            try:
                user = await self.bot.fetch_user(int(user_id))
                banned_by = await self.bot.fetch_user(data['banned_by'])
                hardban_list.append(f"**{user.name}#{user.discriminator}** ({user_id})\nBanned by: {banned_by.name}#{banned_by.discriminator}\nReason: {data['reason']}\n")
            except:
                hardban_list.append(f"**Unknown User** ({user_id})\nBanned by: Unknown\nReason: {data['reason']}\n")
        
        paginated, total_pages = paginate_list(hardban_list, page, 5)
        
        if not paginated:
            await ctx.send(f"❌ Page {page} doesn't exist. Total pages: {total_pages}")
            return
        
        embed = discord.Embed(
            title=f"Hardbanned Users (Page {page}/{total_pages})",
            description='\n'.join(paginated),
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        try:
            hardbans = await self.config_manager.get_hardbans(guild.id)
            
            if str(user.id) in hardbans:
                await asyncio.sleep(1)
                
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                    if entry.target.id == user.id:
                        executor = entry.user
                        
                        if executor.bot:
                            return
                        
                        warning_key = f"{guild.id}_{executor.id}_{user.id}"
                        warning_count = self.unban_warnings.get(warning_key, 0)
                        
                        if warning_count == 0:
                            try:
                                await executor.send(f"⚠️ Hey buddy, the guy you just unbanned ({user.name}#{user.discriminator}) is hard banned... don't try to unban them!")
                            except:
                                pass
                            self.unban_warnings[warning_key] = 1
                        elif warning_count == 1:
                            try:
                                await executor.send(f"⚠️⚠️ If you do it again you'll get the wrath of god! Seriously, stop trying to unban {user.name}#{user.discriminator}!")
                            except:
                                pass
                            self.unban_warnings[warning_key] = 2
                        
                        await guild.ban(user, reason=f"Hardban re-applied (was unbanned by {executor})")
                        break
        except Exception as e:
            print(f"Error in on_member_unban: {e}")
    
    @commands.command(name='hbpermsadd')
    @is_owner()
    async def hbperms_add(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.add_hardban_perm(ctx.guild.id, target.id, 'users')
            await ctx.send(f"✅ Granted hardban permission to {target.mention}")
        elif role:
            await self.config_manager.add_hardban_perm(ctx.guild.id, role.id, 'roles')
            await ctx.send(f"✅ Granted hardban permission to {role.mention}")
        else:
            await ctx.send("❌ Please mention a user or role")
    
    @commands.command(name='hbpermsrem')
    @is_owner()
    async def hbperms_remove(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.remove_hardban_perm(ctx.guild.id, target.id, 'users')
            await ctx.send(f"✅ Removed hardban permission from {target.mention}")
        elif role:
            await self.config_manager.remove_hardban_perm(ctx.guild.id, role.id, 'roles')
            await ctx.send(f"✅ Removed hardban permission from {role.mention}")
        else:
            await ctx.send("❌ Please mention a user or role")
    
    @commands.group(name='fakeperm', invoke_without_command=True)
    @is_owner()
    async def fakeperm(self, ctx):
        await ctx.send("Use `.fakeperm add/remove/list/check`")
    
    @fakeperm.command(name='add')
    @is_owner()
    async def fakeperm_add(self, ctx, target: discord.Member = None, role: discord.Role = None, *perms):
        if not perms:
            await ctx.send("❌ Usage: `.fakeperm add @user/@role <permissions>`\nExample: `.fakeperm add @user ban kick`")
            return
        
        if target:
            await self.config_manager.add_fake_perm(ctx.guild.id, target.id, 'users', list(perms))
            await ctx.send(f"✅ Added fake permissions to {target.mention}: {', '.join(perms)}")
        elif role:
            await self.config_manager.add_fake_perm(ctx.guild.id, role.id, 'roles', list(perms))
            await ctx.send(f"✅ Added fake permissions to {role.mention}: {', '.join(perms)}")
        else:
            await ctx.send("❌ Please mention a user or role")
    
    @fakeperm.command(name='remove')
    @is_owner()
    async def fakeperm_remove(self, ctx, target: discord.Member = None, role: discord.Role = None, *perms):
        if not perms:
            await ctx.send("❌ Usage: `.fakeperm remove @user/@role <permissions>`")
            return
        
        if target:
            await self.config_manager.remove_fake_perm(ctx.guild.id, target.id, 'users', list(perms))
            await ctx.send(f"✅ Removed fake permissions from {target.mention}: {', '.join(perms)}")
        elif role:
            await self.config_manager.remove_fake_perm(ctx.guild.id, role.id, 'roles', list(perms))
            await ctx.send(f"✅ Removed fake permissions from {role.mention}: {', '.join(perms)}")
        else:
            await ctx.send("❌ Please mention a user or role")
    
    @fakeperm.command(name='list')
    @is_owner()
    async def fakeperm_list(self, ctx, page: int = 1):
        fake_perms = await self.config_manager.get_fake_perms(ctx.guild.id)
        
        perm_list = []
        
        for user_id, perms in fake_perms.get('users', {}).items():
            user = ctx.guild.get_member(int(user_id))
            if user:
                perm_list.append(f"**User:** {user.mention}\n**Perms:** {', '.join(perms)}\n")
        
        for role_id, perms in fake_perms.get('roles', {}).items():
            role = ctx.guild.get_role(int(role_id))
            if role:
                perm_list.append(f"**Role:** {role.mention}\n**Perms:** {', '.join(perms)}\n")
        
        if not perm_list:
            await ctx.send("❌ No fake permissions configured")
            return
        
        paginated, total_pages = paginate_list(perm_list, page, 5)
        
        if not paginated:
            await ctx.send(f"❌ Page {page} doesn't exist. Total pages: {total_pages}")
            return
        
        embed = discord.Embed(
            title=f"Fake Permissions (Page {page}/{total_pages})",
            description='\n'.join(paginated),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @fakeperm.command(name='check')
    @is_owner()
    async def fakeperm_check(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.fakeperm check @user`")
            return
        
        fake_perms = await self.config_manager.get_fake_perms(ctx.guild.id)
        
        user_perms = fake_perms.get('users', {}).get(str(member.id), [])
        role_perms = []
        
        for role in member.roles:
            role_perms.extend(fake_perms.get('roles', {}).get(str(role.id), []))
        
        all_perms = list(set(user_perms + role_perms))
        
        if not all_perms:
            await ctx.send(f"❌ {member.mention} has no fake permissions")
            return
        
        embed = discord.Embed(
            title=f"Fake Permissions for {member.name}#{member.discriminator}",
            description=f"**Permissions:** {', '.join(all_perms)}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='ghelp')
    @is_admin()
    async def admin_help(self, ctx):
        embed = discord.Embed(
            title="🛡️ Admin Command Overview",
            description="Comprehensive list of all admin commands",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="**Moderation**",
            value="`.ban <user> [reason]` - Ban a user\n"
                  "`.kick <user> [reason]` - Kick a user\n"
                  "`.mute <user> [duration] [reason]` - Mute a user\n"
                  "`.unmute <user>` - Unmute a user\n"
                  "`.cls <amount>` - Bulk delete messages (max 100)",
            inline=False
        )
        
        embed.add_field(
            name="**Warning System**",
            value="`.warn @user [reason]` - Warn a user\n"
                  "`.warns @user` - View user warnings\n"
                  "`.removewarn @user <id>` - Remove a warning\n"
                  "`.clearwarn @user` - Clear all warnings\n"
                  "`.warn config threshold/action <value>`",
            inline=False
        )
        
        embed.add_field(
            name="**Hardban System (Owner)**",
            value="`.hb <user> <reason>` - Hardban a user\n"
                  "`.unhb <user>` - Remove hardban\n"
                  "`.hblist <page>` - View hardbanned users\n"
                  "`.hbpermsadd @user/@role` - Grant hardban permission\n"
                  "`.hbpermsrem @user/@role` - Remove hardban permission",
            inline=False
        )
        
        embed.add_field(
            name="**Fake Permissions (Owner)**",
            value="`.fakeperm add @user/@role <perms>` - Add fake permissions\n"
                  "`.fakeperm remove @user/@role <perms>` - Remove fake permissions\n"
                  "`.fakeperm list <page>` - View all fake permissions\n"
                  "`.fakeperm check @user` - Check user's fake permissions",
            inline=False
        )
        
        embed.add_field(
            name="**Role Management**",
            value="`.r <user> <role>` - Assign role\n"
                  "`.role remove <user> <role>` - Remove role",
            inline=False
        )
        
        embed.add_field(
            name="**Logging Setup**",
            value="`.setuplog messages` - Setup message logs\n"
                  "`.setuplog voice` - Setup voice logs\n"
                  "`.setuplog roles` - Setup role logs\n"
                  "`.setuplog antinuke` - Setup anti-nuke logs\n"
                  "`.setuplog message_edit` - Setup edit logs",
            inline=False
        )
        
        embed.add_field(
            name="**Anti-Nuke (Owner)**",
            value="`.whitelist add @user/@role` - Add to whitelist\n"
                  "`.whitelist remove @user/@role` - Remove from whitelist\n"
                  "`.whitelist list` - View whitelist\n"
                  "`.antinuke threshold <action> <count> <hours>` - Set thresholds",
            inline=False
        )
        
        embed.add_field(
            name="**Settings (Owner)**",
            value="`.jail role <role>` - Set jail role\n"
                  "`.jail channel <channel>` - Set jail channel\n"
                  "`.muterole set @role` - Set mute role\n"
                  "`.roleplay on/off` - Toggle roleplay commands\n"
                  "`.setrpgif <command> <url>` - Set roleplay gif",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cls')
    @is_admin()
    async def clear_messages(self, ctx, amount: int = 100):
        if amount > 100:
            amount = 100
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"✅ Deleted {len(deleted) - 1} messages")
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
