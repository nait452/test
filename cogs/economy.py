import discord
from discord.ext import commands, tasks
from utils.config_manager import ConfigManager
from utils.formatting import create_log_embed, paginate_list
from utils.checks import is_admin
import config
from datetime import datetime, timedelta
import asyncio


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        self.cleanup_expired_boosters.start()
        
        self.upgrades = {
            'msg_multi': {
                'name': 'Message XP Multiplier',
                'description': '+10% XP per message (permanent)',
                'cost': 1000,
                'type': 'permanent',
                'effect': {'msg': 0.1}
            },
            'voice_multi': {
                'name': 'Voice XP Multiplier',
                'description': '+10% XP per voice minute (permanent)',
                'cost': 1000,
                'type': 'permanent',
                'effect': {'voice': 0.1}
            },
            'xp_booster': {
                'name': 'XP Booster',
                'description': '+25% all XP for 1 hour',
                'cost': 500,
                'type': 'temporary',
                'duration': 3600,
                'effect': {'msg': 0.25, 'voice': 0.25}
            },
            'level_jump': {
                'name': 'Level Jump',
                'description': 'Instantly gain +1 level',
                'cost': 5000,
                'type': 'instant',
                'effect': {'level': 1}
            }
        }
    
    def cog_unload(self):
        self.cleanup_expired_boosters.cancel()
    
    async def get_economy_data(self, guild_id: int) -> dict:
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.ECONOMY_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'users': {}}
            return data.get(str(guild_id), {'users': {}})
    
    async def save_economy_data(self, guild_id: int, guild_data: dict):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.ECONOMY_DATA_FILE)
            data[str(guild_id)] = guild_data
            await self.config_manager._write_json(config.ECONOMY_DATA_FILE, data)
    
    async def get_user_economy(self, guild_id: int, user_id: int) -> dict:
        guild_data = await self.get_economy_data(guild_id)
        if str(user_id) not in guild_data['users']:
            guild_data['users'][str(user_id)] = {
                'permanent_upgrades': [],
                'active_boosters': [],
                'purchase_history': []
            }
        return guild_data['users'][str(user_id)]
    
    async def set_user_economy(self, guild_id: int, user_id: int, user_data: dict):
        guild_data = await self.get_economy_data(guild_id)
        guild_data['users'][str(user_id)] = user_data
        await self.save_economy_data(guild_id, guild_data)
    
    async def get_user_xp(self, guild_id: int, user_id: int) -> int:
        leveling_cog = self.bot.get_cog('Leveling')
        if leveling_cog:
            user_data = await leveling_cog.get_user_data(guild_id, user_id)
            level_config = await leveling_cog.get_level_config(guild_id)
            return (user_data['level'] * level_config['level_up_xp']) + user_data['xp']
        return 0
    
    async def deduct_xp(self, guild_id: int, user_id: int, amount: int) -> bool:
        leveling_cog = self.bot.get_cog('Leveling')
        if not leveling_cog:
            return False
        
        user_data = await leveling_cog.get_user_data(guild_id, user_id)
        level_config = await leveling_cog.get_level_config(guild_id)
        total_xp = (user_data['level'] * level_config['level_up_xp']) + user_data['xp']
        
        if total_xp < amount:
            return False
        
        new_total_xp = total_xp - amount
        new_level = new_total_xp // level_config['level_up_xp']
        new_xp = new_total_xp % level_config['level_up_xp']
        
        await leveling_cog.set_user_data(guild_id, user_id, new_xp, new_level)
        return True
    
    async def add_level(self, guild_id: int, user_id: int, levels: int):
        leveling_cog = self.bot.get_cog('Leveling')
        if leveling_cog:
            user_data = await leveling_cog.get_user_data(guild_id, user_id)
            new_level = user_data['level'] + levels
            await leveling_cog.set_user_data(guild_id, user_id, user_data['xp'], new_level)
    
    async def get_active_multipliers(self, guild_id: int, user_id: int) -> dict:
        user_data = await self.get_user_economy(guild_id, user_id)
        multipliers = {'msg': 1.0, 'voice': 1.0}
        
        for upgrade_id in user_data.get('permanent_upgrades', []):
            if upgrade_id in self.upgrades:
                effect = self.upgrades[upgrade_id].get('effect', {})
                multipliers['msg'] += effect.get('msg', 0)
                multipliers['voice'] += effect.get('voice', 0)
        
        current_time = datetime.utcnow().timestamp()
        for booster in user_data.get('active_boosters', []):
            if booster['expires'] > current_time:
                effect = booster.get('effect', {})
                multipliers['msg'] += effect.get('msg', 0)
                multipliers['voice'] += effect.get('voice', 0)
        
        return multipliers
    
    @tasks.loop(minutes=5)
    async def cleanup_expired_boosters(self):
        async with self.config_manager._lock:
            data = await self.config_manager._read_json(config.ECONOMY_DATA_FILE)
            current_time = datetime.utcnow().timestamp()
            
            for guild_id, guild_data in data.items():
                for user_id, user_data in guild_data.get('users', {}).items():
                    active_boosters = user_data.get('active_boosters', [])
                    user_data['active_boosters'] = [
                        b for b in active_boosters if b['expires'] > current_time
                    ]
            
            await self.config_manager._write_json(config.ECONOMY_DATA_FILE, data)
    
    @cleanup_expired_boosters.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='shop')
    async def shop(self, ctx):
        user_xp = await self.get_user_xp(ctx.guild.id, ctx.author.id)
        
        embed = discord.Embed(
            title="🛒 XP Shop",
            description=f"Your XP: **{user_xp:,}**\nUse `.buy <upgrade_id>` to purchase",
            color=discord.Color.green()
        )
        
        for upgrade_id, upgrade in self.upgrades.items():
            affordable = "✅" if user_xp >= upgrade['cost'] else "❌"
            embed.add_field(
                name=f"{affordable} {upgrade['name']}",
                value=f"**ID:** `{upgrade_id}`\n"
                      f"**Cost:** `{upgrade['cost']:,}` XP\n"
                      f"**Effect:** {upgrade['description']}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='buy')
    async def buy(self, ctx, upgrade_id: str = None):
        if not upgrade_id:
            await ctx.send("❌ Usage: `.buy <upgrade_id>`\nUse `.shop` to see available upgrades")
            return
        
        upgrade_id = upgrade_id.lower()
        if upgrade_id not in self.upgrades:
            await ctx.send("❌ Invalid upgrade ID. Use `.shop` to see available upgrades")
            return
        
        upgrade = self.upgrades[upgrade_id]
        user_xp = await self.get_user_xp(ctx.guild.id, ctx.author.id)
        
        if user_xp < upgrade['cost']:
            await ctx.send(f"❌ You need `{upgrade['cost']:,}` XP but only have `{user_xp:,}` XP")
            return
        
        user_economy = await self.get_user_economy(ctx.guild.id, ctx.author.id)
        
        if upgrade['type'] == 'permanent':
            if upgrade_id in user_economy.get('permanent_upgrades', []):
                await ctx.send("❌ You already own this upgrade!")
                return
        
        if not await self.deduct_xp(ctx.guild.id, ctx.author.id, upgrade['cost']):
            await ctx.send("❌ Failed to deduct XP. Please try again.")
            return
        
        if upgrade['type'] == 'permanent':
            if 'permanent_upgrades' not in user_economy:
                user_economy['permanent_upgrades'] = []
            user_economy['permanent_upgrades'].append(upgrade_id)
        
        elif upgrade['type'] == 'temporary':
            if 'active_boosters' not in user_economy:
                user_economy['active_boosters'] = []
            user_economy['active_boosters'].append({
                'id': upgrade_id,
                'effect': upgrade['effect'],
                'expires': datetime.utcnow().timestamp() + upgrade['duration']
            })
        
        elif upgrade['type'] == 'instant':
            if 'level' in upgrade['effect']:
                await self.add_level(ctx.guild.id, ctx.author.id, upgrade['effect']['level'])
        
        if 'purchase_history' not in user_economy:
            user_economy['purchase_history'] = []
        user_economy['purchase_history'].append({
            'id': upgrade_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        await self.set_user_economy(ctx.guild.id, ctx.author.id, user_economy)
        
        new_xp = await self.get_user_xp(ctx.guild.id, ctx.author.id)
        await ctx.send(f"✅ Purchased **{upgrade['name']}** for `{upgrade['cost']:,}` XP!\nRemaining XP: `{new_xp:,}`")
    
    @commands.command(name='inventory', aliases=['inv'])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_economy = await self.get_user_economy(ctx.guild.id, member.id)
        
        embed = discord.Embed(
            title=f"📦 Inventory for {member.display_name}",
            color=discord.Color.purple()
        )
        
        permanent = user_economy.get('permanent_upgrades', [])
        if permanent:
            perm_list = []
            for upgrade_id in permanent:
                if upgrade_id in self.upgrades:
                    perm_list.append(f"• {self.upgrades[upgrade_id]['name']}")
            embed.add_field(
                name="🔒 Permanent Upgrades",
                value='\n'.join(perm_list) if perm_list else "None",
                inline=False
            )
        else:
            embed.add_field(name="🔒 Permanent Upgrades", value="None", inline=False)
        
        active = user_economy.get('active_boosters', [])
        current_time = datetime.utcnow().timestamp()
        valid_boosters = [b for b in active if b['expires'] > current_time]
        
        if valid_boosters:
            booster_list = []
            for booster in valid_boosters:
                time_left = int(booster['expires'] - current_time)
                mins, secs = divmod(time_left, 60)
                hours, mins = divmod(mins, 60)
                if booster['id'] in self.upgrades:
                    name = self.upgrades[booster['id']]['name']
                    booster_list.append(f"• {name} ({hours}h {mins}m {secs}s left)")
            embed.add_field(
                name="⏱️ Active Boosters",
                value='\n'.join(booster_list) if booster_list else "None",
                inline=False
            )
        else:
            embed.add_field(name="⏱️ Active Boosters", value="None", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='upgrades')
    async def upgrades_cmd(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        multipliers = await self.get_active_multipliers(ctx.guild.id, member.id)
        
        embed = discord.Embed(
            title=f"📈 Active Multipliers for {member.display_name}",
            color=discord.Color.blue()
        )
        
        msg_bonus = int((multipliers['msg'] - 1.0) * 100)
        voice_bonus = int((multipliers['voice'] - 1.0) * 100)
        
        embed.add_field(
            name="💬 Message XP Multiplier",
            value=f"`{multipliers['msg']:.2f}x` (+{msg_bonus}%)",
            inline=True
        )
        embed.add_field(
            name="🎤 Voice XP Multiplier",
            value=f"`{multipliers['voice']:.2f}x` (+{voice_bonus}%)",
            inline=True
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
