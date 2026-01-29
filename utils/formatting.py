import discord
from datetime import datetime
from typing import Optional

def create_embed(title: str, description: str = None, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
    return embed

def create_log_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
    return embed

def paginate_list(items: list, page: int, per_page: int = 10):
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (len(items) + per_page - 1) // per_page
    
    return items[start:end], total_pages

def format_user(user: discord.User) -> str:
    return f"{user.mention} ({user.name}#{user.discriminator} - {user.id})"

def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
