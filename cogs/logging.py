import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed
from utils.checks import is_admin
from datetime import datetime
from typing import Optional

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.voice_sessions = {}
    
    @commands.command(name='setuplog')
    @is_admin()
    async def setup_log(self, ctx, log_type: str):
        if log_type not in ['messages', 'voice', 'roles', 'antinuke']:
            await ctx.send("❌ Invalid log type. Choose from: messages, voice, roles, antinuke")
            return
        
        await ctx.send(f"Setting up {log_type} logging. Would you like to:\n1️⃣ Create a new channel\n2️⃣ Use an existing channel\n\nReact with 1️⃣ or 2️⃣")
        
        msg = await ctx.channel.fetch_message(ctx.message.id)
        await msg.add_reaction('1️⃣')
        await msg.add_reaction('2️⃣')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣'] and reaction.message.id == ctx.message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == '1️⃣':
                channel_name = f"{log_type}-logs"
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await ctx.guild.create_text_channel(name=channel_name, overwrites=overwrites)
                await self.config_manager.set_log_channel(ctx.guild.id, log_type, channel.id)
                await ctx.send(f"✅ Created {channel.mention} for {log_type} logging!")
            
            elif str(reaction.emoji) == '2️⃣':
                await ctx.send("Please mention the channel you want to use for logging.")
                
                def msg_check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=msg_check)
                    if msg.channel_mentions:
                        channel = msg.channel_mentions[0]
                        await self.config_manager.set_log_channel(ctx.guild.id, log_type, channel.id)
                        await ctx.send(f"✅ Set {channel.mention} for {log_type} logging!")
                    else:
                        await ctx.send("❌ No channel mentioned. Setup cancelled.")
                except:
                    await ctx.send("❌ Timed out. Setup cancelled.")
        
        except:
            await ctx.send("❌ Timed out. Setup cancelled.")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        channel_id = await self.config_manager.get_log_channel(message.guild.id, 'messages')
        if not channel_id:
            return
        
        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = create_log_embed(
            "Message Deleted",
            f"**Author:** {message.author.mention} ({message.author.name}#{message.author.discriminator} - {message.author.id})\n"
            f"**Channel:** {message.channel.mention}\n"
            f"**Content:** {message.content[:1000] if message.content else '*No content*'}\n"
            f"**Timestamp:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            discord.Color.red()
        )
        
        if message.attachments:
            embed.add_field(name="Attachments", value='\n'.join([a.filename for a in message.attachments]))
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel_id = await self.config_manager.get_log_channel(member.guild.id, 'voice')
        if not channel_id:
            return
        
        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return
        
        if before.channel != after.channel:
            if before.channel is None:
                session_key = f"{member.guild.id}_{member.id}_{after.channel.id}"
                self.voice_sessions[session_key] = datetime.utcnow()
                
                embed = create_log_embed(
                    "Voice Channel Join",
                    f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                    f"**Channel:** {after.channel.name}\n"
                    f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    discord.Color.green()
                )
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass
            
            elif after.channel is None:
                session_key = f"{member.guild.id}_{member.id}_{before.channel.id}"
                duration = "Unknown"
                if session_key in self.voice_sessions:
                    start_time = self.voice_sessions[session_key]
                    duration_delta = datetime.utcnow() - start_time
                    hours, remainder = divmod(int(duration_delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours}h {minutes}m {seconds}s"
                    del self.voice_sessions[session_key]
                
                embed = create_log_embed(
                    "Voice Channel Leave",
                    f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                    f"**Channel:** {before.channel.name}\n"
                    f"**Duration:** {duration}\n"
                    f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    discord.Color.red()
                )
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass
            
            else:
                embed = create_log_embed(
                    "Voice Channel Switch",
                    f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                    f"**From:** {before.channel.name}\n"
                    f"**To:** {after.channel.name}\n"
                    f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    discord.Color.blue()
                )
                try:
                    await log_channel.send(embed=embed)
                except:
                    pass
        
        if before.self_stream != after.self_stream:
            action = "Started Streaming" if after.self_stream else "Stopped Streaming"
            embed = create_log_embed(
                f"Voice {action}",
                f"**User:** {member.mention} ({member.name}#{member.discriminator} - {member.id})\n"
                f"**Channel:** {after.channel.name if after.channel else 'N/A'}\n"
                f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                discord.Color.purple()
            )
            try:
                await log_channel.send(embed=embed)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Logging(bot))
