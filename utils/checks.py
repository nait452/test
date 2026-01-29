import discord
from discord.ext import commands
import config
from typing import Union

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == config.OWNER_ID or ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

def is_admin():
    async def predicate(ctx):
        if ctx.author.id == config.OWNER_ID or ctx.author.id == ctx.guild.owner_id:
            return True
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

async def has_fake_permission(ctx, permission: str):
    from utils.config_manager import ConfigManager
    config_manager = ConfigManager()
    fake_perms = await config_manager.get_fake_perms(ctx.guild.id)
    
    user_perms = fake_perms.get('users', {}).get(str(ctx.author.id), [])
    if permission in user_perms:
        return True
    
    for role in ctx.author.roles:
        role_perms = fake_perms.get('roles', {}).get(str(role.id), [])
        if permission in role_perms:
            return True
    
    return False

async def has_hardban_permission(ctx):
    if ctx.author.id == config.OWNER_ID or ctx.author.id == ctx.guild.owner_id:
        return True
    
    from utils.config_manager import ConfigManager
    config_manager = ConfigManager()
    hardban_perms = await config_manager.get_hardban_perms(ctx.guild.id)
    
    if str(ctx.author.id) in hardban_perms.get('users', []):
        return True
    
    for role in ctx.author.roles:
        if str(role.id) in hardban_perms.get('roles', []):
            return True
    
    return False

def hardban_permission():
    async def predicate(ctx):
        return await has_hardban_permission(ctx)
    return commands.check(predicate)
