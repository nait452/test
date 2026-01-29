import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_owner, is_admin, has_fake_permission, hardban_permission
import config
from datetime import datetime
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.unban_warnings = {}
    
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
                  "`.cls <amount>` - Bulk delete messages (max 100)",
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
                  "`.setuplog antinuke` - Setup anti-nuke logs",
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
                  "`.roleplay on/off` - Toggle roleplay commands\n"
                  "`.rolegif <command> <url>` - Set roleplay gif",
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
