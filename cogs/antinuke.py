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
        
        self.default_thresholds = {
            'ban': {'count': 3, 'hours': 1},
            'kick': {'count': 5, 'hours': 1},
            'role_create': {'count': 5, 'hours': 1},
            'role_delete': {'count': 3, 'hours': 1},
            'channel_create': {'count': 5, 'hours': 1},
            'channel_delete': {'count': 3, 'hours': 1},
            'webhook_create': {'count': 5, 'hours': 1},
            'webhook_delete': {'count': 3, 'hours': 1},
            'emoji_create': {'count': 10, 'hours': 1},
            'emoji_delete': {'count': 5, 'hours': 1},
            'sticker_create': {'count': 10, 'hours': 1},
            'sticker_delete': {'count': 5, 'hours': 1}
        }
    
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
            if action in self.default_thresholds:
                threshold_config = self.default_thresholds[action]
            else:
                return False
        else:
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
    
    async def get_action_count(self, guild_id: int, user_id: int, action: str) -> int:
        thresholds = await self.config_manager.get_antinuke_thresholds(guild_id)
        
        if action not in thresholds:
            if action in self.default_thresholds:
                threshold_config = self.default_thresholds[action]
            else:
                return 0
        else:
            threshold_config = thresholds[action]
        
        time_window = timedelta(hours=threshold_config['hours'])
        now = datetime.utcnow()
        
        self.action_tracker[guild_id][f"{user_id}_{action}"] = [
            t for t in self.action_tracker[guild_id][f"{user_id}_{action}"]
            if now - t < time_window
        ]
        
        return len(self.action_tracker[guild_id][f"{user_id}_{action}"])
    
    async def execute_punishment(self, guild: discord.Guild, member: discord.Member, action: str, reason: str, details: dict = None):
        punishment_action = await self.config_manager.get_antinuke_action(guild.id)
        
        success = False
        punishment_msg = ""
        
        if punishment_action == 'jail':
            success = await self.jail_user(guild, member, reason)
            punishment_msg = "Jailed"
        elif punishment_action == 'ban':
            try:
                await guild.ban(member, reason=f"Anti-nuke: {reason}")
                success = True
                punishment_msg = "Banned"
            except Exception as e:
                print(f"Error banning user: {e}")
        elif punishment_action == 'kick':
            try:
                await guild.kick(member, reason=f"Anti-nuke: {reason}")
                success = True
                punishment_msg = "Kicked"
            except Exception as e:
                print(f"Error kicking user: {e}")
        
        if success:
            history_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'action_type': action,
                'user_id': member.id,
                'user_name': str(member),
                'punishment': punishment_msg,
                'reason': reason
            }
            if details:
                history_data['details'] = details
            
            await self.config_manager.add_antinuke_history(guild.id, history_data)
        
        return success, punishment_msg
    
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
            return True
        except Exception as e:
            print(f"Error jailing user: {e}")
            return False
    
    async def log_antinuke_action(self, guild: discord.Guild, title: str, description: str, 
                                   actor: discord.Member, action_type: str, threshold_info: dict = None):
        channel_id = await self.config_manager.get_log_channel(guild.id, 'antinuke')
        if not channel_id:
            return
        
        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title=f"🚨 {title}",
            description=description,
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Actor",
            value=f"{actor.mention} ({actor.name}#{actor.discriminator})\nID: {actor.id}",
            inline=False
        )
        
        if threshold_info:
            action_count = threshold_info.get('count', 0)
            threshold_limit = threshold_info.get('limit', 0)
            time_window = threshold_info.get('hours', 1)
            
            embed.add_field(
                name="Threshold Status",
                value=f"**Actions in window:** {action_count}/{threshold_limit}\n"
                      f"**Time window:** {time_window} hour(s)",
                inline=False
            )
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending antinuke log: {e}")
    
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
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(guild.id)
                    threshold_config = thresholds.get('ban', self.default_thresholds['ban'])
                    
                    if await self.check_threshold(guild.id, executor.id, 'ban'):
                        action_count = await self.get_action_count(guild.id, executor.id, 'ban')
                        success, punishment = await self.execute_punishment(
                            guild, member, 'ban',
                            f"Mass ban detected - {action_count} bans in {threshold_config['hours']} hour(s)",
                            {'target': str(user), 'reason': entry.reason}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                guild,
                                "Mass Ban Detected - Action Taken",
                                f"**Target banned:** {user.name}#{user.discriminator} ({user.id})\n"
                                f"**Audit reason:** {entry.reason or 'No reason'}\n"
                                f"**Punishment:** {punishment}",
                                member,
                                'ban',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
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
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(member.guild.id)
                    threshold_config = thresholds.get('kick', self.default_thresholds['kick'])
                    
                    if await self.check_threshold(member.guild.id, executor.id, 'kick'):
                        action_count = await self.get_action_count(member.guild.id, executor.id, 'kick')
                        success, punishment = await self.execute_punishment(
                            member.guild, executor_member, 'kick',
                            f"Mass kick detected - {action_count} kicks in {threshold_config['hours']} hour(s)",
                            {'target': str(member), 'reason': entry.reason}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                member.guild,
                                "Mass Kick Detected - Action Taken",
                                f"**Target kicked:** {member.name}#{member.discriminator} ({member.id})\n"
                                f"**Audit reason:** {entry.reason or 'No reason'}\n"
                                f"**Punishment:** {punishment}",
                                executor_member,
                                'kick',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
                    break
        except Exception as e:
            print(f"Error in on_member_remove: {e}")
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        try:
            await asyncio.sleep(1)
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    executor_member = role.guild.get_member(executor.id)
                    if not executor_member:
                        return
                    
                    if await self.is_whitelisted(role.guild.id, executor.id, executor_member.roles):
                        return
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(role.guild.id)
                    threshold_config = thresholds.get('role_create', self.default_thresholds['role_create'])
                    
                    if await self.check_threshold(role.guild.id, executor.id, 'role_create'):
                        action_count = await self.get_action_count(role.guild.id, executor.id, 'role_create')
                        success, punishment = await self.execute_punishment(
                            role.guild, executor_member, 'role_create',
                            f"Mass role creation detected - {action_count} roles in {threshold_config['hours']} hour(s)",
                            {'role_name': role.name, 'role_id': role.id}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                role.guild,
                                "Mass Role Creation Detected - Action Taken",
                                f"**Role created:** {role.name} ({role.id})\n"
                                f"**Punishment:** {punishment}",
                                executor_member,
                                'role_create',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
                    break
        except Exception as e:
            print(f"Error in on_guild_role_create: {e}")
    
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
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(role.guild.id)
                    threshold_config = thresholds.get('role_delete', self.default_thresholds['role_delete'])
                    
                    if await self.check_threshold(role.guild.id, executor.id, 'role_delete'):
                        action_count = await self.get_action_count(role.guild.id, executor.id, 'role_delete')
                        success, punishment = await self.execute_punishment(
                            role.guild, executor_member, 'role_delete',
                            f"Mass role deletion detected - {action_count} roles in {threshold_config['hours']} hour(s)",
                            {'role_name': role.name, 'role_id': role.id}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                role.guild,
                                "Mass Role Deletion Detected - Action Taken",
                                f"**Role deleted:** {role.name} ({role.id})\n"
                                f"**Punishment:** {punishment}",
                                executor_member,
                                'role_delete',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
                    break
        except Exception as e:
            print(f"Error in on_guild_role_delete: {e}")
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        try:
            await asyncio.sleep(1)
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    executor = entry.user
                    
                    if executor.bot:
                        return
                    
                    executor_member = channel.guild.get_member(executor.id)
                    if not executor_member:
                        return
                    
                    if await self.is_whitelisted(channel.guild.id, executor.id, executor_member.roles):
                        return
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(channel.guild.id)
                    threshold_config = thresholds.get('channel_create', self.default_thresholds['channel_create'])
                    
                    if await self.check_threshold(channel.guild.id, executor.id, 'channel_create'):
                        action_count = await self.get_action_count(channel.guild.id, executor.id, 'channel_create')
                        success, punishment = await self.execute_punishment(
                            channel.guild, executor_member, 'channel_create',
                            f"Mass channel creation detected - {action_count} channels in {threshold_config['hours']} hour(s)",
                            {'channel_name': channel.name, 'channel_id': channel.id, 'channel_type': str(channel.type)}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                channel.guild,
                                "Mass Channel Creation Detected - Action Taken",
                                f"**Channel created:** {channel.name} ({channel.id})\n"
                                f"**Channel type:** {channel.type}\n"
                                f"**Punishment:** {punishment}",
                                executor_member,
                                'channel_create',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
                    break
        except Exception as e:
            print(f"Error in on_guild_channel_create: {e}")
    
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
                    
                    thresholds = await self.config_manager.get_antinuke_thresholds(channel.guild.id)
                    threshold_config = thresholds.get('channel_delete', self.default_thresholds['channel_delete'])
                    
                    if await self.check_threshold(channel.guild.id, executor.id, 'channel_delete'):
                        action_count = await self.get_action_count(channel.guild.id, executor.id, 'channel_delete')
                        success, punishment = await self.execute_punishment(
                            channel.guild, executor_member, 'channel_delete',
                            f"Mass channel deletion detected - {action_count} channels in {threshold_config['hours']} hour(s)",
                            {'channel_name': channel.name, 'channel_id': channel.id, 'channel_type': str(channel.type)}
                        )
                        
                        if success:
                            await self.log_antinuke_action(
                                channel.guild,
                                "Mass Channel Deletion Detected - Action Taken",
                                f"**Channel deleted:** {channel.name} ({channel.id})\n"
                                f"**Channel type:** {channel.type}\n"
                                f"**Punishment:** {punishment}",
                                executor_member,
                                'channel_delete',
                                {
                                    'count': action_count,
                                    'limit': threshold_config['count'],
                                    'hours': threshold_config['hours']
                                }
                            )
                    break
        except Exception as e:
            print(f"Error in on_guild_channel_delete: {e}")
    
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        try:
            await asyncio.sleep(1)
            
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_create):
                executor = entry.user
                
                if executor.bot:
                    continue
                
                executor_member = channel.guild.get_member(executor.id)
                if not executor_member:
                    continue
                
                if await self.is_whitelisted(channel.guild.id, executor.id, executor_member.roles):
                    continue
                
                thresholds = await self.config_manager.get_antinuke_thresholds(channel.guild.id)
                threshold_config = thresholds.get('webhook_create', self.default_thresholds['webhook_create'])
                
                if await self.check_threshold(channel.guild.id, executor.id, 'webhook_create'):
                    action_count = await self.get_action_count(channel.guild.id, executor.id, 'webhook_create')
                    success, punishment = await self.execute_punishment(
                        channel.guild, executor_member, 'webhook_create',
                        f"Mass webhook creation detected - {action_count} webhooks in {threshold_config['hours']} hour(s)",
                        {'channel_name': channel.name, 'channel_id': channel.id}
                    )
                    
                    if success:
                        await self.log_antinuke_action(
                            channel.guild,
                            "Mass Webhook Creation Detected - Action Taken",
                            f"**Channel:** {channel.mention} ({channel.id})\n"
                            f"**Punishment:** {punishment}",
                            executor_member,
                            'webhook_create',
                            {
                                'count': action_count,
                                'limit': threshold_config['count'],
                                'hours': threshold_config['hours']
                            }
                        )
                break
            
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.webhook_delete):
                executor = entry.user
                
                if executor.bot:
                    continue
                
                executor_member = channel.guild.get_member(executor.id)
                if not executor_member:
                    continue
                
                if await self.is_whitelisted(channel.guild.id, executor.id, executor_member.roles):
                    continue
                
                thresholds = await self.config_manager.get_antinuke_thresholds(channel.guild.id)
                threshold_config = thresholds.get('webhook_delete', self.default_thresholds['webhook_delete'])
                
                if await self.check_threshold(channel.guild.id, executor.id, 'webhook_delete'):
                    action_count = await self.get_action_count(channel.guild.id, executor.id, 'webhook_delete')
                    success, punishment = await self.execute_punishment(
                        channel.guild, executor_member, 'webhook_delete',
                        f"Mass webhook deletion detected - {action_count} webhooks in {threshold_config['hours']} hour(s)",
                        {'channel_name': channel.name, 'channel_id': channel.id}
                    )
                    
                    if success:
                        await self.log_antinuke_action(
                            channel.guild,
                            "Mass Webhook Deletion Detected - Action Taken",
                            f"**Channel:** {channel.mention} ({channel.id})\n"
                            f"**Punishment:** {punishment}",
                            executor_member,
                            'webhook_delete',
                            {
                                'count': action_count,
                                'limit': threshold_config['count'],
                                'hours': threshold_config['hours']
                            }
                        )
                break
        except Exception as e:
            print(f"Error in on_webhooks_update: {e}")
    
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        try:
            await asyncio.sleep(1)
            
            before_ids = {emoji.id for emoji in before}
            after_ids = {emoji.id for emoji in after}
            
            created = after_ids - before_ids
            deleted = before_ids - after_ids
            
            if created:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_create):
                    if entry.target.id in created:
                        executor = entry.user
                        
                        if executor.bot:
                            return
                        
                        executor_member = guild.get_member(executor.id)
                        if not executor_member:
                            return
                        
                        if await self.is_whitelisted(guild.id, executor.id, executor_member.roles):
                            return
                        
                        thresholds = await self.config_manager.get_antinuke_thresholds(guild.id)
                        threshold_config = thresholds.get('emoji_create', self.default_thresholds['emoji_create'])
                        
                        if await self.check_threshold(guild.id, executor.id, 'emoji_create'):
                            action_count = await self.get_action_count(guild.id, executor.id, 'emoji_create')
                            success, punishment = await self.execute_punishment(
                                guild, executor_member, 'emoji_create',
                                f"Mass emoji creation detected - {action_count} emojis in {threshold_config['hours']} hour(s)",
                                {'emoji_name': entry.target.name, 'emoji_id': entry.target.id}
                            )
                            
                            if success:
                                await self.log_antinuke_action(
                                    guild,
                                    "Mass Emoji Creation Detected - Action Taken",
                                    f"**Emoji created:** {entry.target.name} ({entry.target.id})\n"
                                    f"**Punishment:** {punishment}",
                                    executor_member,
                                    'emoji_create',
                                    {
                                        'count': action_count,
                                        'limit': threshold_config['count'],
                                        'hours': threshold_config['hours']
                                    }
                                )
                        break
            
            if deleted:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_delete):
                    if entry.target.id in deleted:
                        executor = entry.user
                        
                        if executor.bot:
                            return
                        
                        executor_member = guild.get_member(executor.id)
                        if not executor_member:
                            return
                        
                        if await self.is_whitelisted(guild.id, executor.id, executor_member.roles):
                            return
                        
                        thresholds = await self.config_manager.get_antinuke_thresholds(guild.id)
                        threshold_config = thresholds.get('emoji_delete', self.default_thresholds['emoji_delete'])
                        
                        if await self.check_threshold(guild.id, executor.id, 'emoji_delete'):
                            action_count = await self.get_action_count(guild.id, executor.id, 'emoji_delete')
                            success, punishment = await self.execute_punishment(
                                guild, executor_member, 'emoji_delete',
                                f"Mass emoji deletion detected - {action_count} emojis in {threshold_config['hours']} hour(s)",
                                {'emoji_name': entry.target.name, 'emoji_id': entry.target.id}
                            )
                            
                            if success:
                                await self.log_antinuke_action(
                                    guild,
                                    "Mass Emoji Deletion Detected - Action Taken",
                                    f"**Emoji deleted:** {entry.target.name} ({entry.target.id})\n"
                                    f"**Punishment:** {punishment}",
                                    executor_member,
                                    'emoji_delete',
                                    {
                                        'count': action_count,
                                        'limit': threshold_config['count'],
                                        'hours': threshold_config['hours']
                                    }
                                )
                        break
        except Exception as e:
            print(f"Error in on_guild_emojis_update: {e}")
    
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        try:
            await asyncio.sleep(1)
            
            before_ids = {sticker.id for sticker in before}
            after_ids = {sticker.id for sticker in after}
            
            created = after_ids - before_ids
            deleted = before_ids - after_ids
            
            if created:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.sticker_create):
                    if entry.target.id in created:
                        executor = entry.user
                        
                        if executor.bot:
                            return
                        
                        executor_member = guild.get_member(executor.id)
                        if not executor_member:
                            return
                        
                        if await self.is_whitelisted(guild.id, executor.id, executor_member.roles):
                            return
                        
                        thresholds = await self.config_manager.get_antinuke_thresholds(guild.id)
                        threshold_config = thresholds.get('sticker_create', self.default_thresholds['sticker_create'])
                        
                        if await self.check_threshold(guild.id, executor.id, 'sticker_create'):
                            action_count = await self.get_action_count(guild.id, executor.id, 'sticker_create')
                            success, punishment = await self.execute_punishment(
                                guild, executor_member, 'sticker_create',
                                f"Mass sticker creation detected - {action_count} stickers in {threshold_config['hours']} hour(s)",
                                {'sticker_name': entry.target.name, 'sticker_id': entry.target.id}
                            )
                            
                            if success:
                                await self.log_antinuke_action(
                                    guild,
                                    "Mass Sticker Creation Detected - Action Taken",
                                    f"**Sticker created:** {entry.target.name} ({entry.target.id})\n"
                                    f"**Punishment:** {punishment}",
                                    executor_member,
                                    'sticker_create',
                                    {
                                        'count': action_count,
                                        'limit': threshold_config['count'],
                                        'hours': threshold_config['hours']
                                    }
                                )
                        break
            
            if deleted:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.sticker_delete):
                    if entry.target.id in deleted:
                        executor = entry.user
                        
                        if executor.bot:
                            return
                        
                        executor_member = guild.get_member(executor.id)
                        if not executor_member:
                            return
                        
                        if await self.is_whitelisted(guild.id, executor.id, executor_member.roles):
                            return
                        
                        thresholds = await self.config_manager.get_antinuke_thresholds(guild.id)
                        threshold_config = thresholds.get('sticker_delete', self.default_thresholds['sticker_delete'])
                        
                        if await self.check_threshold(guild.id, executor.id, 'sticker_delete'):
                            action_count = await self.get_action_count(guild.id, executor.id, 'sticker_delete')
                            success, punishment = await self.execute_punishment(
                                guild, executor_member, 'sticker_delete',
                                f"Mass sticker deletion detected - {action_count} stickers in {threshold_config['hours']} hour(s)",
                                {'sticker_name': entry.target.name, 'sticker_id': entry.target.id}
                            )
                            
                            if success:
                                await self.log_antinuke_action(
                                    guild,
                                    "Mass Sticker Deletion Detected - Action Taken",
                                    f"**Sticker deleted:** {entry.target.name} ({entry.target.id})\n"
                                    f"**Punishment:** {punishment}",
                                    executor_member,
                                    'sticker_delete',
                                    {
                                        'count': action_count,
                                        'limit': threshold_config['count'],
                                        'hours': threshold_config['hours']
                                    }
                                )
                        break
        except Exception as e:
            print(f"Error in on_guild_stickers_update: {e}")
    
    @commands.group(name='antinuke', invoke_without_command=True)
    @is_owner()
    async def antinuke(self, ctx):
        embed = discord.Embed(
            title="Anti-Nuke System",
            description="Configure and manage the anti-nuke protection system",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Commands",
            value="`.antinuke threshold <action> <count> <hours>` - Set threshold\n"
                  "`.antinuke view` - View all thresholds\n"
                  "`.antinuke whitelist add <@user/@role>` - Whitelist\n"
                  "`.antinuke whitelist remove <@user/@role>` - Remove whitelist\n"
                  "`.antinuke whitelist view` - View whitelist\n"
                  "`.antinuke action <ban|kick|jail>` - Set punishment\n"
                  "`.antinuke history` - View action history",
            inline=False
        )
        
        embed.add_field(
            name="Available Actions",
            value="`ban`, `kick`, `role_create`, `role_delete`, `channel_create`, `channel_delete`, "
                  "`webhook_create`, `webhook_delete`, `emoji_create`, `emoji_delete`, `sticker_create`, `sticker_delete`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @antinuke.command(name='threshold')
    @is_owner()
    async def set_threshold(self, ctx, action: str, count: int, hours: int):
        valid_actions = ['ban', 'kick', 'role_create', 'role_delete', 'channel_create', 'channel_delete',
                        'webhook_create', 'webhook_delete', 'emoji_create', 'emoji_delete', 
                        'sticker_create', 'sticker_delete']
        
        if action not in valid_actions:
            await ctx.send(f"❌ Invalid action. Valid actions: {', '.join(valid_actions)}")
            return
        
        if count < 1 or hours < 1:
            await ctx.send("❌ Count and hours must be at least 1")
            return
        
        await self.config_manager.set_antinuke_threshold(ctx.guild.id, action, count, hours)
        
        embed = discord.Embed(
            title="✅ Threshold Set",
            description=f"**Action:** {action}\n"
                       f"**Count:** {count}\n"
                       f"**Time window:** {hours} hour(s)",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @antinuke.command(name='view')
    @is_owner()
    async def view_thresholds(self, ctx):
        thresholds = await self.config_manager.get_antinuke_thresholds(ctx.guild.id)
        default_action = await self.config_manager.get_antinuke_action(ctx.guild.id)
        
        embed = discord.Embed(
            title="Anti-Nuke Configuration",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Default Punishment",
            value=default_action.capitalize(),
            inline=False
        )
        
        threshold_text = []
        for action in ['ban', 'kick', 'role_create', 'role_delete', 'channel_create', 'channel_delete',
                      'webhook_create', 'webhook_delete', 'emoji_create', 'emoji_delete', 
                      'sticker_create', 'sticker_delete']:
            if action in thresholds:
                config = thresholds[action]
                threshold_text.append(f"**{action}:** {config['count']} in {config['hours']}h")
            else:
                default = self.default_thresholds.get(action, {'count': 0, 'hours': 0})
                threshold_text.append(f"**{action}:** {default['count']} in {default['hours']}h (default)")
        
        embed.add_field(
            name="Thresholds",
            value='\n'.join(threshold_text[:6]),
            inline=True
        )
        
        embed.add_field(
            name="⠀",
            value='\n'.join(threshold_text[6:]),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @antinuke.command(name='action')
    @is_owner()
    async def set_action(self, ctx, action: str):
        action = action.lower()
        if action not in ['ban', 'kick', 'jail']:
            await ctx.send("❌ Invalid action. Valid options: `ban`, `kick`, `jail`")
            return
        
        await self.config_manager.set_antinuke_action(ctx.guild.id, action)
        
        embed = discord.Embed(
            title="✅ Default Action Set",
            description=f"Anti-nuke will now **{action}** offenders when thresholds are exceeded",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @antinuke.command(name='history')
    @is_owner()
    async def view_history(self, ctx):
        history = await self.config_manager.get_antinuke_history(ctx.guild.id)
        
        if not history:
            await ctx.send("No anti-nuke actions have been taken yet.")
            return
        
        embed = discord.Embed(
            title="Anti-Nuke Action History",
            description="Last 10 actions taken by the anti-nuke system",
            color=discord.Color.orange()
        )
        
        for i, action in enumerate(reversed(history), 1):
            timestamp = action.get('timestamp', 'Unknown')
            action_type = action.get('action_type', 'Unknown')
            user_name = action.get('user_name', 'Unknown')
            user_id = action.get('user_id', 'Unknown')
            punishment = action.get('punishment', 'Unknown')
            reason = action.get('reason', 'No reason')
            
            embed.add_field(
                name=f"#{i} - {action_type.replace('_', ' ').title()}",
                value=f"**User:** {user_name} ({user_id})\n"
                      f"**Punishment:** {punishment}\n"
                      f"**Reason:** {reason}\n"
                      f"**Time:** {timestamp[:19]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.group(name='whitelist', invoke_without_command=True)
    @is_owner()
    async def whitelist(self, ctx):
        await ctx.send("Use `.whitelist add <@user/@role>`, `.whitelist remove <@user/@role>`, or `.whitelist view`")
    
    @whitelist.command(name='add')
    @is_owner()
    async def whitelist_add(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.add_antinuke_whitelist(ctx.guild.id, target.id, 'users')
            embed = discord.Embed(
                title="✅ User Whitelisted",
                description=f"{target.mention} has been added to the anti-nuke whitelist",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        elif role:
            await self.config_manager.add_antinuke_whitelist(ctx.guild.id, role.id, 'roles')
            embed = discord.Embed(
                title="✅ Role Whitelisted",
                description=f"{role.mention} has been added to the anti-nuke whitelist",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Please mention a user or role to whitelist")
    
    @whitelist.command(name='remove')
    @is_owner()
    async def whitelist_remove(self, ctx, target: discord.Member = None, role: discord.Role = None):
        if target:
            await self.config_manager.remove_antinuke_whitelist(ctx.guild.id, target.id, 'users')
            embed = discord.Embed(
                title="✅ User Removed",
                description=f"{target.mention} has been removed from the anti-nuke whitelist",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        elif role:
            await self.config_manager.remove_antinuke_whitelist(ctx.guild.id, role.id, 'roles')
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"{role.mention} has been removed from the anti-nuke whitelist",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Please mention a user or role to remove from whitelist")
    
    @whitelist.command(name='view')
    @is_owner()
    async def whitelist_view(self, ctx):
        whitelist = await self.config_manager.get_antinuke_whitelist(ctx.guild.id)
        
        user_list = []
        for user_id in whitelist.get('users', []):
            user = ctx.guild.get_member(user_id)
            if user:
                user_list.append(f"{user.mention} ({user.id})")
            else:
                user_list.append(f"Unknown User ({user_id})")
        
        role_list = []
        for role_id in whitelist.get('roles', []):
            role = ctx.guild.get_role(role_id)
            if role:
                role_list.append(f"{role.mention} ({role.id})")
            else:
                role_list.append(f"Unknown Role ({role_id})")
        
        embed = discord.Embed(
            title="Anti-Nuke Whitelist",
            description="Users and roles exempt from anti-nuke protection",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Whitelisted Users",
            value='\n'.join(user_list) if user_list else "None",
            inline=False
        )
        embed.add_field(
            name="Whitelisted Roles",
            value='\n'.join(role_list) if role_list else "None",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
