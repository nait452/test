import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed
from datetime import datetime
import asyncio

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
    
    async def log_role_action(self, guild: discord.Guild, action: str, member: discord.Member, role: discord.Role, actor: discord.Member):
        channel_id = await self.config_manager.get_log_channel(guild.id, 'roles')
        if not channel_id:
            return
        
        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return
        
        color = discord.Color.green() if action == "Added" else discord.Color.red()
        
        embed = create_log_embed(
            f"Role {action}",
            f"**Actor:** {actor.mention} ({actor.name}#{actor.discriminator} - {actor.id})\n"
            f"**Target:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
            f"**Role:** {role.mention}\n"
            f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            color
        )
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.command(name='r', aliases=['role'])
    async def assign_role(self, ctx, member: discord.Member = None, *, role: discord.Role = None):
        if not member or not role:
            await ctx.send("❌ Usage: `.r <user> <role>` or `.role <user> <role>`")
            return
        
        if not ctx.author.guild_permissions.manage_roles:
            from utils.checks import has_fake_permission
            if not await has_fake_permission(ctx, 'role'):
                await ctx.send("❌ You don't have permission to manage roles")
                return
        
        if role in member.roles:
            await ctx.send(f"❌ {member.mention} already has the {role.mention} role")
            return
        
        try:
            await member.add_roles(role, reason=f"Role assigned by {ctx.author}")
            await ctx.send(f"✅ Added {role.mention} to {member.mention}")
            await self.log_role_action(ctx.guild, "Added", member, role, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign that role")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.group(name='role', invoke_without_command=True)
    async def role_group(self, ctx, member: discord.Member = None, *, role: discord.Role = None):
        if not member or not role:
            await ctx.send("❌ Usage: `.role <user> <role>` or `.role remove <user> <role>`")
            return
        
        await self.assign_role(ctx, member, role=role)
    
    @role_group.command(name='remove')
    async def remove_role(self, ctx, member: discord.Member = None, *, role: discord.Role = None):
        if not member or not role:
            await ctx.send("❌ Usage: `.role remove <user> <role>`")
            return
        
        if not ctx.author.guild_permissions.manage_roles:
            from utils.checks import has_fake_permission
            if not await has_fake_permission(ctx, 'role'):
                await ctx.send("❌ You don't have permission to manage roles")
                return
        
        if role not in member.roles:
            await ctx.send(f"❌ {member.mention} doesn't have the {role.mention} role")
            return
        
        try:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            await ctx.send(f"✅ Removed {role.mention} from {member.mention}")
            await self.log_role_action(ctx.guild, "Removed", member, role, ctx.author)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove that role")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        try:
            await asyncio.sleep(1)
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    executor = entry.user
                    
                    channel_id = await self.config_manager.get_log_channel(role.guild.id, 'roles')
                    if not channel_id:
                        return
                    
                    log_channel = role.guild.get_channel(channel_id)
                    if not log_channel:
                        return
                    
                    embed = create_log_embed(
                        "Role Created",
                        f"**Creator:** {executor.mention} ({executor.name}#{executor.discriminator} - {executor.id})\n"
                        f"**Role:** {role.mention}\n"
                        f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                        discord.Color.blue()
                    )
                    
                    await log_channel.send(embed=embed)
                    break
        except Exception as e:
            print(f"Error in on_guild_role_create: {e}")

async def setup(bot):
    await bot.add_cog(Roles(bot))
