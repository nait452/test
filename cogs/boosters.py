import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_admin
import config
from datetime import datetime


class Boosters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
    
    async def get_booster_data(self, guild_id: int) -> dict:
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.BOOSTERS_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'config': {}, 'boosters': {}}
            return data.get(str(guild_id), {'config': {}, 'boosters': {}})
    
    async def save_booster_data(self, guild_id: int, guild_data: dict):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.BOOSTERS_DATA_FILE)
            data[str(guild_id)] = guild_data
            await self.config_manager._write_json(config.BOOSTERS_DATA_FILE, data)
    
    async def get_booster_config(self, guild_id: int) -> dict:
        guild_data = await self.get_booster_data(guild_id)
        default_config = {
            'template': '🎉 Thank you {booster} for boosting {guild}! We now have {count} boosts (Level {level})!',
            'log_channel': None
        }
        return {**default_config, **guild_data.get('config', {})}
    
    async def set_booster_config(self, guild_id: int, key: str, value):
        guild_data = await self.get_booster_data(guild_id)
        if 'config' not in guild_data:
            guild_data['config'] = {}
        guild_data['config'][key] = value
        await self.save_booster_data(guild_id, guild_data)
    
    async def track_booster(self, guild_id: int, user_id: int, boosted: bool):
        guild_data = await self.get_booster_data(guild_id)
        
        if 'boosters' not in guild_data:
            guild_data['boosters'] = {}
        
        if boosted:
            guild_data['boosters'][str(user_id)] = {
                'first_boost': datetime.utcnow().isoformat(),
                'active': True
            }
        else:
            if str(user_id) in guild_data['boosters']:
                guild_data['boosters'][str(user_id)]['active'] = False
        
        await self.save_booster_data(guild_id, guild_data)
    
    def format_boost_message(self, template: str, member: discord.Member, guild: discord.Guild) -> str:
        return template.format(
            booster=member.mention,
            guild=guild.name,
            count=guild.premium_subscription_count,
            level=guild.premium_tier
        )
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.premium_since is None and after.premium_since is not None:
            await self.track_booster(after.guild.id, after.id, True)
            
            booster_config = await self.get_booster_config(after.guild.id)
            channel_id = booster_config.get('log_channel')
            
            if channel_id:
                channel = after.guild.get_channel(channel_id)
                if channel:
                    template = booster_config.get('template', '')
                    message = self.format_boost_message(template, after, after.guild)
                    
                    embed = discord.Embed(
                        title="💎 New Server Boost!",
                        description=message,
                        color=discord.Color.nitro_pink()
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.add_field(name="Booster", value=after.mention, inline=True)
                    embed.add_field(name="Total Boosts", value=f"`{after.guild.premium_subscription_count}`", inline=True)
                    embed.add_field(name="Server Level", value=f"`{after.guild.premium_tier}`", inline=True)
                    embed.timestamp = datetime.utcnow()
                    
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass
        
        elif before.premium_since is not None and after.premium_since is None:
            await self.track_booster(after.guild.id, after.id, False)
            
            booster_config = await self.get_booster_config(after.guild.id)
            channel_id = booster_config.get('log_channel')
            
            if channel_id:
                channel = after.guild.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="💔 Boost Lost",
                        description=f"{after.mention} is no longer boosting the server.",
                        color=discord.Color.red()
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.add_field(name="Remaining Boosts", value=f"`{after.guild.premium_subscription_count}`", inline=True)
                    embed.add_field(name="Server Level", value=f"`{after.guild.premium_tier}`", inline=True)
                    embed.timestamp = datetime.utcnow()
                    
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass
    
    @commands.group(name='booster', invoke_without_command=True)
    @is_admin()
    async def booster(self, ctx):
        await ctx.send("Use `.booster config template <text>`, `.booster config channel #channel`, or `.booster info`")
    
    @booster.command(name='config')
    @is_admin()
    async def booster_config(self, ctx, setting: str = None, *, value: str = None):
        if not setting:
            booster_config = await self.get_booster_config(ctx.guild.id)
            embed = discord.Embed(
                title="⚙️ Booster Configuration",
                color=discord.Color.nitro_pink()
            )
            
            channel_id = booster_config.get('log_channel')
            channel_str = f"<#{channel_id}>" if channel_id else "Not set"
            
            embed.add_field(name="Log Channel", value=channel_str, inline=False)
            embed.add_field(name="Template", value=f"```{booster_config['template']}```", inline=False)
            embed.add_field(
                name="Placeholders",
                value="`{booster}` - Booster mention\n"
                      "`{guild}` - Server name\n"
                      "`{count}` - Boost count\n"
                      "`{level}` - Server boost level",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value="`.booster config template <text>` - Set boost message\n"
                      "`.booster config channel #channel` - Set notification channel",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        setting = setting.lower()
        
        if setting == 'template':
            if not value:
                await ctx.send("❌ Please provide a template message")
                return
            await self.set_booster_config(ctx.guild.id, 'template', value)
            await ctx.send(f"✅ Set boost message template:\n```{value}```")
        
        elif setting == 'channel':
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
                await self.set_booster_config(ctx.guild.id, 'log_channel', channel.id)
                await ctx.send(f"✅ Set boost notification channel to {channel.mention}")
            else:
                await ctx.send("❌ Please mention a channel")
        
        else:
            await ctx.send("❌ Invalid setting. Use `template` or `channel`")
    
    @booster.command(name='info')
    async def booster_info(self, ctx):
        booster_config = await self.get_booster_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="💎 Booster Information",
            color=discord.Color.nitro_pink()
        )
        
        embed.add_field(name="Total Boosts", value=f"`{ctx.guild.premium_subscription_count}`", inline=True)
        embed.add_field(name="Server Level", value=f"`{ctx.guild.premium_tier}`", inline=True)
        embed.add_field(name="Active Boosters", value=f"`{len(ctx.guild.premium_subscribers)}`", inline=True)
        
        channel_id = booster_config.get('log_channel')
        channel_str = f"<#{channel_id}>" if channel_id else "Not configured"
        embed.add_field(name="Notification Channel", value=channel_str, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='boosters')
    async def boosters(self, ctx, page: int = 1):
        boosters = ctx.guild.premium_subscribers
        
        if not boosters:
            await ctx.send("❌ This server has no boosters")
            return
        
        booster_entries = []
        for i, member in enumerate(boosters, 1):
            boost_since = member.premium_since
            if boost_since:
                duration = datetime.utcnow() - boost_since.replace(tzinfo=None)
                days = duration.days
                booster_entries.append(f"**#{i}** {member.mention}\nBoosting for `{days}` days\n")
            else:
                booster_entries.append(f"**#{i}** {member.mention}\n")
        
        paginated, total_pages = paginate_list(booster_entries, page, 10)
        
        if not paginated:
            await ctx.send(f"❌ Page {page} doesn't exist. Total pages: {total_pages}")
            return
        
        embed = discord.Embed(
            title=f"💎 Server Boosters ({len(boosters)} total)",
            description=''.join(paginated),
            color=discord.Color.nitro_pink()
        )
        embed.add_field(name="Server Level", value=f"`{ctx.guild.premium_tier}`", inline=True)
        embed.add_field(name="Total Boosts", value=f"`{ctx.guild.premium_subscription_count}`", inline=True)
        embed.set_footer(text=f"Page {page}/{total_pages}")
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Boosters(bot))
