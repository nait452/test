import discord
from discord.ext import commands, tasks
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_admin
import config
from datetime import datetime
import asyncio


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.voice_tracking = {}
        self.voice_xp_task.start()
    
    def cog_unload(self):
        self.voice_xp_task.cancel()
    
    async def get_leveling_data(self, guild_id: int) -> dict:
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.LEVELING_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'users': {}, 'config': {}}
            return data.get(str(guild_id), {'users': {}, 'config': {}})
    
    async def save_leveling_data(self, guild_id: int, guild_data: dict):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.LEVELING_DATA_FILE)
            data[str(guild_id)] = guild_data
            await self.config_manager._write_json(config.LEVELING_DATA_FILE, data)
    
    async def get_user_data(self, guild_id: int, user_id: int) -> dict:
        guild_data = await self.get_leveling_data(guild_id)
        if str(user_id) not in guild_data['users']:
            guild_data['users'][str(user_id)] = {'xp': 0, 'level': 0}
        return guild_data['users'][str(user_id)]
    
    async def set_user_data(self, guild_id: int, user_id: int, xp: int, level: int):
        guild_data = await self.get_leveling_data(guild_id)
        guild_data['users'][str(user_id)] = {'xp': xp, 'level': level}
        await self.save_leveling_data(guild_id, guild_data)
    
    async def get_level_config(self, guild_id: int) -> dict:
        guild_data = await self.get_leveling_data(guild_id)
        default_config = {
            'msg_xp': 10,
            'voice_xp': 5,
            'level_up_xp': 100
        }
        return {**default_config, **guild_data.get('config', {})}
    
    async def set_level_config(self, guild_id: int, key: str, value: int):
        guild_data = await self.get_leveling_data(guild_id)
        if 'config' not in guild_data:
            guild_data['config'] = {}
        guild_data['config'][key] = value
        await self.save_leveling_data(guild_id, guild_data)
    
    async def get_user_multiplier(self, guild_id: int, user_id: int) -> dict:
        from cogs.economy import Economy
        economy_cog = self.bot.get_cog('Economy')
        if economy_cog:
            return await economy_cog.get_active_multipliers(guild_id, user_id)
        return {'msg': 1.0, 'voice': 1.0}
    
    async def add_xp(self, guild_id: int, user_id: int, xp_amount: int, xp_type: str = 'msg') -> tuple:
        user_data = await self.get_user_data(guild_id, user_id)
        level_config = await self.get_level_config(guild_id)
        multipliers = await self.get_user_multiplier(guild_id, user_id)
        
        multiplier = multipliers.get(xp_type, 1.0)
        xp_gained = int(xp_amount * multiplier)
        
        user_data['xp'] += xp_gained
        level_up_xp = level_config['level_up_xp']
        
        leveled_up = False
        while user_data['xp'] >= level_up_xp:
            user_data['xp'] -= level_up_xp
            user_data['level'] += 1
            leveled_up = True
        
        await self.set_user_data(guild_id, user_id, user_data['xp'], user_data['level'])
        return leveled_up, user_data['level']
    
    def create_progress_bar(self, current: int, maximum: int, length: int = 20) -> str:
        filled = int(length * current / maximum)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    @tasks.loop(minutes=1)
    async def voice_xp_task(self):
        for guild in self.bot.guilds:
            level_config = await self.get_level_config(guild.id)
            voice_xp = level_config['voice_xp']
            
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot:
                        continue
                    if member.voice and not member.voice.self_deaf and not member.voice.deaf:
                        leveled_up, new_level = await self.add_xp(guild.id, member.id, voice_xp, 'voice')
    
    @voice_xp_task.before_loop
    async def before_voice_xp_task(self):
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        level_config = await self.get_level_config(message.guild.id)
        msg_xp = level_config['msg_xp']
        
        leveled_up, new_level = await self.add_xp(message.guild.id, message.author.id, msg_xp, 'msg')
        
        if leveled_up:
            try:
                await message.channel.send(f"🎉 Congratulations {message.author.mention}! You reached **Level {new_level}**!")
            except:
                pass
    
    @commands.group(name='level', invoke_without_command=True)
    async def level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = await self.get_user_data(ctx.guild.id, member.id)
        level_config = await self.get_level_config(ctx.guild.id)
        
        xp = user_data['xp']
        level = user_data['level']
        level_up_xp = level_config['level_up_xp']
        
        progress_bar = self.create_progress_bar(xp, level_up_xp)
        
        embed = discord.Embed(
            title=f"📊 Level Stats for {member.display_name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}/{level_up_xp}**", inline=True)
        embed.add_field(name="Progress", value=progress_bar, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @level.command(name='config')
    @is_admin()
    async def level_config(self, ctx, setting: str = None, amount: int = None):
        if not setting or not amount:
            level_config = await self.get_level_config(ctx.guild.id)
            embed = discord.Embed(
                title="⚙️ Leveling Configuration",
                color=discord.Color.gold()
            )
            embed.add_field(name="Message XP", value=f"`{level_config['msg_xp']}`", inline=True)
            embed.add_field(name="Voice XP/min", value=f"`{level_config['voice_xp']}`", inline=True)
            embed.add_field(name="XP per Level", value=f"`{level_config['level_up_xp']}`", inline=True)
            embed.add_field(
                name="Usage",
                value="`.level config msg <amount>` - Set message XP\n"
                      "`.level config voice <amount>` - Set voice XP/min\n"
                      "`.level config level_up <amount>` - Set XP per level",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        setting = setting.lower()
        valid_settings = {'msg': 'msg_xp', 'voice': 'voice_xp', 'level_up': 'level_up_xp'}
        
        if setting not in valid_settings:
            await ctx.send("❌ Invalid setting. Use `msg`, `voice`, or `level_up`")
            return
        
        if amount < 1:
            await ctx.send("❌ Amount must be at least 1")
            return
        
        await self.set_level_config(ctx.guild.id, valid_settings[setting], amount)
        await ctx.send(f"✅ Set `{setting}` to `{amount}`")
    
    @level.command(name='reset')
    @is_admin()
    async def level_reset(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send("❌ Usage: `.level reset @user`")
            return
        
        await self.set_user_data(ctx.guild.id, member.id, 0, 0)
        await ctx.send(f"✅ Reset level and XP for {member.mention}")
    
    @level.command(name='set')
    @is_admin()
    async def level_set(self, ctx, member: discord.Member = None, new_level: int = None):
        if not member or new_level is None:
            await ctx.send("❌ Usage: `.level set @user <level>`")
            return
        
        if new_level < 0:
            await ctx.send("❌ Level cannot be negative")
            return
        
        await self.set_user_data(ctx.guild.id, member.id, 0, new_level)
        await ctx.send(f"✅ Set {member.mention}'s level to `{new_level}`")
    
    @level.command(name='addxp')
    @is_admin()
    async def level_addxp(self, ctx, member: discord.Member = None, xp_amount: int = None):
        if not member or xp_amount is None:
            await ctx.send("❌ Usage: `.level addxp @user <amount>`")
            return
        
        leveled_up, new_level = await self.add_xp(ctx.guild.id, member.id, xp_amount, 'msg')
        await ctx.send(f"✅ Added `{xp_amount}` XP to {member.mention}")
        
        if leveled_up:
            await ctx.send(f"🎉 {member.mention} leveled up to **Level {new_level}**!")
    
    @commands.command(name='rank')
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = await self.get_user_data(ctx.guild.id, member.id)
        level_config = await self.get_level_config(ctx.guild.id)
        
        guild_data = await self.get_leveling_data(ctx.guild.id)
        users = guild_data.get('users', {})
        
        sorted_users = sorted(
            users.items(),
            key=lambda x: (x[1].get('level', 0), x[1].get('xp', 0)),
            reverse=True
        )
        
        rank = 1
        for i, (user_id, data) in enumerate(sorted_users, 1):
            if str(member.id) == user_id:
                rank = i
                break
        
        xp = user_data['xp']
        level = user_data['level']
        level_up_xp = level_config['level_up_xp']
        total_xp = (level * level_up_xp) + xp
        
        progress_bar = self.create_progress_bar(xp, level_up_xp)
        
        embed = discord.Embed(
            title=f"🏆 Rank Card for {member.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Total XP", value=f"**{total_xp:,}**", inline=True)
        embed.add_field(name="Progress to Next Level", value=f"{progress_bar}\n`{xp}/{level_up_xp} XP`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx, page: int = 1):
        guild_data = await self.get_leveling_data(ctx.guild.id)
        level_config = await self.get_level_config(ctx.guild.id)
        users = guild_data.get('users', {})
        
        if not users:
            await ctx.send("❌ No leveling data yet!")
            return
        
        sorted_users = sorted(
            users.items(),
            key=lambda x: (x[1].get('level', 0), x[1].get('xp', 0)),
            reverse=True
        )
        
        entries = []
        for i, (user_id, data) in enumerate(sorted_users, 1):
            try:
                member = ctx.guild.get_member(int(user_id))
                if member:
                    level = data.get('level', 0)
                    xp = data.get('xp', 0)
                    total_xp = (level * level_config['level_up_xp']) + xp
                    
                    medal = ""
                    if i == 1:
                        medal = "🥇 "
                    elif i == 2:
                        medal = "🥈 "
                    elif i == 3:
                        medal = "🥉 "
                    
                    entries.append(f"{medal}**#{i}** {member.mention}\nLevel: `{level}` | XP: `{total_xp:,}`\n")
            except:
                continue
        
        if not entries:
            await ctx.send("❌ No valid users in leaderboard!")
            return
        
        paginated, total_pages = paginate_list(entries, page, 10)
        
        if not paginated:
            await ctx.send(f"❌ Page {page} doesn't exist. Total pages: {total_pages}")
            return
        
        embed = discord.Embed(
            title=f"🏆 XP Leaderboard (Page {page}/{total_pages})",
            description=''.join(paginated),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Use .leaderboard <page> to view more")
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
