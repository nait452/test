import discord
from discord.ext import commands
from utils.vc_manager import VCManager
from utils.formatting import create_embed
import asyncio

class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_manager = VCManager()
        self.dashboards = {}
    
    async def create_dashboard(self, channel: discord.VoiceChannel, owner: discord.Member):
        vc_data = await self.vc_manager.get_vc_data(channel.id)
        if not vc_data:
            return
        
        embed = discord.Embed(
            title=f"🎙️ Voice Channel Dashboard - {channel.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Owner",
            value=f"<@{vc_data['owner_id']}>",
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value="🔒 Locked" if vc_data['locked'] else "🔓 Unlocked",
            inline=True
        )
        
        embed.add_field(
            name="Member Count",
            value=f"{len(channel.members)}/{channel.user_limit if channel.user_limit > 0 else '∞'}",
            inline=True
        )
        
        trusted_list = '\n'.join([f"<@{uid}>" for uid in vc_data['trusted']]) if vc_data['trusted'] else "None"
        blocked_list = '\n'.join([f"<@{uid}>" for uid in vc_data['blocked']]) if vc_data['blocked'] else "None"
        
        embed.add_field(name="Trusted Users", value=trusted_list, inline=True)
        embed.add_field(name="Blocked Users", value=blocked_list, inline=True)
        
        embed.add_field(
            name="Commands",
            value="`.vc lock/unlock` - Lock/unlock the VC\n"
                  "`.vc trust @user` - Add trusted user\n"
                  "`.vc untrust @user` - Remove trusted user\n"
                  "`.vc block @user` - Block a user\n"
                  "`.vc unblock @user` - Unblock a user\n"
                  "`.vc disconnect @user` - Disconnect a user\n"
                  "`.vc limit <number>` - Set user limit\n"
                  "`.vc transfer @user` - Transfer ownership\n"
                  "`.vc rename <name>` - Rename the VC\n"
                  "`.vc delete` - Delete the VC\n"
                  "`.vc claim` - Claim the VC (if owner left)",
            inline=False
        )
        
        try:
            if channel.id in self.dashboards:
                old_msg = self.dashboards[channel.id]
                try:
                    await old_msg.delete()
                except:
                    pass
            
            msg = await channel.send(embed=embed)
            self.dashboards[channel.id] = msg
        except:
            pass
    
    async def update_dashboard(self, channel: discord.VoiceChannel):
        await self.create_dashboard(channel, channel.guild.get_member(await self.get_vc_owner(channel.id)))
    
    async def get_vc_owner(self, channel_id: int) -> int:
        vc_data = await self.vc_manager.get_vc_data(channel_id)
        return vc_data['owner_id'] if vc_data else None
    
    async def is_vc_owner(self, channel_id: int, user_id: int) -> bool:
        owner_id = await self.get_vc_owner(channel_id)
        return owner_id == user_id if owner_id else False
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel and before.channel != after.channel:
            vc_data = await self.vc_manager.get_vc_data(before.channel.id)
            if vc_data and vc_data['owner_id'] == member.id:
                self.vc_manager.set_owner_left_time(before.channel.id)
        
        if after.channel and after.channel != before.channel:
            vc_data = await self.vc_manager.get_vc_data(after.channel.id)
            if vc_data and vc_data['owner_id'] == member.id:
                self.vc_manager.clear_owner_left_time(after.channel.id)
    
    @commands.group(name='vc', invoke_without_command=True)
    async def vc(self, ctx):
        await ctx.send("Use `.vc <command>`. Type `.vc help` for a list of commands.")
    
    @vc.command(name='claim')
    async def vc_claim(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel to claim it")
            return
        
        channel = ctx.author.voice.channel
        vc_data = await self.vc_manager.get_vc_data(channel.id)
        
        if not vc_data:
            await ctx.send("❌ This is not a managed voice channel")
            return
        
        if vc_data['owner_id'] == ctx.author.id:
            await ctx.send("❌ You already own this voice channel")
            return
        
        owner = ctx.guild.get_member(vc_data['owner_id'])
        if owner and owner in channel.members:
            await ctx.send("❌ The owner is currently in the voice channel")
            return
        
        if not self.vc_manager.can_claim(channel.id):
            await ctx.send("❌ You must wait 30 seconds after the owner leaves to claim the channel")
            return
        
        await self.vc_manager.update_vc_owner(channel.id, ctx.author.id)
        await ctx.send(f"✅ You now own {channel.name}")
        await self.update_dashboard(channel)
    
    @vc.command(name='lock')
    async def vc_lock(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        vc_data = await self.vc_manager.get_vc_data(channel.id)
        if vc_data['locked']:
            await ctx.send("❌ Voice channel is already locked")
            return
        
        await self.vc_manager.toggle_lock(channel.id)
        await ctx.send(f"🔒 Locked {channel.name}")
        await self.update_dashboard(channel)
    
    @vc.command(name='unlock')
    async def vc_unlock(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        vc_data = await self.vc_manager.get_vc_data(channel.id)
        if not vc_data['locked']:
            await ctx.send("❌ Voice channel is already unlocked")
            return
        
        await self.vc_manager.toggle_lock(channel.id)
        await ctx.send(f"🔓 Unlocked {channel.name}")
        await self.update_dashboard(channel)
    
    @vc.command(name='trust')
    async def vc_trust(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc trust @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        await self.vc_manager.add_trusted(channel.id, member.id)
        await ctx.send(f"✅ Added {member.mention} to trusted list")
        await self.update_dashboard(channel)
    
    @vc.command(name='untrust')
    async def vc_untrust(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc untrust @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        await self.vc_manager.remove_trusted(channel.id, member.id)
        await ctx.send(f"✅ Removed {member.mention} from trusted list")
        await self.update_dashboard(channel)
    
    @vc.command(name='block')
    async def vc_block(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc block @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        await self.vc_manager.add_blocked(channel.id, member.id)
        
        try:
            overwrite = channel.overwrites_for(member)
            overwrite.connect = False
            await channel.set_permissions(member, overwrite=overwrite)
            
            if member in channel.members:
                await member.move_to(None, reason=f"Blocked by {ctx.author}")
        except:
            pass
        
        await ctx.send(f"✅ Blocked {member.mention}")
        await self.update_dashboard(channel)
    
    @vc.command(name='unblock')
    async def vc_unblock(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc unblock @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        await self.vc_manager.remove_blocked(channel.id, member.id)
        
        try:
            await channel.set_permissions(member, overwrite=None)
        except:
            pass
        
        await ctx.send(f"✅ Unblocked {member.mention}")
        await self.update_dashboard(channel)
    
    @vc.command(name='disconnect')
    async def vc_disconnect(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc disconnect @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        if member not in channel.members:
            await ctx.send(f"❌ {member.mention} is not in this voice channel")
            return
        
        try:
            await member.move_to(None, reason=f"Disconnected by {ctx.author}")
            await ctx.send(f"✅ Disconnected {member.mention}")
        except:
            await ctx.send("❌ Failed to disconnect user")
    
    @vc.command(name='limit')
    async def vc_limit(self, ctx, limit: int = 0):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        if limit < 0 or limit > 99:
            await ctx.send("❌ Limit must be between 0 and 99 (0 = unlimited)")
            return
        
        try:
            await channel.edit(user_limit=limit)
            await ctx.send(f"✅ Set user limit to {limit if limit > 0 else 'unlimited'}")
            await self.update_dashboard(channel)
        except:
            await ctx.send("❌ Failed to set user limit")
    
    @vc.command(name='transfer')
    async def vc_transfer(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.vc transfer @user`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        await self.vc_manager.update_vc_owner(channel.id, member.id)
        await ctx.send(f"✅ Transferred ownership to {member.mention}")
        await self.update_dashboard(channel)
    
    @vc.command(name='rename')
    async def vc_rename(self, ctx, *, name: str = None):
        if not name:
            await ctx.send("❌ Usage: `.vc rename <new_name>`")
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        try:
            await channel.edit(name=name)
            await ctx.send(f"✅ Renamed voice channel to {name}")
            await self.update_dashboard(channel)
        except:
            await ctx.send("❌ Failed to rename voice channel")
    
    @vc.command(name='delete')
    async def vc_delete(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel")
            return
        
        channel = ctx.author.voice.channel
        
        if not await self.is_vc_owner(channel.id, ctx.author.id):
            await ctx.send("❌ You don't own this voice channel")
            return
        
        try:
            await self.vc_manager.delete_vc(channel.id)
            await ctx.send(f"✅ Deleting voice channel...")
            await asyncio.sleep(2)
            await channel.delete(reason=f"Deleted by owner {ctx.author}")
        except:
            await ctx.send("❌ Failed to delete voice channel")

async def setup(bot):
    await bot.add_cog(VoiceChannel(bot))
