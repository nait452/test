import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_admin, has_fake_permission
import config
from datetime import datetime
import uuid


class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
    
    async def get_warns_data(self, guild_id: int) -> dict:
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.WARNS_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'users': {}, 'config': {}}
            return data.get(str(guild_id), {'users': {}, 'config': {}})
    
    async def save_warns_data(self, guild_id: int, guild_data: dict):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.WARNS_DATA_FILE)
            data[str(guild_id)] = guild_data
            await self.config_manager._write_json(config.WARNS_DATA_FILE, data)
    
    async def get_warn_config(self, guild_id: int) -> dict:
        guild_data = await self.get_warns_data(guild_id)
        default_config = {
            'threshold': 3,
            'action': 'kick'
        }
        return {**default_config, **guild_data.get('config', {})}
    
    async def set_warn_config(self, guild_id: int, key: str, value):
        guild_data = await self.get_warns_data(guild_id)
        if 'config' not in guild_data:
            guild_data['config'] = {}
        guild_data['config'][key] = value
        await self.save_warns_data(guild_id, guild_data)
    
    async def get_user_warns(self, guild_id: int, user_id: int) -> list:
        guild_data = await self.get_warns_data(guild_id)
        return guild_data.get('users', {}).get(str(user_id), [])
    
    async def add_warn(self, guild_id: int, user_id: int, reason: str, warned_by: int) -> dict:
        guild_data = await self.get_warns_data(guild_id)
        
        if 'users' not in guild_data:
            guild_data['users'] = {}
        if str(user_id) not in guild_data['users']:
            guild_data['users'][str(user_id)] = []
        
        warn_data = {
            'id': str(uuid.uuid4())[:8],
            'reason': reason,
            'warned_by': warned_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        guild_data['users'][str(user_id)].append(warn_data)
        await self.save_warns_data(guild_id, guild_data)
        return warn_data
    
    async def remove_warn(self, guild_id: int, user_id: int, warn_id: str) -> bool:
        guild_data = await self.get_warns_data(guild_id)
        
        if str(user_id) not in guild_data.get('users', {}):
            return False
        
        warns = guild_data['users'][str(user_id)]
        for i, warn in enumerate(warns):
            if warn['id'] == warn_id:
                warns.pop(i)
                await self.save_warns_data(guild_id, guild_data)
                return True
        
        return False
    
    async def clear_warns(self, guild_id: int, user_id: int) -> int:
        guild_data = await self.get_warns_data(guild_id)
        
        if str(user_id) not in guild_data.get('users', {}):
            return 0
        
        count = len(guild_data['users'][str(user_id)])
        guild_data['users'][str(user_id)] = []
        await self.save_warns_data(guild_id, guild_data)
        return count
    
    async def execute_action(self, ctx, member: discord.Member, action: str, warn_count: int):
        try:
            if action == 'ban':
                await member.ban(reason=f"Automatic ban: Reached {warn_count} warnings")
                return f"🔨 {member.mention} has been **banned** for reaching {warn_count} warnings"
            
            elif action == 'kick':
                await member.kick(reason=f"Automatic kick: Reached {warn_count} warnings")
                return f"👢 {member.mention} has been **kicked** for reaching {warn_count} warnings"
            
            elif action == 'jail':
                guild_config = await self.config_manager.get_guild_config(ctx.guild.id)
                jail_role_id = guild_config.get('jail_role')
                
                if jail_role_id:
                    jail_role = ctx.guild.get_role(jail_role_id)
                    if jail_role:
                        await member.add_roles(jail_role, reason=f"Automatic jail: Reached {warn_count} warnings")
                        return f"⛓️ {member.mention} has been **jailed** for reaching {warn_count} warnings"
                
                return f"⚠️ {member.mention} reached {warn_count} warnings but jail role is not configured"
        
        except discord.Forbidden:
            return f"❌ Failed to execute action on {member.mention} - missing permissions"
        except Exception as e:
            return f"❌ Error executing action: {e}"
    
    async def log_warn(self, ctx, member: discord.Member, warn_data: dict, action_msg: str = None):
        channel_id = await self.config_manager.get_log_channel(ctx.guild.id, 'antinuke')
        if not channel_id:
            return
        
        log_channel = ctx.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        description = (
            f"**Moderator:** {ctx.author.mention}\n"
            f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
            f"**Reason:** {warn_data['reason']}\n"
            f"**Warn ID:** `{warn_data['id']}`"
        )
        
        if action_msg:
            description += f"\n\n**Auto-Action:** {action_msg}"
        
        embed = create_log_embed(
            "⚠️ Member Warned",
            description,
            discord.Color.orange()
        )
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.group(name='warn', invoke_without_command=True)
    async def warn(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        if not ctx.author.guild_permissions.kick_members:
            if not await has_fake_permission(ctx, 'warn'):
                await ctx.send("❌ You don't have permission to warn members")
                return
        
        if not member:
            await ctx.send("❌ Usage: `.warn @user [reason]`")
            return
        
        if member.bot:
            await ctx.send("❌ You cannot warn bots")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ You cannot warn yourself")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You cannot warn someone with a higher or equal role")
            return
        
        warn_data = await self.add_warn(ctx.guild.id, member.id, reason, ctx.author.id)
        user_warns = await self.get_user_warns(ctx.guild.id, member.id)
        warn_count = len(user_warns)
        
        warn_config = await self.get_warn_config(ctx.guild.id)
        threshold = warn_config['threshold']
        action = warn_config['action']
        
        action_msg = None
        if warn_count >= threshold:
            action_msg = await self.execute_action(ctx, member, action, warn_count)
        
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Warned By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Total Warns", value=f"`{warn_count}`", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warn ID", value=f"`{warn_data['id']}`", inline=True)
        
        if action_msg:
            embed.add_field(name="Auto-Action", value=action_msg, inline=False)
        
        embed.set_footer(text=f"Threshold: {threshold} warns | Action: {action}")
        
        await ctx.send(embed=embed)
        await self.log_warn(ctx, member, warn_data, action_msg)
    
    @warn.command(name='config')
    @is_admin()
    async def warn_config(self, ctx, setting: str = None, value: str = None):
        if not setting or not value:
            warn_config = await self.get_warn_config(ctx.guild.id)
            embed = discord.Embed(
                title="⚙️ Warning Configuration",
                color=discord.Color.gold()
            )
            embed.add_field(name="Threshold", value=f"`{warn_config['threshold']}` warns", inline=True)
            embed.add_field(name="Action", value=f"`{warn_config['action']}`", inline=True)
            embed.add_field(
                name="Usage",
                value="`.warn config threshold <number>` - Set warning threshold\n"
                      "`.warn config action <ban|kick|jail>` - Set auto-action",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        setting = setting.lower()
        
        if setting == 'threshold':
            try:
                threshold = int(value)
                if threshold < 1:
                    await ctx.send("❌ Threshold must be at least 1")
                    return
                await self.set_warn_config(ctx.guild.id, 'threshold', threshold)
                await ctx.send(f"✅ Set warning threshold to `{threshold}`")
            except ValueError:
                await ctx.send("❌ Please provide a valid number")
        
        elif setting == 'action':
            value = value.lower()
            if value not in ['ban', 'kick', 'jail']:
                await ctx.send("❌ Action must be `ban`, `kick`, or `jail`")
                return
            await self.set_warn_config(ctx.guild.id, 'action', value)
            await ctx.send(f"✅ Set warning action to `{value}`")
        
        else:
            await ctx.send("❌ Invalid setting. Use `threshold` or `action`")
    
    @commands.command(name='warns')
    async def warns(self, ctx, member: discord.Member = None, page: int = 1):
        if not member:
            await ctx.send("❌ Usage: `.warns @user [page]`")
            return
        
        user_warns = await self.get_user_warns(ctx.guild.id, member.id)
        
        if not user_warns:
            await ctx.send(f"✅ {member.mention} has no warnings")
            return
        
        warn_entries = []
        for i, warn in enumerate(user_warns, 1):
            warned_by = ctx.guild.get_member(warn['warned_by'])
            warned_by_str = warned_by.mention if warned_by else f"Unknown ({warn['warned_by']})"
            
            timestamp = datetime.fromisoformat(warn['timestamp'])
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
            
            warn_entries.append(
                f"**#{i}** | ID: `{warn['id']}`\n"
                f"**Reason:** {warn['reason']}\n"
                f"**By:** {warned_by_str} | **Date:** {timestamp_str}\n"
            )
        
        paginated, total_pages = paginate_list(warn_entries, page, 5)
        
        if not paginated:
            await ctx.send(f"❌ Page {page} doesn't exist. Total pages: {total_pages}")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name} ({len(user_warns)} total)",
            description=''.join(paginated),
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Page {page}/{total_pages}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarn', aliases=['clearwarns'])
    @is_admin()
    async def clearwarn(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.clearwarn @user`")
            return
        
        count = await self.clear_warns(ctx.guild.id, member.id)
        
        if count == 0:
            await ctx.send(f"✅ {member.mention} had no warnings to clear")
        else:
            await ctx.send(f"✅ Cleared `{count}` warning(s) from {member.mention}")
    
    @commands.command(name='removewarn', aliases=['delwarn'])
    @is_admin()
    async def removewarn(self, ctx, member: discord.Member = None, warn_id: str = None):
        if not member or not warn_id:
            await ctx.send("❌ Usage: `.removewarn @user <warn_id>`")
            return
        
        success = await self.remove_warn(ctx.guild.id, member.id, warn_id)
        
        if success:
            await ctx.send(f"✅ Removed warning `{warn_id}` from {member.mention}")
        else:
            await ctx.send(f"❌ Warning `{warn_id}` not found for {member.mention}")


async def setup(bot):
    await bot.add_cog(Warns(bot))
